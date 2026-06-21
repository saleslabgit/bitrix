from datetime import datetime, timezone
from pathlib import Path

import duckdb

from app.pipeline.normalization import normalize_local_data
from app.pipeline.synthetic_dataset import build_synthetic_dataset
from app.storage import initialize_schema
from app.storage.loaders import load_synthetic_dataset
from app.storage.snapshots import build_run_id, write_raw_parquet_snapshots
from app.storage.status import (
    DatasetRunStatus,
    count_current_rows,
    get_latest_dataset_run,
    store_dataset_run,
)


LOCAL_SYNTHETIC_DATASET_NAME = "synthetic-fixture"
LOCAL_SYNTHETIC_DATASET_KIND = "local_synthetic"


PipelineStatus = DatasetRunStatus


def run_synthetic_pipeline(
    connection: duckdb.DuckDBPyConnection,
    *,
    data_dir: Path | None = None,
) -> PipelineStatus:
    started_at = datetime.now(timezone.utc)
    run_id = build_run_id(LOCAL_SYNTHETIC_DATASET_KIND, started_at)
    initialize_schema(connection)
    try:
        connection.execute("BEGIN TRANSACTION")
        dataset = build_synthetic_dataset()
        load_synthetic_dataset(connection, dataset)
        normalize_local_data(connection)
        snapshot_paths = ()
        if data_dir is not None:
            snapshot_paths = write_raw_parquet_snapshots(
                connection,
                data_dir=data_dir,
                dataset_kind=LOCAL_SYNTHETIC_DATASET_KIND,
                run_id=run_id,
            )
        finished_at = datetime.now(timezone.utc)
        counts = count_current_rows(connection)
        status = PipelineStatus(
            run_id=run_id,
            dataset_name=LOCAL_SYNTHETIC_DATASET_NAME,
            dataset_kind=LOCAL_SYNTHETIC_DATASET_KIND,
            state="success",
            message="Local synthetic fixture pipeline completed. No Bitrix calls were made.",
            started_at=started_at,
            finished_at=finished_at,
            snapshot_paths=snapshot_paths,
            is_active=True,
            **counts,
        )
        store_dataset_run(connection, status)
        connection.execute("COMMIT")
        return status
    except Exception:
        connection.execute("ROLLBACK")
        raise


def get_latest_pipeline_status(
    connection: duckdb.DuckDBPyConnection,
) -> PipelineStatus | None:
    return get_latest_dataset_run(
        connection,
        dataset_name=LOCAL_SYNTHETIC_DATASET_NAME,
    )
