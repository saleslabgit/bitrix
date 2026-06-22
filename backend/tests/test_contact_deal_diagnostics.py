from datetime import datetime, timezone
from decimal import Decimal

import duckdb

from app.pipeline.normalization import normalize_local_data
from app.reports.analytics import list_contact_analytics
from app.reports.contact_deal_diagnostics import (
    get_explicit_contact_deal_diagnostic,
    reconcile_explicit_contact_deals,
    verify_bitrix_item_list_contact_links,
    verify_explicit_bitrix_contact_deals,
)
from app.storage import initialize_schema


SUPPLIED_DEAL_IDS = (1, 2, 3, 4, 5, 6, 7)


def test_exact_id_local_diagnostic_categorizes_supplied_deals() -> None:
    with duckdb.connect(database=":memory:") as connection:
        _load_designer_mismatch_dataset(connection)

        diagnostic = get_explicit_contact_deal_diagnostic(
            connection,
            contact_id=661,
            deal_ids=(1, 5, 8),
        )
        rows = {row.deal_id: row for row in diagnostic.deals}

    assert diagnostic.supplied_deal_ids == (1, 5, 8)
    assert rows[1].raw_deal_exists is True
    assert rows[1].has_contact_link is True
    assert rows[1].counts_for_contact is True
    assert rows[1].divergence_reason == "counts_for_contact"
    assert rows[5].raw_deal_exists is True
    assert rows[5].has_contact_link is False
    assert rows[5].linked_contact_ids == (900,)
    assert rows[5].analytical_contact_id == 900
    assert rows[5].divergence_reason == "missing_contact_link_assigned_to_another_contact"
    assert rows[8].raw_deal_exists is False
    assert rows[8].linked_contact_ids == ()
    assert rows[8].divergence_reason == "missing_raw_deal"


def test_exact_id_bitrix_verification_is_read_only_and_bounded_to_supplied_ids() -> None:
    client = ExplicitDealVerificationClient()

    verification = verify_explicit_bitrix_contact_deals(
        client=client,
        contact_id=661,
        deal_ids=(7, 1, 5, 5),
    )
    relations = {row.deal_id: row for row in verification.relations}

    assert client.listed_deal_ids == ((1, 5, 7),)
    assert client.linked_deal_ids == (1, 5, 7)
    assert verification.methods_used == ("crm.deal.list", "crm.deal.contact.items.get")
    assert verification.supplied_deal_ids == (1, 5, 7)
    assert verification.bitrix_deal_ids == (1, 5, 7)
    assert verification.confirmed_contact_deal_ids == (1, 5, 7)
    assert relations[5].linked_contact_ids == (661, 900)
    assert relations[5].has_contact_link is True


def test_item_list_verification_is_bounded_and_preserves_contact_ids() -> None:
    client = ItemListVerificationClient()

    verification = verify_bitrix_item_list_contact_links(
        client=client,
        contact_id=661,
        deal_ids=(7, 1, 5, 5),
    )
    rows = {row.deal_id: row for row in verification.rows}

    assert client.listed_deal_ids == ((1, 5, 7),)
    assert verification.methods_used == ("crm.item.fields", "crm.item.list")
    assert verification.supplied_deal_ids == (1, 5, 7)
    assert verification.returned_deal_ids == (1, 5, 7)
    assert verification.contact_related_fields == ("contactId", "contactIds")
    assert "fm" not in verification.selected_fields
    assert rows[1].returned_contact_ids == (661,)
    assert rows[5].returned_contact_ids == (661, 900)
    assert rows[7].has_contact_link is True
    assert verification.is_complete_for_contact is True


def test_reconciliation_inserts_only_confirmed_missing_links_and_renormalizes() -> None:
    with duckdb.connect(database=":memory:") as connection:
        _load_designer_mismatch_dataset(connection)

        result = reconcile_explicit_contact_deals(
            connection,
            client=ExplicitDealVerificationClient(),
            contact_id=661,
            deal_ids=SUPPLIED_DEAL_IDS,
        )
        analytics = {
            row.contact_id: row for row in list_contact_analytics(connection, limit=10).items
        }
        links = connection.execute(
            """
            SELECT deal_id, contact_id
            FROM raw_deal_contact_links
            WHERE contact_id = 661
            ORDER BY deal_id
            """
        ).fetchall()

    assert result.status.state == "success"
    assert result.status.is_active is True
    assert result.confirmed_contact_deal_ids == SUPPLIED_DEAL_IDS
    assert result.inserted_raw_deal_ids == ()
    assert result.inserted_link_deal_ids == (5, 6, 7)
    assert result.skipped_deal_ids == ()
    assert links == [(1, 661), (2, 661), (3, 661), (4, 661), (5, 661), (6, 661), (7, 661)]
    assert analytics[661].total_deals_count == 7
    assert all(row.counts_for_contact for row in result.local_after.deals)


