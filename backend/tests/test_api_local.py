import pytest

from app import main
from app.local_database import reset_connection
from app.main import (
    dataset_status,
    dataset_profile,
    meta_filters,
    report_abc,
    report_concentration,
    report_contact_analytics,
    report_contacts,
    report_deal_cycle,
    report_rfm,
    report_stale_deals,
    report_type_region,
    run_local_synthetic_sync,
    sync_status,
)


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
    abc = report_abc()
    rfm = report_rfm()
    stale_deals = report_stale_deals()
    deal_cycle = report_deal_cycle()
    concentration = report_concentration()
    type_region = report_type_region()

    assert contacts.total == 10
    assert contacts.items[0].revenue_usd > 0
    assert open_contacts.total >= 1
    assert all(item.open_deals_count >= 1 for item in open_contacts.items)
    assert len(abc) == 10
    assert any(row.abc_12m == "Нет продаж" for row in abc)
    assert len(rfm) == 10
    assert any(row.needs_reactivation for row in rfm)
    assert any(row.deal_id == 21 for row in stale_deals)
    assert deal_cycle.overall.deals_count == 25
    assert concentration.total_revenue_usd > 0
    assert type_region.type_rows
    assert type_region.region_rows


def test_api_responses_do_not_expose_forbidden_fields() -> None:
    run_local_synthetic_sync()
    responses = [
        sync_status().model_dump(),
        dataset_status().model_dump(),
        dataset_profile().model_dump(),
        meta_filters().model_dump(),
        report_contacts(limit=10, offset=0).model_dump(),
        report_contact_analytics(limit=10, offset=0).model_dump(),
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
