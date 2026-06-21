from app.core.config import get_settings
from app.storage import initialize_schema
from app.storage.connection import connect_configured_duckdb


_connection = None


def get_connection():
    global _connection
    if _connection is None:
        _connection = connect_configured_duckdb(get_settings())
    initialize_schema(_connection)
    return _connection


def reset_connection() -> None:
    global _connection
    if _connection is not None:
        _connection.close()
    _connection = None
