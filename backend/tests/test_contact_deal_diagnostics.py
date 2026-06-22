from datetime import datetime, timezone
from decimal import Decimal

import duckdb

from app.pipeline.normalization import normalize_local_data
from app.reports.contact_deal_diagnostics import (
    get_contact_deal_diagnostic,
    verify_bitrix_contact_deals,
)
from app.reports.analytics import list_contact_analytics
from app.storage import initialize_schema


def test_targeted_contact_deal_correction_adds_missing_links_and_renormalizes() -> None:
    with duckdb.connect(database=":memory:") as connection:
        _load_designer_mismatch_dataset(connection)

        before = get_contact_deal_diagnostic(connection, 661)
        verification = verify_bitrix_contact_deals(
            connection,
            client=ContactDealVerificationClient(),
            contact_id=661,
            apply_local_correction=True,
        )
        after = get_contact_deal_diagnostic(connection, 661)
        analytics = {
            row.contact_id: row for row in list_contact_analytics(connection, limit=10).items
        }

    assert before.local_linked_deal_ids == (1, 2, 3, 4)
    assert before.local_analytical_deal_ids == (1, 2, 3, 4)
    assert verification.methods_used == ("crm.deal.list",)
    assert verification.bitrix_deal_ids == (1, 2, 3, 4, 5, 6, 7)
    assert verification.raw_deals_inserted == 0
    assert verification.raw_links_inserted == 3
    assert verification.missing_local_link_deal_ids == ()
    assert after.local_linked_deal_ids == (1, 2, 3, 4, 5, 6, 7)
    assert after.local_analytical_deal_ids == (1, 2, 3, 4, 5, 6, 7)
    assert analytics[661].total_deals_count == 7


def _load_designer_mismatch_dataset(connection: duckdb.DuckDBPyConnection) -> None:
    initialize_schema(connection)
    connection.executemany(
        """
        INSERT INTO contact_type_rules (
            raw_value,
            normalized_type,
            priority,
            region,
            is_active
        )
        VALUES (?, ?, ?, ?, true)
        """,
        [
            ("61", "Дизайнер", 1, "Беларусь"),
            ("67", "Дилер", 3, "Беларусь"),
        ],
    )
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
            (661, "Designer Contact", "[61]"),
            (900, "Dealer Contact", "[67]"),
        ],
    )
    connection.execute(
        """
        INSERT INTO raw_stages (
            stage_id,
            category_id,
            status_group
        )
        VALUES ('WON', 0, 'won')
        """
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
        VALUES (?, ?, ?, 'USD', ?, ?, 'WON', 0, 'won')
        """,
        [
            (
                deal_id,
                f"Deal {deal_id}",
                Decimal("100.00"),
                datetime(2025, 1, deal_id, tzinfo=timezone.utc),
                datetime(2025, 1, deal_id, tzinfo=timezone.utc),
            )
            for deal_id in range(1, 8)
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
        VALUES (?, ?, ?, NULL, NULL)
        """,
        [
            (1, 661, True),
            (2, 661, True),
            (3, 661, True),
            (4, 661, True),
            (5, 900, True),
            (6, 900, True),
            (7, 900, True),
        ],
    )
    connection.execute(
        """
        INSERT INTO currency_rates (
            currency,
            rate_date,
            source_rate_byn,
            usd_rate_byn,
            rate_source,
            rate_fetched_at
        )
        VALUES ('USD', DATE '2025-01-01', 3.30000000, 3.30000000, 'test', ?)
        """,
        [datetime(2025, 1, 1, tzinfo=timezone.utc)],
    )
    normalize_local_data(connection)


class ContactDealVerificationClient:
    def list_deals_for_contact(self, contact_id: int) -> list[dict[str, object]]:
        assert contact_id == 661
        return [
            {
                "ID": str(deal_id),
                "TITLE": f"Deal {deal_id}",
                "OPPORTUNITY": "100.00",
                "CURRENCY_ID": "USD",
                "DATE_CREATE": f"2025-01-{deal_id:02d}T00:00:00+00:00",
                "CLOSEDATE": f"2025-01-{deal_id:02d}T00:00:00+00:00",
                "STAGE_ID": "WON",
                "CATEGORY_ID": "0",
                "CONTACT_ID": "661" if deal_id <= 4 else "900",
            }
            for deal_id in range(1, 8)
        ]
