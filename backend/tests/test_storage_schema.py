import duckdb

from app.core.config import Settings
from app.storage.connection import connect_configured_duckdb
from app.storage import initialize_schema, list_expected_tables


EXPECTED_COLUMNS = {
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
        "kev_held",
    ),
    "raw_deal_contact_links": (
        "deal_id",
        "contact_id",
        "is_primary",
        "sort_order",
        "role_id",
    ),
    "raw_stages": ("stage_id", "category_id", "status_group"),
    "contact_type_rules": (
        "raw_value",
        "normalized_type",
        "priority",
        "region",
        "is_active",
    ),
    "currency_rates": (
        "currency",
        "rate_date",
        "source_rate_byn",
        "usd_rate_byn",
        "rate_source",
        "rate_fetched_at",
    ),
    "normalized_contacts": (
        "contact_id",
        "contact_name",
        "contact_type_raw",
        "contact_type_normalized",
        "region_normalized",
    ),
    "normalized_deals": (
        "deal_id",
        "deal_name",
        "amount_original",
        "currency_original",
        "created_at",
        "closed_at",
        "stage_id",
        "category_id",
        "status_group",
        "analytical_contact_id",
        "analytical_contact_name",
        "contact_type_normalized",
        "region_normalized",
        "kev_held",
    ),
    "local_dataset_status": (
        "dataset_name",
        "dataset_kind",
        "state",
        "message",
        "raw_contacts_count",
        "raw_deals_count",
        "raw_links_count",
        "normalized_contacts_count",
        "normalized_deals_count",
        "started_at",
        "finished_at",
    ),
    "local_dataset_runs": (
        "run_id",
        "dataset_name",
        "dataset_kind",
        "state",
        "message",
        "raw_contacts_count",
        "raw_deals_count",
        "raw_links_count",
        "normalized_contacts_count",
        "normalized_deals_count",
        "started_at",
        "finished_at",
        "snapshot_paths",
        "is_active",
    ),
    "local_active_dataset": (
        "singleton_id",
        "run_id",
        "dataset_name",
        "dataset_kind",
        "activated_at",
    ),
}

FORBIDDEN_FIELD_PARTS = (
    "phone",
    "email",
    "address",
    "messenger",
    "requisite",
    "comment",
    "file",
    "activity",
)


def table_names(connection: duckdb.DuckDBPyConnection) -> set[str]:
    rows = connection.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        """
    ).fetchall()
    return {row[0] for row in rows}


def column_names(connection: duckdb.DuckDBPyConnection, table_name: str) -> tuple[str, ...]:
    rows = connection.execute(f"PRAGMA table_info('{table_name}')").fetchall()
    return tuple(row[1] for row in rows)


def test_schema_initialization_creates_expected_tables_and_columns() -> None:
    with duckdb.connect(database=":memory:") as connection:
        initialize_schema(connection)

        assert table_names(connection) == set(list_expected_tables())
        for table_name, expected_columns in EXPECTED_COLUMNS.items():
            assert column_names(connection, table_name) == expected_columns


def test_schema_initialization_is_idempotent() -> None:
    with duckdb.connect(database=":memory:") as connection:
        initialize_schema(connection)
        initialize_schema(connection)

        assert table_names(connection) == set(list_expected_tables())


def test_schema_migrates_previous_file_without_losing_deal_rows(tmp_path) -> None:
    database_path = tmp_path / "previous-schema.duckdb"
    with duckdb.connect(database=str(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE raw_deals (
                deal_id BIGINT PRIMARY KEY,
                deal_name VARCHAR NOT NULL,
                amount_original DECIMAL(18, 2) NOT NULL,
                currency_original VARCHAR NOT NULL,
                created_at TIMESTAMP NOT NULL,
                closed_at TIMESTAMP,
                stage_id VARCHAR NOT NULL,
                category_id INTEGER,
                status_group VARCHAR NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE normalized_deals (
                deal_id BIGINT PRIMARY KEY,
                deal_name VARCHAR NOT NULL,
                amount_original DECIMAL(18, 2) NOT NULL,
                currency_original VARCHAR NOT NULL,
                created_at TIMESTAMP NOT NULL,
                closed_at TIMESTAMP,
                stage_id VARCHAR NOT NULL,
                category_id INTEGER,
                status_group VARCHAR NOT NULL,
                analytical_contact_id BIGINT,
                analytical_contact_name VARCHAR NOT NULL,
                contact_type_normalized VARCHAR NOT NULL,
                region_normalized VARCHAR NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO raw_deals VALUES
            (1, 'Previous raw deal', 10, 'USD', TIMESTAMP '2025-01-01', NULL, 'OPEN', 0, 'open')
            """
        )
        connection.execute(
            """
            INSERT INTO normalized_deals VALUES
            (1, 'Previous normalized deal', 10, 'USD', TIMESTAMP '2025-01-01', NULL,
             'OPEN', 0, 'open', NULL, 'Без контакта', 'Не определено', 'Не определено')
            """
        )

        initialize_schema(connection)
        initialize_schema(connection)

        assert connection.execute(
            "SELECT deal_id, kev_held FROM raw_deals"
        ).fetchall() == [(1, False)]
        assert connection.execute(
            "SELECT deal_id, kev_held FROM normalized_deals"
        ).fetchall() == [(1, False)]
        for table_name in ("raw_deals", "normalized_deals"):
            kev_column = next(
                row for row in connection.execute(f"PRAGMA table_info('{table_name}')").fetchall()
                if row[1] == "kev_held"
            )
            assert kev_column[3] is True


def test_configured_duckdb_file_storage_persists_across_connections(tmp_path) -> None:
    database_path = tmp_path / "analytics.duckdb"
    settings = Settings(APP_DATA_DIR=tmp_path, APP_DUCKDB_PATH=database_path)

    first_connection = connect_configured_duckdb(settings)
    first_connection.execute(
        """
        INSERT INTO contact_type_rules (
            raw_value,
            normalized_type,
            priority,
            region,
            is_active
        )
        VALUES ('raw', 'Normalized', 1, 'Region', true)
        """
    )
    first_connection.close()

    second_connection = connect_configured_duckdb(settings)
    try:
        initialize_schema(second_connection)
        count = second_connection.execute(
            "SELECT COUNT(*) FROM contact_type_rules"
        ).fetchone()[0]
    finally:
        second_connection.close()

    assert database_path.exists()
    assert count == 1


def test_schema_does_not_include_forbidden_columns() -> None:
    with duckdb.connect(database=":memory:") as connection:
        initialize_schema(connection)

        all_columns = [
            column_name.lower()
            for table_name in list_expected_tables()
            for column_name in column_names(connection, table_name)
        ]

    assert all(
        forbidden not in column_name
        for column_name in all_columns
        for forbidden in FORBIDDEN_FIELD_PARTS
    )
