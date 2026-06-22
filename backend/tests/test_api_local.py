from datetime import date
from decimal import Decimal

import duckdb
import pytest
from fastapi import HTTPException

from app import main
from app.local_database import get_connection, reset_connection
from app.main import (
    dataset_status,
    dataset_profile,
    meta_filters,
    report_abc,
    report_concentration,
    report_contact_analytics,
    report_contacts,
    report_deal_analytics,
    report_deal_cycle,
    report_rfm,
    report_stale_deals,
    report_type_region,
    run_local_synthetic_sync,
    sync_status,
)
from app.reports.local import get_filter_metadata
from app.storage import initialize_schema


FORBIDDEN_RESPONSE_PARTS = (
    "phone",
    "email",
    "address",
    "messenger",
    "requisite",
    "comment",
    "file",
    "activity",
)


@pytest.fixture(autouse=True)
def configured_temp_storage(monkeypatch, tmp_path):
    reset_connection()
    monkeypatch.setattr(main.settings, "data_dir", tmp_path)
    monkeypatch.setattr(main.settings, "duckdb_path", tmp_path / "api.duckdb")
    yield
    reset_connection()


def test_api_status_run_and_filters_return_local_synthetic_data() -> None:
    run_response = run_local_synthetic_sync()
    status_response = sync_status()
    filters_response = meta_filters()

    assert run_response.dataset_kind == "local_synthetic"
    assert run_response.state == "success"
    assert "Bitrix" in run_response.message
    assert status_response.normalized_contacts_count == 10
    assert status_response.normalized_deals_count == 30
    assert set(filters_response.statuses) == {"won", "open", "lost"}
    assert "Synthetic Key" in filters_response.contact_types
    assert "Не определено" in filters_response.contact_types
    assert filters_response.min_created_at is not None
    assert filters_response.max_created_at is not None


def test_filter_metadata_initializes_empty_schema_for_direct_calls() -> None:
    with duckdb.connect(database=":memory:") as connection:
        filters_response = get_filter_metadata(connection)

    assert filters_response.contact_types == ()
    assert filters_response.regions == ()
    assert filters_response.statuses == ()
    assert filters_response.min_created_at is None
    assert filters_response.max_created_at is None
    assert filters_response.min_closed_at is None
    assert filters_response.max_closed_at is None


def test_meta_filters_returns_empty_metadata_before_dataset_is_prepared() -> None:
    filters_response = meta_filters()

    assert filters_response.contact_types == ()
    assert filters_response.regions == ()
    assert filters_response.statuses == ()
    assert filters_response.min_created_at is None
    assert filters_response.max_created_at is None
    assert filters_response.min_closed_at is None
    assert filters_response.max_closed_at is None


def test_meta_filters_rejects_empty_contact_types_for_active_non_empty_dataset() -> None:
    run_local_synthetic_sync()
    get_connection().execute("DELETE FROM normalized_contacts")

    with pytest.raises(HTTPException) as exc_info:
        meta_filters()

    assert exc_info.value.status_code == 503
    assert (
        exc_info.value.detail
        == "Filter metadata is temporarily unavailable. Keep previous options and retry."
    )


def test_filter_metadata_handles_empty_contacts_and_no_closed_deals() -> None:
    with duckdb.connect(database=":memory:") as connection:
        initialize_schema(connection)
        connection.execute(
            """
            INSERT INTO normalized_deals (
                deal_id,
                deal_name,
                amount_original,
                currency_original,
                created_at,
                closed_at,
                stage_id,
                category_id,
                status_group,
                analytical_contact_id,
                analytical_contact_name,
                contact_type_normalized,
                region_normalized
            )
            VALUES (
                1,
                'Open Deal',
                100.00,
                'USD',
                TIMESTAMP '2026-01-01 10:00:00',
                NULL,
                'OPEN',
                0,
                'open',
                NULL,
                'Без контакта',
                'Не определено',
                'Не определено'
            )
            """
        )

        filters_response = get_filter_metadata(connection)

    assert filters_response.contact_types == ()
    assert filters_response.regions == ()
    assert filters_response.statuses == ("open",)
    assert filters_response.min_created_at is not None
    assert filters_response.max_created_at is not None
    assert filters_response.min_closed_at is None
    assert filters_response.max_closed_at is None


