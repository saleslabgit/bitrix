from datetime import datetime, timezone
from decimal import Decimal

import duckdb
import app.reports.contact_deal_diagnostics as diagnostics_module

from app.pipeline.normalization import normalize_local_data
from app.reports.analytics import list_contact_analytics, list_deal_analytics
from app.reports.contact_deal_diagnostics import (
    get_explicit_contact_deal_diagnostic,
    reconcile_explicit_contact_deals,
    verify_bitrix_item_list_contact_links,
    verify_explicit_bitrix_contact_deals,
)
from app.storage import initialize_schema
from app.storage.status import get_active_dataset_run


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


def test_reconciliation_stores_planned_and_actual_close_history_and_kev_idempotently() -> None:
    client = FactualReconciliationClient()
    with duckdb.connect(database=":memory:") as connection:
        _load_designer_mismatch_dataset(connection)

        first = reconcile_explicit_contact_deals(
            connection, client=client, contact_id=661, deal_ids=(8,)
        )
        second = reconcile_explicit_contact_deals(
            connection, client=client, contact_id=661, deal_ids=(8,)
        )
        raw = connection.execute(
            """
            SELECT closed_at, planned_close_at, actual_closed_at, kev_held
            FROM raw_deals WHERE deal_id = 8
            """
        ).fetchone()
        normalized = connection.execute(
            "SELECT actual_closed_at FROM normalized_deals WHERE deal_id = 8"
        ).fetchone()
        history = connection.execute(
            "SELECT history_id, deal_id, stage_id, stage_semantic_id FROM raw_deal_stage_history WHERE deal_id = 8 ORDER BY history_id"
        ).fetchall()
        api_row = list_deal_analytics(connection, deal_id=8).items[0]

    assert first.status.state == "success"
    assert first.inserted_raw_deal_ids == (8,)
    assert first.methods_used[-1] == "crm.stagehistory.list"
    assert second.status.state == "success"
    assert client.history_calls == ((8,), (8,))
    assert raw == (None, datetime(2025, 2, 1), datetime(2025, 6, 1), True)
    assert normalized == (datetime(2025, 6, 1),)
    assert history == [(799, 8, "WON", "S"), (800, 8, "WON", "S")]
    assert api_row.closed_date.isoformat() == "2025-06-01"
    assert api_row.cycle_days == 151


def test_reconciliation_repairs_existing_missing_factual_close_and_supports_moved_time() -> None:
    client = FactualReconciliationClient(history_rows=[])
    with duckdb.connect(database=":memory:") as connection:
        _load_designer_mismatch_dataset(connection)
        connection.execute("UPDATE raw_deals SET actual_closed_at = NULL WHERE deal_id = 5")

        result = reconcile_explicit_contact_deals(
            connection, client=client, contact_id=661, deal_ids=(5,)
        )
        actual = connection.execute(
            "SELECT actual_closed_at FROM raw_deals WHERE deal_id = 5"
        ).fetchone()[0]

    assert result.status.state == "success"
    assert actual == datetime(2025, 7, 1)
    assert client.history_calls == ((5,),)


def test_reconciliation_loads_history_once_for_multiple_closed_deals() -> None:
    client = FactualReconciliationClient()
    with duckdb.connect(database=":memory:") as connection:
        _load_designer_mismatch_dataset(connection)

        result = reconcile_explicit_contact_deals(
            connection, client=client, contact_id=661, deal_ids=(9, 8)
        )

    assert result.status.state == "success"
    assert result.inserted_raw_deal_ids == (8, 9)
    assert client.history_calls == ((8, 9),)


def test_reconciliation_existing_reclose_updates_stale_may_close_to_june() -> None:
    client = FactualReconciliationClient(existing_state=True)
    with duckdb.connect(database=":memory:") as connection:
        _load_designer_mismatch_dataset(connection)
        connection.execute(
            "UPDATE raw_deals SET actual_closed_at = TIMESTAMP '2025-05-01' WHERE deal_id = 5"
        )
        normalize_local_data(connection)

        result = reconcile_explicit_contact_deals(
            connection, client=client, contact_id=661, deal_ids=(5,)
        )
        raw_actual = connection.execute(
            "SELECT actual_closed_at FROM raw_deals WHERE deal_id = 5"
        ).fetchone()[0]
        api_row = list_deal_analytics(connection, deal_id=5).items[0]

    assert result.status.state == "success"
    assert client.history_calls == ((5,),)
    assert raw_actual == datetime(2025, 6, 1)
    assert api_row.closed_date.isoformat() == "2025-06-01"
    assert api_row.cycle_days == 147


