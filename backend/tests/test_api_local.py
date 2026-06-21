from app.main import (
    meta_filters,
    report_contacts,
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


def test_api_responses_do_not_expose_forbidden_fields() -> None:
    run_local_synthetic_sync()
    responses = [
        sync_status().model_dump(),
        meta_filters().model_dump(),
        report_contacts(limit=10, offset=0).model_dump(),
    ]

    response_text = repr(responses).lower()

    assert all(
        forbidden not in response_text for forbidden in FORBIDDEN_RESPONSE_PARTS
    )
