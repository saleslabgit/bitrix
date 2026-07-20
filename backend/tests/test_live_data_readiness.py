from datetime import date, datetime, timezone
from decimal import Decimal

import duckdb
import pytest

from app.domain import ContactSnapshot, DealContactLink, DealSnapshot, StageSnapshot
from app.pipeline.approved_contact_type_rules import (
    APPROVED_CONTACT_TYPE_RULES,
    replace_contact_type_rules,
)
from app.pipeline.currency_rates import NbrbRateClient, load_currency_rates_for_raw_deals
from app.pipeline.local_refresh import apply_approved_rules_and_renormalize
from app.pipeline.normalization import NO_CONTACT_NAME, UNDEFINED_VALUE
from app.storage import initialize_schema
from app.storage.loaders import load_bitrix_raw_data


def test_approved_rules_normalize_option_combinations_and_missing_type() -> None:
    with duckdb.connect(database=":memory:") as connection:
        _load_option_rule_dataset(connection)

        result = apply_approved_rules_and_renormalize(connection)
        contacts = {
            row[0]: row[1:]
            for row in connection.execute(
                """
                SELECT contact_id, contact_type_normalized, region_normalized
                FROM normalized_contacts
                ORDER BY contact_id
                """
            ).fetchall()
        }
        deals = {
            row[0]: row[1:]
            for row in connection.execute(
                """
                SELECT
                    deal_id,
                    analytical_contact_id,
                    analytical_contact_name,
                    contact_type_normalized,
                    region_normalized
                FROM normalized_deals
                ORDER BY deal_id
                """
            ).fetchall()
        }

    assert result.rules_count == len(APPROVED_CONTACT_TYPE_RULES)
    assert result.active_rules_count == 13
    assert contacts[1] == ("Дизайнер", "Беларусь")
    assert contacts[2] == ("Конечный клиент", "Без региона")
    assert contacts[3] == ("Конечный клиент", "Без региона")
    assert contacts[4] == (UNDEFINED_VALUE, UNDEFINED_VALUE)
    assert contacts[5] == (UNDEFINED_VALUE, UNDEFINED_VALUE)
    assert contacts[6] == ("Дилер", "Россия")
    assert deals[1] == (1, "Contact 1", "Дизайнер", "Беларусь")
    assert deals[2] == (None, NO_CONTACT_NAME, UNDEFINED_VALUE, UNDEFINED_VALUE)
    assert deals[3] == (6, "Contact 6", "Дилер", "Россия")


def test_currency_rate_loader_uses_mocked_nbrb_dynamics() -> None:
    calls: list[str] = []

    def transport(url: str) -> object:
        calls.append(url)
        if url.endswith("/currencies"):
            return [
                {
                    "Cur_ID": 431,
                    "Cur_Abbreviation": "USD",
                    "Cur_Scale": 1,
                    "Cur_DateStart": "2020-01-01T00:00:00",
                    "Cur_DateEnd": "2050-01-01T00:00:00",
                },
                {
                    "Cur_ID": 451,
                    "Cur_Abbreviation": "EUR",
                    "Cur_Scale": 1,
                    "Cur_DateStart": "2020-01-01T00:00:00",
                    "Cur_DateEnd": "2050-01-01T00:00:00",
                },
                {
                    "Cur_ID": 456,
                    "Cur_Abbreviation": "RUB",
                    "Cur_Scale": 100,
                    "Cur_DateStart": "2020-01-01T00:00:00",
                    "Cur_DateEnd": "2050-01-01T00:00:00",
                },
            ]
        if "dynamics/431" in url:
            return [
                {"Date": "2025-01-01T00:00:00", "Cur_OfficialRate": 3.3},
                {"Date": "2025-01-02T00:00:00", "Cur_OfficialRate": 3.4},
            ]
        if "dynamics/451" in url:
            return [
                {"Date": "2025-01-01T00:00:00", "Cur_OfficialRate": 3.6},
                {"Date": "2025-01-02T00:00:00", "Cur_OfficialRate": 3.7},
            ]
        if "dynamics/456" in url:
            return [
                {"Date": "2025-01-01T00:00:00", "Cur_OfficialRate": 3.5},
                {"Date": "2025-01-02T00:00:00", "Cur_OfficialRate": 3.6},
            ]
        raise AssertionError(f"Unexpected URL: {url}")

    with duckdb.connect(database=":memory:") as connection:
        initialize_schema(connection)
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
            VALUES (?, ?, ?, ?, ?, ?, 'SYN:WON', 1, 'won')
            """,
            [
                (
                    1,
                    "Deal 1",
                    Decimal("10.00"),
                    "BYN",
                    datetime(2025, 1, 1, tzinfo=timezone.utc),
                    None,
                ),
                (
                    2,
                    "Deal 2",
                    Decimal("10.00"),
                    "EUR",
                    datetime(2025, 1, 2, tzinfo=timezone.utc),
                    None,
                ),
                (
                    3,
                    "Deal 3",
                    Decimal("10.00"),
                    "RUB",
                    datetime(2025, 1, 2, tzinfo=timezone.utc),
                    None,
                ),
                (
                    4,
                    "Deal 4",
                    Decimal("10.00"),
                    "USD",
                    datetime(2025, 1, 2, tzinfo=timezone.utc),
                    None,
                ),
            ],
        )
        connection.execute("UPDATE raw_deals SET actual_closed_at = created_at")

        result = load_currency_rates_for_raw_deals(
            connection,
            client=NbrbRateClient(transport=transport),
            as_of_date=date(2025, 1, 2),
        )
        rows = connection.execute(
            """
            SELECT currency, rate_date, source_rate_byn, usd_rate_byn
            FROM currency_rates
            ORDER BY currency, rate_date
            """
        ).fetchall()

    assert result is not None
    assert result.currencies == ("BYN", "EUR", "RUB", "USD")
    assert result.rows_loaded == 8
    assert any("rates/dynamics/431" in call for call in calls)
    assert (
        "RUB",
        date(2025, 1, 2),
        Decimal("0.03600000"),
        Decimal("3.40000000"),
    ) in rows


def test_currency_rate_loader_raises_safe_error_when_raw_deals_have_no_rate_rows() -> None:
    def transport(url: str) -> object:
        if url.endswith("/currencies"):
            return [
                {
                    "Cur_ID": 431,
                    "Cur_Abbreviation": "USD",
                    "Cur_Scale": 1,
                    "Cur_DateStart": "2020-01-01T00:00:00",
                    "Cur_DateEnd": "2050-01-01T00:00:00",
                },
                {
                    "Cur_ID": 451,
                    "Cur_Abbreviation": "EUR",
                    "Cur_Scale": 1,
                    "Cur_DateStart": "2020-01-01T00:00:00",
                    "Cur_DateEnd": "2050-01-01T00:00:00",
                },
            ]
        if "dynamics/431" in url:
            return [{"Date": "2025-01-01T00:00:00", "Cur_OfficialRate": 3.3}]
        if "dynamics/451" in url:
            return [{"Date": "2025-01-02T00:00:00", "Cur_OfficialRate": 3.6}]
        raise AssertionError(f"Unexpected URL: {url}")

    with duckdb.connect(database=":memory:") as connection:
        initialize_schema(connection)
        connection.execute(
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
            VALUES (?, ?, ?, ?, ?, ?, 'SYN:WON', 1, 'won')
            """,
            (
                1,
                "Deal 1",
                Decimal("10.00"),
                "EUR",
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                None,
            ),
        )
        connection.execute("UPDATE raw_deals SET actual_closed_at = created_at")

        with pytest.raises(ValueError, match="No currency rate rows were loaded"):
            load_currency_rates_for_raw_deals(
                connection,
                client=NbrbRateClient(transport=transport),
                as_of_date=date(2025, 1, 1),
            )
        rate_count = connection.execute("SELECT COUNT(*) FROM currency_rates").fetchone()[0]

    assert rate_count == 0


