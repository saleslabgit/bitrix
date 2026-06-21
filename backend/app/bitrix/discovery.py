from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.bitrix.allowlist import build_contact_select, build_deal_select, is_forbidden_field
from app.bitrix.client import BitrixClient, BitrixClientError


@dataclass(frozen=True)
class BitrixDiscoveryResult:
    state: str
    message: str
    configured_contact_type_field: str | None
    contact_type_field_exists: bool | None
    contact_fields_count: int
    deal_fields_count: int
    allowed_contact_fields: tuple[str, ...]
    allowed_deal_fields: tuple[str, ...]
    candidate_contact_type_fields: tuple[str, ...]
    missing_required_contact_fields: tuple[str, ...]
    missing_required_deal_fields: tuple[str, ...]


def discover_bitrix_metadata(
    client: BitrixClient,
    *,
    contact_type_field: str | None,
) -> BitrixDiscoveryResult:
    try:
        contact_fields = client.get_contact_fields()
        deal_fields = client.get_deal_fields()
    except BitrixClientError as exc:
        return _error_result(str(exc), contact_type_field)

    allowed_contact_fields = build_contact_select(contact_type_field)
    allowed_deal_fields = build_deal_select()
    contact_type_exists = (
        contact_type_field in contact_fields if contact_type_field else None
    )
    missing_contact = _missing_fields(contact_fields, allowed_contact_fields)
    missing_deal = _missing_fields(deal_fields, allowed_deal_fields)
    state = "success" if not missing_contact and not missing_deal else "warning"

    return BitrixDiscoveryResult(
        state=state,
        message="Bitrix metadata discovery completed.",
        configured_contact_type_field=contact_type_field,
        contact_type_field_exists=contact_type_exists,
        contact_fields_count=len(contact_fields),
        deal_fields_count=len(deal_fields),
        allowed_contact_fields=allowed_contact_fields,
        allowed_deal_fields=allowed_deal_fields,
        candidate_contact_type_fields=_candidate_contact_type_fields(contact_fields),
        missing_required_contact_fields=missing_contact,
        missing_required_deal_fields=missing_deal,
    )


def _error_result(
    message: str,
    contact_type_field: str | None,
) -> BitrixDiscoveryResult:
    return BitrixDiscoveryResult(
        state="error",
        message=message,
        configured_contact_type_field=contact_type_field,
        contact_type_field_exists=None,
        contact_fields_count=0,
        deal_fields_count=0,
        allowed_contact_fields=build_contact_select(contact_type_field),
        allowed_deal_fields=build_deal_select(),
        candidate_contact_type_fields=(),
        missing_required_contact_fields=(),
        missing_required_deal_fields=(),
    )


def _missing_fields(
    metadata: dict[str, Any],
    required_fields: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(field for field in required_fields if field not in metadata)


def _candidate_contact_type_fields(metadata: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        sorted(
            field_name
            for field_name in metadata
            if field_name.startswith("UF_") and not is_forbidden_field(field_name)
        )
    )