def test_filter_metadata_ignores_null_distinct_values_from_older_local_schema() -> None:
    with duckdb.connect(database=":memory:") as connection:
        connection.execute(
            """
            CREATE TABLE normalized_contacts (
                contact_id BIGINT PRIMARY KEY,
                contact_name VARCHAR NOT NULL,
                contact_type_raw VARCHAR,
                contact_type_normalized VARCHAR,
                region_normalized VARCHAR
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
                status_group VARCHAR,
                analytical_contact_id BIGINT,
                analytical_contact_name VARCHAR NOT NULL,
                contact_type_normalized VARCHAR,
                region_normalized VARCHAR
            )
            """
        )
        connection.execute(
            """
            INSERT INTO normalized_contacts (
                contact_id,
                contact_name,
                contact_type_raw,
                contact_type_normalized,
                region_normalized
            )
            VALUES
                (1, 'A', NULL, NULL, NULL),
                (2, 'B', NULL, 'Partner', 'West')
            """
        )
        connection.execute(
            """
            INSERT INTO normalized_deals (
                deal_id,
                deal_name,
                amount_original,
                currency_original,
                created_at,
                closed_at,
                stage_id,
                category_id,
                status_group,
                analytical_contact_id,
                analytical_contact_name,
                contact_type_normalized,
                region_normalized
            )
            VALUES
                (1, 'Open Deal', 100.00, 'USD', TIMESTAMP '2026-01-01 10:00:00', NULL, 'OPEN', 0, NULL, 1, 'A', NULL, NULL),
                (2, 'Won Deal', 200.00, 'USD', TIMESTAMP '2026-02-01 10:00:00', TIMESTAMP '2026-03-01 10:00:00', 'WON', 0, 'won', 2, 'B', 'Partner', 'West')
            """
        )

        filters_response = get_filter_metadata(connection)

    assert filters_response.contact_types == ("Partner",)
    assert filters_response.regions == ("West",)
    assert filters_response.statuses == ("won",)
    assert filters_response.min_created_at is not None
    assert filters_response.max_created_at is not None
    assert filters_response.min_closed_at is not None
    assert filters_response.max_closed_at is not None


def test_dataset_status_reports_active_and_latest_without_sensitive_paths() -> None:
    run_response = run_local_synthetic_sync()
    status_response = dataset_status()

    assert status_response.active_dataset is not None
    assert status_response.latest_run is not None
    assert status_response.active_dataset.run_id == run_response.run_id
    assert status_response.latest_run.dataset_kind == "local_synthetic"
    assert status_response.latest_run.is_active is True
    assert status_response.latest_run.snapshot_paths
    assert all(
        not path.startswith("/") for path in status_response.latest_run.snapshot_paths
    )


def test_dataset_profile_reports_only_safe_aggregate_data() -> None:
    run_local_synthetic_sync()
    profile = dataset_profile()

    assert profile.active_dataset is not None
    assert profile.active_dataset.dataset_kind == "local_synthetic"
    assert profile.snapshot_count == 4
    assert all(table.exists for table in profile.expected_tables)
    assert profile.contact_type_raw_counts
    assert profile.contact_type_rules.raw_values_without_active_rule == (
        "synthetic-service",
    )
    assert profile.link_integrity.links_missing_contact_count == 0
    assert profile.link_integrity.links_missing_deal_count == 0

    response_text = repr(profile.model_dump()).lower()

    assert "snapshot_paths" not in response_text
    assert all(
        forbidden not in response_text for forbidden in FORBIDDEN_RESPONSE_PARTS
    )


