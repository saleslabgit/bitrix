import duckdb

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