def test_reconciliation_does_not_change_local_data_without_confirmed_links() -> None:
    with duckdb.connect(database=":memory:") as connection:
        _load_designer_mismatch_dataset(connection)

        result = reconcile_explicit_contact_deals(
            connection,
            client=NoContactRelationClient(),
            contact_id=661,
            deal_ids=(5, 6, 7),
        )
        links = connection.execute(
            """
            SELECT deal_id
            FROM raw_deal_contact_links
            WHERE contact_id = 661
            ORDER BY deal_id
            """
        ).fetchall()

    assert result.status.state == "error"
    assert result.status.is_active is False
    assert result.confirmed_contact_deal_ids == ()
    assert result.inserted_link_deal_ids == ()
    assert links == [(1,), (2,), (3,), (4,)]


def test_diagnostic_response_contains_only_safe_fields() -> None:
    with duckdb.connect(database=":memory:") as connection:
        _load_designer_mismatch_dataset(connection)

        diagnostic = get_explicit_contact_deal_diagnostic(
            connection,
            contact_id=661,
            deal_ids=(1, 5),
        )

    assert "phone" not in str(diagnostic).lower()
    assert "email" not in str(diagnostic).lower()
    assert "address" not in str(diagnostic).lower()
    assert "comment" not in str(diagnostic).lower()


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
        VALUES ('USD', DATE '2025-01-01', 3.30000000, 3.30000000, 'NBRB', ?)
        """,
        [datetime(2025, 1, 1, tzinfo=timezone.utc)],
    )
    normalize_local_data(connection)


class ExplicitDealVerificationClient:
    def __init__(self) -> None:
        self.listed_deal_ids: tuple[tuple[int, ...], ...] = ()
        self.linked_deal_ids: tuple[int, ...] = ()

    def list_deals_by_ids(self, deal_ids: tuple[int, ...]) -> list[dict[str, object]]:
        self.listed_deal_ids = (*self.listed_deal_ids, tuple(deal_ids))
        return [_deal_row(deal_id) for deal_id in deal_ids if deal_id in SUPPLIED_DEAL_IDS]

    def get_deal_contact_links(self, deal_id: int) -> list[dict[str, object]]:
        self.linked_deal_ids = (*self.linked_deal_ids, deal_id)
        if deal_id <= 4:
            return [{"DEAL_ID": str(deal_id), "CONTACT_ID": "661", "IS_PRIMARY": "Y"}]
        return [
            {"DEAL_ID": str(deal_id), "CONTACT_ID": "900", "IS_PRIMARY": "Y"},
            {"DEAL_ID": str(deal_id), "CONTACT_ID": "661", "IS_PRIMARY": "N"},
        ]


class NoContactRelationClient(ExplicitDealVerificationClient):
    def get_deal_contact_links(self, deal_id: int) -> list[dict[str, object]]:
        self.linked_deal_ids = (*self.linked_deal_ids, deal_id)
        return [{"DEAL_ID": str(deal_id), "CONTACT_ID": "900", "IS_PRIMARY": "Y"}]


class ItemListVerificationClient:
    def __init__(self) -> None:
        self.listed_deal_ids: tuple[tuple[int, ...], ...] = ()

    def get_deal_item_fields(self) -> dict[str, object]:
        return {
            "id": {},
            "title": {},
            "opportunity": {},
            "currencyId": {},
            "createdTime": {},
            "closedTime": {},
            "stageId": {},
            "categoryId": {},
            "contactId": {},
            "contactIds": {},
            "fm": {},
        }

    def list_deal_items_with_select(
        self,
        select: tuple[str, ...],
        *,
        filter_: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        assert "*" not in select
        assert "fm" not in select
        deal_ids = tuple(filter_["@id"])
        self.listed_deal_ids = (*self.listed_deal_ids, deal_ids)
        return [
            _deal_item_row(deal_id)
            for deal_id in deal_ids
            if deal_id in SUPPLIED_DEAL_IDS
        ]


def _deal_row(deal_id: int) -> dict[str, object]:
    return {
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


def _deal_item_row(deal_id: int) -> dict[str, object]:
    return {
        "id": str(deal_id),
        "title": f"Deal {deal_id}",
        "opportunity": "100.00",
        "currencyId": "USD",
        "createdTime": f"2025-01-{deal_id:02d}T00:00:00+00:00",
        "closedTime": f"2025-01-{deal_id:02d}T00:00:00+00:00",
        "stageId": "WON",
        "categoryId": "0",
        "contactId": "661" if deal_id <= 4 else "900",
        "contactIds": ["661"] if deal_id <= 4 else ["900", "661"],
    }
