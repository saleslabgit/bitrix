from pathlib import Path

import duckdb

from app.core.config import Settings
from app.storage.schema import initialize_schema


IN_MEMORY_DATABASE = ":memory:"


def resolve_data_dir(settings: Settings) -> Path:
    return settings.data_dir.expanduser()


def resolve_duckdb_path(settings: Settings) -> str:
    if settings.duckdb_path is not None:
        value = str(settings.duckdb_path.expanduser())
        if value == IN_MEMORY_DATABASE:
            return IN_MEMORY_DATABASE
        return value

    return str(resolve_data_dir(settings) / "analytics.duckdb")


def connect_configured_duckdb(settings: Settings) -> duckdb.DuckDBPyConnection:
    database = resolve_duckdb_path(settings)
    if database != IN_MEMORY_DATABASE:
        Path(database).parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(database=database)
    initialize_schema(connection)
    return connection