def test_reconciliation_compares_and_updates_complete_approved_deal_state() -> None:
    client = FactualReconciliationClient(
        existing_state=True,
        deal_name="Changed Deal",
        amount="250.50",
        currency="EUR",
        created_time="2025-01-02T00:00:00+00:00",
    )
    with duckdb.connect(database=":memory:") as connection:
        _load_designer_mismatch_dataset(connection)

        result = reconcile_explicit_contact_deals(
            connection, client=client, contact_id=661, deal_ids=(5,)
        )
        raw = connection.execute(
            """
            SELECT deal_name, amount_original, currency_original, created_at
            FROM raw_deals WHERE deal_id = 5
            """
        ).fetchone()
        normalized = connection.execute(
            """
            SELECT deal_name, amount_original, currency_original, created_at
            FROM normalized_deals WHERE deal_id = 5
            """
        ).fetchone()

    expected = ("Changed Deal", Decimal("250.50"), "EUR", datetime(2025, 1, 2))
    assert result.status.state == "success"
    assert raw == expected
    assert normalized == expected


def test_reconciliation_unchanged_closed_deal_fetches_history_without_deal_upsert(
    monkeypatch,
) -> None:
    client = ExplicitDealVerificationClient()
    upserted: list[tuple[int, ...]] = []
    original = diagnostics_module._upsert_raw_deals

    def capture_upserts(connection, deals) -> None:
        upserted.append(tuple(deal.deal_id for deal in deals))
        original(connection, deals)

    monkeypatch.setattr(diagnostics_module, "_upsert_raw_deals", capture_upserts)
    with duckdb.connect(database=":memory:") as connection:
        _load_designer_mismatch_dataset(connection)

        result = reconcile_explicit_contact_deals(
            connection, client=client, contact_id=661, deal_ids=(1,)
        )

    assert result.status.state == "success"
    assert client.history_calls == ((1,),)
    assert upserted == [()]


def test_reconciliation_open_deal_clears_factual_close_without_using_old_history() -> None:
    client = FactualReconciliationClient(status="open")
    with duckdb.connect(database=":memory:") as connection:
        _load_designer_mismatch_dataset(connection)
        connection.execute("INSERT INTO raw_stages VALUES ('OPEN', 0, 'open')")
        connection.execute(
            "UPDATE raw_deals SET actual_closed_at = TIMESTAMP '2025-01-05' WHERE deal_id = 5"
        )
        connection.execute(
            "INSERT INTO raw_deal_stage_history VALUES (500, 5, 3, TIMESTAMP '2025-01-05', 0, 'WON', 'S')"
        )

        result = reconcile_explicit_contact_deals(
            connection, client=client, contact_id=661, deal_ids=(5,)
        )
        actual = connection.execute(
            "SELECT actual_closed_at FROM raw_deals WHERE deal_id = 5"
        ).fetchone()[0]

    assert result.status.state == "success"
    assert actual is None
    assert client.history_calls == ()


def test_reconciliation_missing_factual_close_preserves_previous_active_dataset() -> None:
    client = FactualReconciliationClient(history_rows=[], moved_time=None)
    with duckdb.connect(database=":memory:") as connection:
        _load_designer_mismatch_dataset(connection)
        successful = reconcile_explicit_contact_deals(
            connection,
            client=FactualReconciliationClient(),
            contact_id=661,
            deal_ids=(8,),
        )
        before = connection.execute("SELECT COUNT(*) FROM raw_deals").fetchone()[0]
        active_before = get_active_dataset_run(connection)

        result = reconcile_explicit_contact_deals(
            connection, client=client, contact_id=661, deal_ids=(9,)
        )
        raw_count = connection.execute("SELECT COUNT(*) FROM raw_deals").fetchone()[0]
        history_count = connection.execute(
            "SELECT COUNT(*) FROM raw_deal_stage_history WHERE deal_id = 9"
        ).fetchone()[0]
        link_count = connection.execute(
            "SELECT COUNT(*) FROM raw_deal_contact_links WHERE deal_id = 9"
        ).fetchone()[0]
        active_after = get_active_dataset_run(connection)

    assert successful.status.state == "success"
    assert result.status.state == "error"
    assert result.status.is_active is False
    assert raw_count == before
    assert history_count == 0
    assert link_count == 0
    assert active_before is not None
    assert active_after == active_before


