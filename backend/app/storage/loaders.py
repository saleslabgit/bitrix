import duckdb

from app.pipeline.synthetic_dataset import SyntheticDataset


RAW_TABLES = (
    "raw_deal_contact_links",
    "raw_deals",
    "raw_contacts",
    "raw_stages",
    "contact_type_rules",
    "currency_rates",
)


def clear_raw_tables(connection: duckdb.DuckDBPyConnection) -> None:
    for table_name in RAW_TABLES:
        connection.execute(f"DELETE FROM {table_name}")


def load_synthetic_dataset(
    connection: duckdb.DuckDBPyConnection,
    dataset: SyntheticDataset,
) -> None:
    clear_raw_tables(connection)

    connection.executemany(
        """
        INSERT INTO raw_contacts (
            contact_id,
            contact_name,
            contact_type_raw
        )
        VALUES (?, ?, ?)
        """,
        [
            (contact.contact_id, contact.contact_name, contact.contact_type_raw)
            for contact in dataset.contacts
        ],
    )
    connection.executemany(
        """
        INSERT INTO raw_deals (
            deal_id,
            deal_name,
            amount_original,
            currency_original,
            created_at,
            closed_at,
            stage_id,
            category_id,
            status_group
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                deal.deal_id,
                deal.deal_name,
                deal.amount_original,
                deal.currency_original,
                deal.created_at,
                deal.closed_at,
                deal.stage_id,
                deal.category_id,
                deal.status_group,
            )
            for deal in dataset.deals
        ],
    )
    connection.executemany(
        """
        INSERT INTO raw_deal_contact_links (
            deal_id,
            contact_id,
            is_primary,
            sort_order,
            role_id
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                link.deal_id,
                link.contact_id,
                link.is_primary,
                link.sort_order,
                link.role_id,
            )
            for link in dataset.deal_contact_links
        ],
    )
    connection.executemany(
        """
        INSERT INTO raw_stages (
            stage_id,
            category_id,
            status_group
        )
        VALUES (?, ?, ?)
        """,
        [
            (stage.stage_id, stage.category_id, stage.status_group)
            for stage in dataset.stages
        ],
    )
    connection.executemany(
        """
        INSERT INTO contact_type_rules (
            raw_value,
            normalized_type,
            priority,
            region,
            is_active
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                rule.raw_value,
                rule.normalized_type,
                rule.priority,
                rule.region,
                rule.is_active,
            )
            for rule in dataset.contact_type_rules
        ],
    )
    connection.executemany(
        """
        INSERT INTO currency_rates (
            currency,
            rate_date,
            source_rate_byn,
            usd_rate_byn,
            rate_source,
            rate_fetched_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                rate.currency,
                rate.rate_date,
                rate.source_rate_byn,
                rate.usd_rate_byn,
                rate.rate_source,
                rate.rate_fetched_at,
            )
            for rate in dataset.currency_rates
        ],
    )
