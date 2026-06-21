from datetime import datetime, timezone
from pathlib import Path

import duckdb


RAW_SNAPSHOT_COLUMNS = {
    "raw_contacts": ("contact_id", "contact_name", "contact_type_raw"),
    "raw_deals": (
        "deal_id",
        "deal_name",
        "amount_original",
        "currency_original",
        "created_at",
        "closed_at",
        "stage_id",
        "category_id",
        "status_group",
    ),
    "raw_deal_contact_links": (
        "deal_id",
        "contact_id",
        "is_primary",
        "sort_order",
        "role_id",
    ),
    "raw_stages": ("stage_id", "category_id", "status_group"),
}


def write_raw_parquet_snapshots(
    connection: duckdb.DuckDBPyConnection,
    *,
    data_dir: Path,
    dataset_kind: str,
    run_id: str,
) -> tuple[str, ...]:
    snapshot_dir = Path("snapshots") / dataset_kind / run_id
    output_dir = data_dir / snapshot_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    snapshot_paths = []
    for table_name, columns in RAW_SNAPSHOT_COLUMNS.items():
        relative_path = snapshot_dir / f"{table_name}.parquet"
        output_path = data_dir / relative_path
        selected_columns = ", ".join(columns)
        order_columns = ", ".join(columns[:2])
        connection.execute(
            f"""
            COPY (
                SELECT {selected_columns}
                FROM {table_name}
                ORDER BY {order_columns}
            )
            TO '{_escape_path(output_path)}'
            (FORMAT PARQUET)
            """
        )
        snapshot_paths.append(relative_path.as_posix())

    return tuple(snapshot_paths)


def build_run_id(dataset_kind: str, started_at: datetime) -> str:
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    timestamp = started_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{dataset_kind}-{timestamp}"


def _escape_path(path: Path) -> str:
    return str(path).replace("'", "''")