def test_reconciliation_rolls_back_deal_history_and_link_when_normalization_fails(
    monkeypatch,
) -> None:
    with duckdb.connect(database=":memory:") as connection:
        _load_designer_mismatch_dataset(connection)
        successful = reconcile_explicit_contact_deals(
            connection,
            client=FactualReconciliationClient(),
            contact_id=661,
            deal_ids=(8,),
        )
        active_before = get_active_dataset_run(connection)
        raw_before = connection.execute("SELECT COUNT(*) FROM raw_deals").fetchone()[0]

        def fail_normalization(connection) -> None:
            raise RuntimeError("test failure")

        monkeypatch.setattr(
            diagnostics_module,
            "normalize_local_data",
            fail_normalization,
        )

        result = reconcile_explicit_contact_deals(
            connection,
            client=FactualReconciliationClient(),
            contact_id=661,
            deal_ids=(9,),
        )
        active_after = get_active_dataset_run(connection)
        raw_after = connection.execute("SELECT COUNT(*) FROM raw_deals").fetchone()[0]
        history_after = connection.execute(
            "SELECT COUNT(*) FROM raw_deal_stage_history WHERE deal_id = 9"
        ).fetchone()[0]
        link_after = connection.execute(
            "SELECT COUNT(*) FROM raw_deal_contact_links WHERE deal_id = 9"
        ).fetchone()[0]

    assert successful.status.state == "success"
    assert result.status.state == "error"
    assert raw_after == raw_before
    assert history_after == 0
    assert link_after == 0
    assert active_after == active_before


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
    connection.execute(
        """
        UPDATE raw_deals
        SET planned_close_at = closed_at, actual_closed_at = closed_at, closed_at = NULL
        """
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
        self.history_calls: tuple[tuple[int, ...], ...] = ()

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

    def list_deal_stage_history(self, deal_ids: tuple[int, ...]) -> list[dict[str, object]]:
        self.history_calls = (*self.history_calls, tuple(deal_ids))
        return [
            {
                "ID": str(deal_id * 100),
                "TYPE_ID": "3",
                "OWNER_ID": str(deal_id),
                "CREATED_TIME": f"2025-01-{deal_id:02d}T00:00:00+00:00",
                "CATEGORY_ID": "0",
                "STAGE_ID": "WON",
                "STAGE_SEMANTIC_ID": "S",
            }
            for deal_id in deal_ids
        ]


class FactualReconciliationClient(ExplicitDealVerificationClient):
    def __init__(
        self,
        *,
        history_rows: list[dict[str, object]] | None = None,
        moved_time: str | None = "2025-07-01T00:00:00+00:00",
        status: str = "won",
        existing_state: bool = False,
        deal_name: str | None = None,
        amount: str = "100.00",
        currency: str = "USD",
        created_time: str | None = None,
    ) -> None:
        super().__init__()
        self.history_calls: tuple[tuple[int, ...], ...] = ()
        self.history_rows = history_rows
        self.moved_time = moved_time
        self.status = status
        self.existing_state = existing_state
        self.deal_name = deal_name
        self.amount = amount
        self.currency = currency
        self.created_time = created_time

    def list_deals_by_ids(self, deal_ids: tuple[int, ...]) -> list[dict[str, object]]:
        self.listed_deal_ids = (*self.listed_deal_ids, tuple(deal_ids))
        return [self._row(deal_id) for deal_id in deal_ids]

    def get_deal_contact_links(self, deal_id: int) -> list[dict[str, object]]:
        self.linked_deal_ids = (*self.linked_deal_ids, deal_id)
        return [{"DEAL_ID": str(deal_id), "CONTACT_ID": "661", "IS_PRIMARY": "Y"}]

    def list_deal_stage_history(self, deal_ids: tuple[int, ...]) -> list[dict[str, object]]:
        self.history_calls = (*self.history_calls, tuple(deal_ids))
        if self.history_rows is not None:
            return self.history_rows
        return [
            row
            for deal_id in deal_ids
            for row in (
                {
                    "ID": str(deal_id * 100 - 1),
                    "TYPE_ID": "3",
                    "OWNER_ID": str(deal_id),
                    "CREATED_TIME": "2025-05-01T00:00:00+00:00",
                    "CATEGORY_ID": "0",
                    "STAGE_ID": "WON",
                    "STAGE_SEMANTIC_ID": "S",
                },
                {
                    "ID": str(deal_id * 100),
                    "TYPE_ID": "3",
                    "OWNER_ID": str(deal_id),
                    "CREATED_TIME": "2025-06-01T00:00:00+00:00",
                    "CATEGORY_ID": "0",
                    "STAGE_ID": "WON",
                    "STAGE_SEMANTIC_ID": "S",
                },
            )
        ]

    def _row(self, deal_id: int) -> dict[str, object]:
        stage_id = "OPEN" if self.status == "open" else "WON"
        created_time = self.created_time or (
            f"2025-01-{deal_id:02d}T00:00:00+00:00"
            if self.existing_state
            else "2025-01-01T00:00:00+00:00"
        )
        planned_time = (
            f"2025-01-{deal_id:02d}T00:00:00+00:00"
            if self.existing_state
            else "2025-02-01T00:00:00+00:00"
        )
        row = {
            "ID": str(deal_id),
            "TITLE": self.deal_name or f"Deal {deal_id}",
            "OPPORTUNITY": self.amount,
            "CURRENCY_ID": self.currency,
            "DATE_CREATE": created_time,
            "CLOSEDATE": planned_time,
            "STAGE_ID": stage_id,
            "CATEGORY_ID": "0",
            "CONTACT_ID": "661",
            "UF_CRM_1716895716": "N" if self.existing_state else "Y",
        }
        if self.moved_time is not None:
            row["MOVED_TIME"] = self.moved_time
        return row


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
