import duckdb

from app.storage import initialize_schema


_connection = duckdb.connect(database=":memory:")
initialize_schema(_connection)


def get_connection() -> duckdb.DuckDBPyConnection:
    return _connection
