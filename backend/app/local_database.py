from collections.abc import Iterator
from contextlib import contextmanager
from threading import RLock

import duckdb

from app.core.config import get_settings
from app.storage import initialize_schema
from app.storage.connection import connect_configured_duckdb


_connection: duckdb.DuckDBPyConnection | None = None
_connection_lock = RLock()
_schema_initialized = False


def _ensure_connection_locked() -> duckdb.DuckDBPyConnection:
    global _connection, _schema_initialized
    if _connection is None:
        _connection = connect_configured_duckdb(get_settings())
        _schema_initialized = True
    elif not _schema_initialized:
        initialize_schema(_connection)
        _schema_initialized = True
    return _connection


def get_connection() -> duckdb.DuckDBPyConnection:
    with _connection_lock:
        return _ensure_connection_locked()


@contextmanager
def connection_scope() -> Iterator[duckdb.DuckDBPyConnection]:
    with _connection_lock:
        yield _ensure_connection_locked()


def reset_connection() -> None:
    global _connection, _schema_initialized
    with _connection_lock:
        if _connection is not None:
            _connection.close()
        _connection = None
        _schema_initialized = False
