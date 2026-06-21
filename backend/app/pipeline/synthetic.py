from dataclasses import dataclass
from datetime import datetime, timezone

import duckdb

from app.pipeline.normalization import normalize_local_data
from app.pipeline.synthetic_dataset import build_synthetic_dataset
from app.storage import initialize_schema
from app.storage.loaders import load_synthetic_dataset


LOCAL_SYNTHETIC_DATASET_NAME = "synthetic-fixture"
LOCAL_SYNTHETIC_DATASET_KIND = "local_synthetic"


@dataclass(frozen=True)
class PipelineStatus:
    dataset_name: str
    dataset_kind: str
    state: str
    message: str
    raw_contacts_count: int
    raw_deals_count: int
    raw_links_count: int
    normalized_contacts_count: int
    normalized_deals_count: int
    started_at: datetime
    finished_at: datetime


def run_synthetic_pipeline(connection: duckdb.DuckDBPyConnection) -> PipelineStatus:
    started_at = datetime.now(timezone.utc)
    initialize_schema(connection)
    dataset = build_synthetic_dataset()
    load_synthetic_dataset(connection, dataset)
    normalize_local_data(connection)
    finished_at = datetime.now(timezone.utc)

    status = PipelineStatus(
        dataset_name=LOCAL_SYNTHETIC_DATASET_NAME,
        dataset_kind=LOCAL_SYNTHETIC_DATASET_KIND,
        state="success",
        message="Local synthetic fixture pipeline completed. No Bitrix calls were made.",
        raw_contacts_count=_count_rows(connection, "raw_contacts"),
        raw_deals_count=_count_rows(connection, "raw_deals"),
        raw_links_count=_count_rows(connection, "raw_deal_contact_links"),
        normalized_contacts_count=_count_rows(connection, "normalized_contacts"),
        normalized_deals_count=_count_rows(connection, "normalized_deals"),
        started_at=started_at,
        finished_at=finished_at,
    )
    _store_status(connection, status)
    return status


def get_latest_pipeline_status(
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
        [LOCAL_SYNTHETIC_DATASET_NAME],
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
