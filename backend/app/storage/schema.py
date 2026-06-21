import duckdb


EXPECTED_TABLES = (
    "raw_contacts",
    "raw_deals",
    "raw_deal_contact_links",
    "raw_stages",
    "contact_type_rules",
    "currency_rates",
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
        CREATE TABLE IF NOT EXISTS raw_deals (
            deal_id BIGINT PRIMARY KEY,
            deal_name VARCHAR NOT NULL,
            amount_original DECIMAL(18, 2) NOT NULL,
            currency_original VARCHAR NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            closed_at TIMESTAMPTZ,
            stage_id VARCHAR NOT NULL,
            category_id INTEGER,
            status_group VARCHAR NOT NULL CHECK (status_group IN ('won', 'open', 'lost'))
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
            rate_fetched_at TIMESTAMPTZ NOT NULL,
            PRIMARY KEY (currency, rate_date)
        )
        """
    )
