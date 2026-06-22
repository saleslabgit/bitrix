import pytest

from app.bitrix.allowlist import build_contact_select, build_deal_select
from app.bitrix.client import BitrixApiError, BitrixClient, BitrixConfigurationError


FORBIDDEN_FIELD_PARTS = (
    "PHONE",
    "EMAIL",
    "ADDRESS",
    "MESSENGER",
    "REQUISITE",
    "COMMENT",
    "FILE",
    "ACTIVITY",
)


def test_bitrix_allowlists_exclude_forbidden_fields_by_default() -> None:
    contact_select = build_contact_select()
    deal_select = build_deal_select()
    all_fields = contact_select + deal_select

    assert "*" not in all_fields
    assert "UF_CRM_CONTACT_TYPE" not in contact_select
    assert "CONTACT_ID" in deal_select
    assert "CONTACT_IDS" in deal_select
    assert all(
        forbidden not in field
        for field in all_fields
        for forbidden in FORBIDDEN_FIELD_PARTS
    )


def test_contact_type_field_is_requested_only_when_configured() -> None:
    assert build_contact_select("UF_CRM_CONTACT_TYPE") == (
        "ID",
        "NAME",
        "SECOND_NAME",
        "LAST_NAME",
        "UF_CRM_CONTACT_TYPE",
    )


def test_forbidden_configured_contact_type_field_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_contact_select("UF_CRM_PHONE_TYPE")


def test_client_uses_read_only_list_method_with_pagination() -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def transport(method: str, params: dict[str, object]) -> dict[str, object]:
        calls.append((method, params))
        if params["start"] == 0:
            return {"result": [{"ID": "1"}], "next": 1}
        return {"result": [{"ID": "2"}]}

    client = BitrixClient(
        "https://example.bitrix24.com/rest/1/secret-token/",
        page_size=1,
        transport=transport,
    )

    rows = client.list_contacts("UF_CRM_CONTACT_TYPE")

    assert rows == [{"ID": "1"}, {"ID": "2"}]
    assert [call[0] for call in calls] == ["crm.contact.list", "crm.contact.list"]
    assert calls[0][1]["select"] == [
        "ID",
        "NAME",
        "SECOND_NAME",
        "LAST_NAME",
        "UF_CRM_CONTACT_TYPE",
    ]
    assert calls[0][1]["limit"] == 1
    assert calls[1][1]["start"] == 1


def test_client_lists_deals_for_one_contact_with_safe_select() -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def transport(method: str, params: dict[str, object]) -> dict[str, object]:
        calls.append((method, params))
        return {"result": [{"ID": "100"}]}

    client = BitrixClient(
        "https://example.bitrix24.com/rest/1/secret-token/",
        transport=transport,
    )

    rows = client.list_deals_for_contact(661)

    assert rows == [{"ID": "100"}]
    assert calls == [
        (
            "crm.deal.list",
            {
                "filter": {"CONTACT_ID": 661},
                "select": list(build_deal_select()),
                "order": {"ID": "ASC"},
                "start": 0,
                "limit": 50,
            },
        )
    ]


def test_client_lists_deals_by_explicit_ids_with_safe_select() -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def transport(method: str, params: dict[str, object]) -> dict[str, object]:
        calls.append((method, params))
        return {"result": [{"ID": "100"}, {"ID": "200"}]}

    client = BitrixClient(
        "https://example.bitrix24.com/rest/1/secret-token/",
        transport=transport,
    )

    rows = client.list_deals_by_ids((200, 100, 100))

    assert rows == [{"ID": "100"}, {"ID": "200"}]
    assert calls == [
        (
            "crm.deal.list",
            {
                "filter": {"@ID": [100, 200]},
                "select": list(build_deal_select()),
                "order": {"ID": "ASC"},
                "start": 0,
                "limit": 50,
            },
        )
    ]


def test_client_accepts_plain_contact_ids_from_deal_contact_links() -> None:
    client = BitrixClient(
        "https://example.bitrix24.com/rest/1/secret-token/",
        transport=lambda method, params: {"result": [661, "900"]},
    )

    links = client.get_deal_contact_links(123)

    assert links == [{"CONTACT_ID": 661}, {"CONTACT_ID": "900"}]


def test_client_rejects_write_methods() -> None:
    client = BitrixClient(
        "https://example.bitrix24.com/rest/1/secret-token/",
        transport=lambda method, params: {"result": {}},
    )

    with pytest.raises(BitrixConfigurationError):
        client._call_full("crm.deal.update", {"id": 1})


def test_client_errors_do_not_expose_webhook_secret() -> None:
    client = BitrixClient(
        "https://example.bitrix24.com/rest/1/secret-token/",
        transport=lambda method, params: {
            "error": "INVALID_CREDENTIALS",
            "error_description": "secret-token",
        },
    )

    with pytest.raises(BitrixApiError) as error:
        client.get_contact_fields()

    assert "secret-token" not in str(error.value)
    assert "INVALID_CREDENTIALS" in str(error.value)


def test_client_requires_credentials_without_live_call() -> None:
    with pytest.raises(BitrixConfigurationError):
        BitrixClient(None)