def test_api_contacts_report_supports_filters_and_search() -> None:
    run_local_synthetic_sync()

    page = report_contacts(limit=5, offset=0)
    filtered_page = report_contacts(
        limit=10,
        offset=0,
        contact_type="Synthetic Partner B",
        region="Synthetic West",
        search="Contact 4",
    )
    status_page = report_contacts(limit=10, offset=0, status="open")

    assert page.total == 10
    assert len(page.items) == 5
    assert filtered_page.total == 1
    assert filtered_page.items[0].contact_id == 4
    assert filtered_page.items[0].total_deals_count >= 1
    assert status_page.total >= 1
    assert all(item.open_deals_count >= 1 for item in status_page.items)


def test_api_analytics_reports_return_local_typed_data() -> None:
    run_local_synthetic_sync()

    contacts = report_contact_analytics(limit=10, offset=0)
    open_contacts = report_contact_analytics(limit=10, offset=0, status="open")
    contact_by_id = report_contact_analytics(limit=10, offset=0, contact_id=4)
    created_range_contacts = report_contact_analytics(
        limit=10,
        offset=0,
        deal_created_from=date(2025, 1, 1),
        deal_created_to=date(2025, 12, 31),
    )
    sorted_contacts = report_contact_analytics(
        limit=1,
        offset=0,
        sort="revenue_usd",
        order="desc",
    )
    abc = report_abc()
    rfm = report_rfm()
    stale_deals = report_stale_deals()
    deal_cycle = report_deal_cycle()
    concentration = report_concentration()
    type_region = report_type_region()
    deals = report_deal_analytics(limit=10, offset=0)
    deal_by_id = report_deal_analytics(limit=10, offset=0, deal_id=4)
    open_deals = report_deal_analytics(limit=10, offset=0, status="open")
    filtered_deals = report_deal_analytics(
        limit=10,
        offset=0,
        status="open",
        contact_type="Synthetic Partner A",
        region="Synthetic East",
        deal_created_from=date(2025, 10, 1),
        deal_created_to=date(2025, 10, 1),
    )
    sorted_deals = report_deal_analytics(
        limit=3,
        offset=0,
        sort="budget_usd",
        order="desc",
    )
    client_search_deals = report_deal_analytics(
        limit=1,
        offset=0,
        client_search="contact 2",
        sort="budget_usd",
        order="desc",
    )
    client_id_deals = report_deal_analytics(
        limit=1,
        offset=0,
        client_id=2,
        client_search="does not match",
        status="won",
    )

    assert contacts.total == 10
    assert contacts.items[0].revenue_usd > 0
    assert contacts.items[0].budget_usd >= contacts.items[0].revenue_usd
    assert "budget_in_work_usd" in contacts.items[0].model_dump()
    assert "lost_budget_usd" in contacts.items[0].model_dump()
    assert open_contacts.total >= 1
    assert all(item.open_deals_count >= 1 for item in open_contacts.items)
    assert contact_by_id.total == 1
    assert contact_by_id.items[0].contact_id == 4
    assert created_range_contacts.total >= 1
    assert all(item.total_deals_count >= 1 for item in created_range_contacts.items)
    assert sorted_contacts.items[0].contact_id == 1
    assert len(abc) == 10
    assert any(row.abc_12m == "Нет продаж" for row in abc)
    assert len(rfm) == 10
    assert any(row.needs_reactivation for row in rfm)
    assert any(row.deal_id == 21 for row in stale_deals)
    assert deal_cycle.overall.deals_count == 25
    assert concentration.total_revenue_usd > 0
    assert type_region.type_rows
    assert type_region.region_rows
    assert deals.total == 30
    assert deals.items[0].deal_id == 1
    assert deals.items[0].estimated_profit_usd == deals.items[0].budget_usd * Decimal("0.50")
    assert deal_by_id.total == 1
    assert deal_by_id.items[0].deal_id == 4
    assert open_deals.total >= 1
    assert all(item.status_group == "open" for item in open_deals.items)
    assert all(item.estimated_profit_usd == 0 for item in open_deals.items)
    assert filtered_deals.total == 1
    assert filtered_deals.items[0].deal_id == 22
    assert sorted_deals.items[0].deal_id == 1
    assert client_search_deals.total == 4
    assert client_search_deals.filtered_budget_usd == Decimal("191454.55")
    assert client_search_deals.filtered_revenue_usd == Decimal("146454.55")
    assert client_search_deals.filtered_estimated_profit_usd == Decimal("73227.28")
    assert client_id_deals.total == 3
    assert client_id_deals.items[0].deal_id == 5
    assert client_id_deals.filtered_budget_usd == Decimal("146454.55")
    assert client_id_deals.filtered_revenue_usd == Decimal("146454.55")
    assert client_id_deals.filtered_estimated_profit_usd == Decimal("73227.28")


