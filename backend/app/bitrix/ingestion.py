from __future__ import annotations

from datetime import datetime, timezone

import duckdb

from app.bitrix.client import BitrixClient, BitrixClientError
from app.bitrix.transform import (
    transform_contacts,
    transform_deal_contact_links,
    transform_deals,
    transform_stages,
)
from app.pipeline.normalization import normalize_local_data
from app.pipeline.synthetic import PipelineStatus
from app.storage import initialize_schema
from app.storage.loaders import load_bitrix_raw_data


BITRIX_MANUAL_DATASET_NAME = "bitrix-manual"
BITRIX_MANUAL_DATASET_KIND = "bitrix_manual"


def run_bitrix_manual_ingestion(
    connection: duckdb.DuckDBPyConnection,
    *,
    client: BitrixClient,
    contact_type_field: str | None,
) -> PipelineStatus:
    started_at = datetime.now(timezone.utc)
    initialize_schema(connection)
    try:
        stage_rows = client.list_stages()
        stages = transform_stages(stage_rows)
        contact_rows = client.list_contacts(contact_type_field)
        contacts = transform_contacts(
            contact_rows,
            contact_type_field=contact_type_field,
        )
        deal_rows = client.list_deals()
        deals = transform_deals(deal_rows, stages)
        links = [
            link
            for deal in deals
            for link in transform_deal_contact_links(
                deal.deal_id,
                client.get_deal_contact_links(deal.deal_id),
            )
        ]
        load_bitrix_raw_data(
            connection,
            contacts=contacts,
            deals=deals,
            links=links,
            stages=stages,
        )
        normalize_local_data(connection)
    except (BitrixClientError, ValueError) as exc:
        finished_at = datetime.now(timezone.utc)
        status = _status(
            connection,
            state="error",
            message=str(exc),
            started_at=started_at,
            finished_at=finished_at,
        )
        _store_status(connection, status)
        return status

    finished_at = datetime.now(timezone.utc)
    status = _status(
        connection,
        state="success",
        message="Manual Bitrix ingestion completed.",
        started_at=started_at,
        finished_at=finished_at,
    )
    _store_status(connection, status)
    return status


def get_latest_bitrix_ingestion_status(
    connection: duckdb.DuckDBPyConnection,
) -> PipelineStatus | None:
    initialize_schema(connection)
    row = connection.execute(
        """
        SELECT
            dataset_name,
            dataset_kind,
            state,
            message,
            raw_contacts_count,
            raw_deals_count,
            raw_links_count,
            normalized_contacts_count,
            normalized_deals_count,
            started_at,
            finished_at
        FROM local_dataset_status
        WHERE dataset_name = ?
        """,
        [BITRIX_MANUAL_DATASET_NAME],
    ).fetchone()
    if row is None:
        return None

    return PipelineStatus(
        dataset_name=row[0],
        dataset_kind=row[1],
        state=row[2],
        message=row[3],
        raw_contacts_count=row[4],
        raw_deals_count=row[5],
        raw_links_count=row[6],
        normalized_contacts_count=row[7],
        normalized_deals_count=row[8],
        started_at=_as_utc(row[9]),
        finished_at=_as_utc(row[10]),
    )


def store_bitrix_ingestion_error(
    connection: duckdb.DuckDBPyConnection,
    message: str,
) -> PipelineStatus:
    now = datetime.now(timezone.utc)
    initialize_schema(connection)
    status = _status(
        connection,
        state="error",
        message=message,
        started_at=now,
        finished_at=now,
    )
    _store_status(connection, status)
    return status


def _status(
    connection: duckdb.DuckDBPyConnection,
    *,
    state: str,
    message: str,
    started_at: datetime,
    finished_at: datetime,
) -> PipelineStatus:
    return PipelineStatus(
        dataset_name=BITRIX_MANUAL_DATASET_NAME,
        dataset_kind=BITRIX_MANUAL_DATASET_KIND,
        state=state,
        message=message,
        raw_contacts_count=_count_rows(connection, "raw_contacts"),
        raw_deals_count=_count_rows(connection, "raw_deals"),
        raw_links_count=_count_rows(connection, "raw_deal_contact_links"),
        normalized_contacts_count=_count_rows(connection, "normalized_contacts"),
        normalized_deals_count=_count_rows(connection, "normalized_deals"),
        started_at=started_at,
        finished_at=finished_at,
    )


def _count_rows(connection: duckdb.DuckDBPyConnection, table_name: str) -> int:
    return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


def _store_status(
    connection: duckdb.DuckDBPyConnection,
    status: PipelineStatus,
) -> None:
    connection.execute(
        "DELETE FROM local_dataset_status WHERE dataset_name = ?",
        [status.dataset_name],
    )
    connection.execute(
        """
        INSERT INTO local_dataset_status (
            dataset_name,
            dataset_kind,
            state,
            message,
            raw_contacts_count,
            raw_deals_count,
            raw_links_count,
            normalized_contacts_count,
            normalized_deals_count,
            started_at,
            finished_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            status.dataset_name,
            status.dataset_kind,
            status.state,
            status.message,
            status.raw_contacts_count,
            status.raw_deals_count,
            status.raw_links_count,
            status.normalized_contacts_count,
            status.normalized_deals_count,
            status.started_at,
            status.finished_at,
        ],
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
