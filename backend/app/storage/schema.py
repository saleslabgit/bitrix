import duckdb


EXPECTED_TABLES = (
    "raw_contacts",
    "raw_deals",
    "raw_deal_contact_links",
    "raw_stages",
    "raw_deal_categories",
    "raw_deal_stage_history",
    "contact_type_rules",
    "currency_rates",
    "normalized_contacts",
    "normalized_deals",
    "local_dataset_status",
    "local_dataset_runs",
    "local_active_dataset",
)


def list_expected_tables() -> tuple[str, ...]:
    return EXPECTED_TABLES


def initialize_schema(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_contacts (
            contact_id BIGINT PRIMARY KEY,
            contact_name VARCHAR NOT NULL,
            contact_type_raw VARCHAR
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_deal_categories (
            category_id BIGINT PRIMARY KEY,
            category_name VARCHAR NOT NULL,
            sort_order INTEGER
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_deals (
            deal_id BIGINT PRIMARY KEY,
            deal_name VARCHAR NOT NULL,
            amount_original DECIMAL(18, 2) NOT NULL,
            currency_original VARCHAR NOT NULL,
            created_at TIMESTAMP NOT NULL,
            closed_at TIMESTAMP,
            planned_close_at TIMESTAMP,
            actual_closed_at TIMESTAMP,
            stage_id VARCHAR NOT NULL,
            category_id INTEGER,
            status_group VARCHAR NOT NULL CHECK (status_group IN ('won', 'open', 'lost')),
            kev_held BOOLEAN NOT NULL DEFAULT false
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_deal_stage_history (
            history_id BIGINT PRIMARY KEY,
            deal_id BIGINT NOT NULL,
            type_id INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL,
            category_id INTEGER NOT NULL,
            stage_id VARCHAR NOT NULL,
            stage_semantic_id VARCHAR NOT NULL CHECK (stage_semantic_id IN ('S', 'F', 'P'))
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_deal_contact_links (
            deal_id BIGINT NOT NULL,
            contact_id BIGINT NOT NULL,
            is_primary BOOLEAN NOT NULL,
            sort_order INTEGER,
            role_id VARCHAR,
            PRIMARY KEY (deal_id, contact_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_stages (
            stage_id VARCHAR NOT NULL,
            category_id INTEGER,
            status_group VARCHAR NOT NULL CHECK (status_group IN ('won', 'open', 'lost'))
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS contact_type_rules (
            raw_value VARCHAR PRIMARY KEY,
            normalized_type VARCHAR NOT NULL,
            priority INTEGER NOT NULL CHECK (priority >= 0),
            region VARCHAR NOT NULL,
            is_active BOOLEAN NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS currency_rates (
            currency VARCHAR NOT NULL,
            rate_date DATE NOT NULL,
            source_rate_byn DECIMAL(18, 8) NOT NULL,
            usd_rate_byn DECIMAL(18, 8) NOT NULL,
            rate_source VARCHAR NOT NULL,
            rate_fetched_at TIMESTAMP NOT NULL,
            PRIMARY KEY (currency, rate_date)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS normalized_contacts (
            contact_id BIGINT PRIMARY KEY,
            contact_name VARCHAR NOT NULL,
            contact_type_raw VARCHAR,
            contact_type_normalized VARCHAR NOT NULL,
            region_normalized VARCHAR NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS normalized_deals (
            deal_id BIGINT PRIMARY KEY,
            deal_name VARCHAR NOT NULL,
            amount_original DECIMAL(18, 2) NOT NULL,
            currency_original VARCHAR NOT NULL,
            created_at TIMESTAMP NOT NULL,
            closed_at TIMESTAMP,
            planned_close_at TIMESTAMP,
            actual_closed_at TIMESTAMP,
            stage_id VARCHAR NOT NULL,
            category_id INTEGER,
            status_group VARCHAR NOT NULL CHECK (status_group IN ('won', 'open', 'lost')),
            analytical_contact_id BIGINT,
            analytical_contact_name VARCHAR NOT NULL,
            contact_type_normalized VARCHAR NOT NULL,
            region_normalized VARCHAR NOT NULL,
            kev_held BOOLEAN NOT NULL DEFAULT false
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS local_dataset_status (
            dataset_name VARCHAR PRIMARY KEY,
            dataset_kind VARCHAR NOT NULL,
            state VARCHAR NOT NULL,
            message VARCHAR NOT NULL,
            raw_contacts_count BIGINT NOT NULL,
            raw_deals_count BIGINT NOT NULL,
            raw_links_count BIGINT NOT NULL,
            normalized_contacts_count BIGINT NOT NULL,
            normalized_deals_count BIGINT NOT NULL,
            started_at TIMESTAMP NOT NULL,
            finished_at TIMESTAMP NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS local_dataset_runs (
            run_id VARCHAR PRIMARY KEY,
            dataset_name VARCHAR NOT NULL,
            dataset_kind VARCHAR NOT NULL,
            state VARCHAR NOT NULL,
            message VARCHAR NOT NULL,
            raw_contacts_count BIGINT NOT NULL,
            raw_deals_count BIGINT NOT NULL,
            raw_links_count BIGINT NOT NULL,
            normalized_contacts_count BIGINT NOT NULL,
            normalized_deals_count BIGINT NOT NULL,
            started_at TIMESTAMP NOT NULL,
            finished_at TIMESTAMP NOT NULL,
            snapshot_paths VARCHAR NOT NULL,
            is_active BOOLEAN NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS local_active_dataset (
            singleton_id BOOLEAN PRIMARY KEY CHECK (singleton_id = true),
            run_id VARCHAR NOT NULL,
            dataset_name VARCHAR NOT NULL,
            dataset_kind VARCHAR NOT NULL,
            activated_at TIMESTAMP NOT NULL
        )
        """
    )
    _migrate_kev_columns(connection)
    _migrate_close_columns(connection)


def _migrate_kev_columns(connection: duckdb.DuckDBPyConnection) -> None:
    for table_name in ("raw_deals", "normalized_deals"):
        columns = {
            row[1] for row in connection.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        }
        if "kev_held" in columns:
            continue
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN kev_held BOOLEAN DEFAULT false"
        )
        connection.execute(f"UPDATE {table_name} SET kev_held = false WHERE kev_held IS NULL")
        connection.execute(
            f"ALTER TABLE {table_name} ALTER COLUMN kev_held SET DEFAULT false"
        )
        connection.execute(
            f"ALTER TABLE {table_name} ALTER COLUMN kev_held SET NOT NULL"
        )


def _migrate_close_columns(connection: duckdb.DuckDBPyConnection) -> None:
    """Add semantic close columns without promoting ambiguous legacy values."""
    for table_name in ("raw_deals", "normalized_deals"):
        columns = {
            row[1] for row in connection.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        }
        for column_name in ("planned_close_at", "actual_closed_at"):
            if column_name not in columns:
                connection.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} TIMESTAMP"
                )
