from app.bitrix.client import BitrixClient
from app.bitrix.discovery import discover_bitrix_metadata


def test_discovery_reports_configured_contact_type_field_present() -> None:
    def transport(method: str, params: dict[str, object]) -> dict[str, object]:
        if method == "crm.contact.fields":
            return {
                "result": {
                    "ID": {},
                    "NAME": {},
                    "SECOND_NAME": {},
                    "LAST_NAME": {},
                    "PHONE": {},
                    "EMAIL": {},
                    "UF_CRM_CONTACT_TYPE": {},
                }
            }
        return {
            "result": {
                "ID": {},
                "TITLE": {},
                "OPPORTUNITY": {},
                "CURRENCY_ID": {},
                "DATE_CREATE": {},
                "CLOSEDATE": {},
                "STAGE_ID": {},
                "CATEGORY_ID": {},
                "CONTACT_ID": {},
                "CONTACT_IDS": {},
            }
        }

    client = BitrixClient("https://example/rest/1/secret/", transport=transport)

    result = discover_bitrix_metadata(
        client,
        contact_type_field="UF_CRM_CONTACT_TYPE",
    )

    assert result.state == "success"
    assert result.contact_type_field_exists is True
    assert result.candidate_contact_type_fields == ("UF_CRM_CONTACT_TYPE",)
    assert result.missing_required_contact_fields == ()
    assert result.missing_required_deal_fields == ()


def test_discovery_reports_missing_configured_contact_type_field() -> None:
    def transport(method: str, params: dict[str, object]) -> dict[str, object]:
        if method == "crm.contact.fields":
            return {
                "result": {
                    "ID": {},
                    "NAME": {},
                    "SECOND_NAME": {},
                    "LAST_NAME": {},
                    "UF_CRM_OTHER": {},
                }
            }
        return {"result": {"ID": {}, "TITLE": {}}}

    client = BitrixClient("https://example/rest/1/secret/", transport=transport)

    result = discover_bitrix_metadata(
        client,
        contact_type_field="UF_CRM_CONTACT_TYPE",
    )

    assert result.state == "warning"
    assert result.contact_type_field_exists is False
    assert "UF_CRM_CONTACT_TYPE" in result.missing_required_contact_fields
    assert "OPPORTUNITY" in result.missing_required_deal_fields