def test_replace_contact_type_rules_accepts_empty_rules_and_clears_existing_rows() -> None:
    with duckdb.connect(database=":memory:") as connection:
        initialize_schema(connection)
        initial_count = replace_contact_type_rules(connection)

        empty_count = replace_contact_type_rules(connection, rules=())
        stored_count = connection.execute("SELECT COUNT(*) FROM contact_type_rules").fetchone()[
            0
        ]

    assert initial_count == len(APPROVED_CONTACT_TYPE_RULES)
    assert empty_count == 0
    assert stored_count == 0


def _load_option_rule_dataset(connection: duckdb.DuckDBPyConnection) -> None:
    initialize_schema(connection)
    load_bitrix_raw_data(
        connection,
        contacts=[
            ContactSnapshot(
                contact_id=1,
                contact_name="Contact 1",
                contact_type_raw="[61, 59, 65]",
            ),
            ContactSnapshot(contact_id=2, contact_name="Contact 2"),
            ContactSnapshot(contact_id=3, contact_name="Contact 3", contact_type_raw="[]"),
            ContactSnapshot(
                contact_id=4,
                contact_name="Contact 4",
                contact_type_raw="[67]",
            ),
            ContactSnapshot(
                contact_id=5,
                contact_name="Contact 5",
                contact_type_raw="[9999]",
            ),
            ContactSnapshot(
                contact_id=6,
                contact_name="Contact 6",
                contact_type_raw="[2343, 2341]",
            ),
        ],
        deals=[
            DealSnapshot(
                deal_id=1,
                deal_name="Deal 1",
                amount_original=Decimal("10.00"),
                currency_original="USD",
                created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
                stage_id="SYN:WON",
                status_group="won",
            ),
            DealSnapshot(
                deal_id=2,
                deal_name="Deal 2",
                amount_original=Decimal("10.00"),
                currency_original="USD",
                created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
                stage_id="SYN:WON",
                status_group="won",
            ),
            DealSnapshot(
                deal_id=3,
                deal_name="Deal 3",
                amount_original=Decimal("10.00"),
                currency_original="USD",
                created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
                stage_id="SYN:WON",
                status_group="won",
            ),
        ],
        links=[
            DealContactLink(deal_id=1, contact_id=1),
            DealContactLink(deal_id=1, contact_id=2, is_primary=True),
            DealContactLink(deal_id=2, contact_id=4, is_primary=True),
            DealContactLink(deal_id=2, contact_id=5),
            DealContactLink(deal_id=3, contact_id=6),
        ],
        stages=[
            StageSnapshot(stage_id="SYN:WON", category_id=None, status_group="won"),
        ],
    )