def test_reported_contact_analytics_query_handles_usd_deals_without_rate_rows() -> None:
    _load_api_usd_deal_without_rates_dataset()

    response = report_contact_analytics(
        limit=25,
        offset=0,
        sort="contact_id",
        order="desc",
    )

    assert response.total == 1
    assert response.items[0].contact_id == 1
    assert response.items[0].budget_usd == Decimal("100.00")
    assert response.items[0].estimated_profit_usd == Decimal("50.00")


def test_contact_analytics_returns_safe_503_when_non_usd_rates_are_missing() -> None:
    _load_api_non_usd_deal_without_rates_dataset()

    with pytest.raises(HTTPException) as exc_info:
        report_contact_analytics(
            limit=25,
            offset=0,
            sort="contact_id",
            order="desc",
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == (
        "Local currency rates are unavailable for the active dataset. "
        "Refresh local data and retry."
    )


def test_api_responses_do_not_expose_forbidden_fields() -> None:
    run_local_synthetic_sync()
    responses = [
        sync_status().model_dump(),
        dataset_status().model_dump(),
        dataset_profile().model_dump(),
        meta_filters().model_dump(),
        report_contacts(limit=10, offset=0).model_dump(),
        report_contact_analytics(limit=10, offset=0).model_dump(),
        report_deal_analytics(limit=10, offset=0).model_dump(),
        [row.model_dump() for row in report_abc()],
        [row.model_dump() for row in report_rfm()],
        [row.model_dump() for row in report_stale_deals()],
        report_deal_cycle().model_dump(),
        report_concentration().model_dump(),
        report_type_region().model_dump(),
    ]

    response_text = repr(responses).lower()

    assert all(
        forbidden not in response_text for forbidden in FORBIDDEN_RESPONSE_PARTS
    )


def _load_api_usd_deal_without_rates_dataset() -> None:
    _load_api_deal_without_rates_dataset(currency="USD")


def _load_api_non_usd_deal_without_rates_dataset() -> None:
    _load_api_deal_without_rates_dataset(currency="EUR")


def _load_api_deal_without_rates_dataset(*, currency: str) -> None:
    connection = get_connection()
    initialize_schema(connection)
    connection.execute(
        """
        INSERT INTO normalized_contacts (
            contact_id,
            contact_name,
            contact_type_raw,
            contact_type_normalized,
            region_normalized
        )
        VALUES (1, 'Rate Fixture Contact', NULL, 'Synthetic Type', 'Synthetic Region')
        """
    )
    connection.execute(
        """
        INSERT INTO normalized_deals (
            deal_id,
            deal_name,
            amount_original,
            currency_original,
            created_at,
            closed_at,
            stage_id,
            category_id,
            status_group,
            analytical_contact_id,
            analytical_contact_name,
            contact_type_normalized,
            region_normalized
        )
        VALUES (
            1,
            'Rate Fixture Deal',
            100.00,
            ?,
            TIMESTAMP '2025-01-01 10:00:00',
            TIMESTAMP '2025-01-02 10:00:00',
            'SYN:WON',
            1,
            'won',
            1,
            'Rate Fixture Contact',
            'Synthetic Type',
            'Synthetic Region'
        )
        """,
        [currency],
    )
