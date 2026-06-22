from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from app.bitrix.client import BitrixClient, BitrixClientError
from app.bitrix.transform import (
    transform_contacts,
    transform_deal_contact_links_from_deals,
    transform_deals,
    transform_stages,
)
from app.pipeline.normalization import normalize_local_data
from app.pipeline.synthetic import PipelineStatus
from app.storage import initialize_schema
from app.storage.loaders import load_bitrix_raw_data
from app.storage.snapshots import build_run_id, write_raw_parquet_snapshots
from app.storage.status import (
    count_current_rows,
    get_latest_dataset_run,
    store_dataset_run,
)


BITRIX_MANUAL_DATASET_NAME = "bitrix-manual"
BITRIX_MANUAL_DATASET_KIND = "bitrix_manual"

BitrixManualFinalizer = Callable[[duckdb.DuckDBPyConnection], None]


def run_bitrix_manual_ingestion(
    connection: duckdb.DuckDBPyConnection,
    *,
    client: BitrixClient,
    contact_type_field: str | None,
    data_dir: Path | None = None,
    finalize_local_data: BitrixManualFinalizer | None = None,
    success_message: str = "Manual Bitrix ingestion completed.",
) -> PipelineStatus:
    started_at = datetime.now(timezone.utc)
    run_id = build_run_id(BITRIX_MANUAL_DATASET_KIND, started_at)
    initialize_schema(connection)
    try:
        stage_rows = client.list_stages()
        stages = transform_stages(stage_rows)
        contact_rows = client.list_contacts(contact_type_field)
        contacts = transform_contacts(
            contact_rows,
            contact_type_field=contact_type_field,
        )
        deal_rows = client.list_deal_items()
        deals = transform_deals(deal_rows, stages)
        links = transform_deal_contact_links_from_deals(deal_rows)
        connection.execute("BEGIN TRANSACTION")
        load_bitrix_raw_data(
            connection,
            contacts=contacts,
            deals=deals,
            links=links,
            stages=stages,
        )
        if finalize_local_data is None:
            normalize_local_data(connection)
        else:
            finalize_local_data(connection)
        snapshot_paths = ()
        if data_dir is not None:
            snapshot_paths = write_raw_parquet_snapshots(
                connection,
                data_dir=data_dir,
                dataset_kind=BITRIX_MANUAL_DATASET_KIND,
                run_id=run_id,
            )
        finished_at = datetime.now(timezone.utc)
        status = _status(
            connection,
            run_id=run_id,
            state="success",
            message=success_message,
            started_at=started_at,
            finished_at=finished_at,
            snapshot_paths=snapshot_paths,
            is_active=True,
        )
        store_dataset_run(connection, status)
        connection.execute("COMMIT")
    except (BitrixClientError, OSError, ValueError, duckdb.Error) as exc:
        _rollback_if_needed(connection)
        finished_at = datetime.now(timezone.utc)
        status = _status(
            connection,
            run_id=run_id,
            state="error",
            message=str(exc),
            started_at=started_at,
            finished_at=finished_at,
            snapshot_paths=(),
            is_active=False,
        )
        store_dataset_run(connection, status)
        return status
    except Exception:
        _rollback_if_needed(connection)
        raise
    return status


def get_latest_bitrix_ingestion_status(
    connection: duckdb.DuckDBPyConnection,
) -> PipelineStatus | None:
    return get_latest_dataset_run(
        connection,
        dataset_name=BITRIX_MANUAL_DATASET_NAME,
    )


def store_bitrix_ingestion_error(
    connection: duckdb.DuckDBPyConnection,
    message: str,
) -> PipelineStatus:
    now = datetime.now(timezone.utc)
    run_id = build_run_id(BITRIX_MANUAL_DATASET_KIND, now)
    initialize_schema(connection)
    status = _status(
        connection,
        run_id=run_id,
        state="error",
        message=message,
        started_at=now,
        finished_at=now,
        snapshot_paths=(),
        is_active=False,
    )
    store_dataset_run(connection, status)
    return status


def _status(
    connection: duckdb.DuckDBPyConnection,
    *,
    run_id: str,
    state: str,
    message: str,
    started_at: datetime,
    finished_at: datetime,
    snapshot_paths: tuple[str, ...],
    is_active: bool,
) -> PipelineStatus:
    counts = count_current_rows(connection)
    return PipelineStatus(
        run_id=run_id,
        dataset_name=BITRIX_MANUAL_DATASET_NAME,
        dataset_kind=BITRIX_MANUAL_DATASET_KIND,
        state=state,
        message=message,
        started_at=started_at,
        finished_at=finished_at,
        snapshot_paths=snapshot_paths,
        is_active=is_active,
        **counts,
    )


def _rollback_if_needed(connection: duckdb.DuckDBPyConnection) -> None:
    try:
        connection.execute("ROLLBACK")
    except duckdb.TransactionException:
        return
