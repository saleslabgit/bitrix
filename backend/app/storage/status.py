from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

import duckdb

from app.storage.schema import initialize_schema


@dataclass(frozen=True)
class DatasetRunStatus:
    run_id: str | None
    dataset_name: str
    dataset_kind: str
    state: str
    message: str
    raw_contacts_count: int
    raw_deals_count: int
    raw_links_count: int
    normalized_contacts_count: int
    normalized_deals_count: int
    started_at: datetime | None
    finished_at: datetime | None
    snapshot_paths: tuple[str, ...] = ()
    is_active: bool = False


@dataclass(frozen=True)
class DatasetStorageStatus:
    active_dataset: DatasetRunStatus | None
    latest_run: DatasetRunStatus | None


def count_table_rows(connection: duckdb.DuckDBPyConnection, table_name: str) -> int:
    return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


def count_current_rows(connection: duckdb.DuckDBPyConnection) -> dict[str, int]:
    return {
        "raw_contacts_count": count_table_rows(connection, "raw_contacts"),
        "raw_deals_count": count_table_rows(connection, "raw_deals"),
        "raw_links_count": count_table_rows(connection, "raw_deal_contact_links"),
        "normalized_contacts_count": count_table_rows(connection, "normalized_contacts"),
        "normalized_deals_count": count_table_rows(connection, "normalized_deals"),
    }


def store_dataset_run(
    connection: duckdb.DuckDBPyConnection,
    status: DatasetRunStatus,
) -> None:
    connection.execute(
        """
        INSERT INTO local_dataset_runs (
            run_id,
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
            finished_at,
            snapshot_paths,
            is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            status.run_id,
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
            json.dumps(list(status.snapshot_paths), ensure_ascii=False),
            status.is_active,
        ],
    )
    _store_latest_dataset_status(connection, status)

    if status.state == "success" and status.run_id is not None:
        connection.execute("UPDATE local_dataset_runs SET is_active = false")
        connection.execute(
            "UPDATE local_dataset_runs SET is_active = true WHERE run_id = ?",
            [status.run_id],
        )
        connection.execute("DELETE FROM local_active_dataset")
        connection.execute(
            """
            INSERT INTO local_active_dataset (
                singleton_id,
                run_id,
                dataset_name,
                dataset_kind,
                activated_at
            )
            VALUES (true, ?, ?, ?, ?)
            """,
            [
                status.run_id,
                status.dataset_name,
                status.dataset_kind,
                status.finished_at,
            ],
        )


def get_latest_dataset_run(
    connection: duckdb.DuckDBPyConnection,
    *,
    dataset_name: str | None = None,
) -> DatasetRunStatus | None:
    initialize_schema(connection)
    where_clause = ""
    params: list[object] = []
    if dataset_name is not None:
        where_clause = "WHERE dataset_name = ?"
        params.append(dataset_name)

    row = connection.execute(
        f"""
        SELECT
            run_id,
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
            finished_at,
            snapshot_paths,
            is_active
        FROM local_dataset_runs
        {where_clause}
        ORDER BY started_at DESC, run_id DESC
        LIMIT 1
        """,
        params,
    ).fetchone()
    if row is None:
        return None
    return _run_from_row(row)


def get_active_dataset_run(
    connection: duckdb.DuckDBPyConnection,
) -> DatasetRunStatus | None:
    initialize_schema(connection)
    row = connection.execute(
        """
        SELECT
            runs.run_id,
            runs.dataset_name,
            runs.dataset_kind,
            runs.state,
            runs.message,
            runs.raw_contacts_count,
            runs.raw_deals_count,
            runs.raw_links_count,
            runs.normalized_contacts_count,
            runs.normalized_deals_count,
            runs.started_at,
            runs.finished_at,
            runs.snapshot_paths,
            true
        FROM local_active_dataset active
        JOIN local_dataset_runs runs ON runs.run_id = active.run_id
        WHERE active.singleton_id = true
        """
    ).fetchone()
    if row is None:
        return None
    return _run_from_row(row)


def get_dataset_storage_status(
    connection: duckdb.DuckDBPyConnection,
) -> DatasetStorageStatus:
    return DatasetStorageStatus(
        active_dataset=get_active_dataset_run(connection),
        latest_run=get_latest_dataset_run(connection),
    )


def _store_latest_dataset_status(
    connection: duckdb.DuckDBPyConnection,
    status: DatasetRunStatus,
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


def _run_from_row(row: tuple[object, ...]) -> DatasetRunStatus:
    return DatasetRunStatus(
        run_id=row[0],
        dataset_name=row[1],
        dataset_kind=row[2],
        state=row[3],
        message=row[4],
        raw_contacts_count=row[5],
        raw_deals_count=row[6],
        raw_links_count=row[7],
        normalized_contacts_count=row[8],
        normalized_deals_count=row[9],
        started_at=_as_utc(row[10]),
        finished_at=_as_utc(row[11]),
        snapshot_paths=tuple(json.loads(row[12] or "[]")),
        is_active=bool(row[13]),
    )


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
