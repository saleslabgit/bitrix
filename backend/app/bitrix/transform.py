from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from app.domain import ContactSnapshot, DealCategorySnapshot, DealContactLink, DealSnapshot, StageSnapshot


def transform_contacts(
    rows: list[dict[str, Any]],
    *,
    contact_type_field: str | None,
) -> list[ContactSnapshot]:
    contacts: list[ContactSnapshot] = []
    for row in rows:
        contact_id = _required_int(row, "ID", "id")
        contacts.append(
            ContactSnapshot(
                contact_id=contact_id,
                contact_name=_contact_name(row, contact_id),
                contact_type_raw=_optional_str(row.get(contact_type_field))
                if contact_type_field
                else None,
            )
        )
    return contacts


def transform_deals(
    rows: list[dict[str, Any]],
    stages: list[StageSnapshot],
) -> list[DealSnapshot]:
    status_by_key = {(stage.stage_id, stage.category_id): stage.status_group for stage in stages}
    deals: list[DealSnapshot] = []
    for row in rows:
        deal_id = _required_int(row, "ID", "id")
        stage_id = _required_str(row, "STAGE_ID", "stageId")
        category_id = _optional_int(_first(row, "CATEGORY_ID", "categoryId"))
        if category_id is None:
            raise ValueError("Bitrix deal category is missing.")
        if (stage_id, category_id) not in status_by_key:
            raise ValueError("Bitrix deal stage cannot be resolved for its funnel.")
        deals.append(
            DealSnapshot(
                deal_id=deal_id,
                deal_name=_required_str(row, "TITLE", "title", fallback=f"Deal {deal_id}"),
                amount_original=_decimal(_first(row, "OPPORTUNITY", "opportunity")),
                currency_original=_required_str(row, "CURRENCY_ID", "currencyId"),
                created_at=_required_datetime(row, "DATE_CREATE", "createdTime"),
                closed_at=_optional_datetime(_first(row, "CLOSEDATE", "closedTime", "closedate")),
                stage_id=stage_id,
                category_id=category_id,
                status_group=status_by_key[(stage_id, category_id)],
                kev_held=parse_kev_held(
                    _first(
                        row,
                        "UF_CRM_1716895716",
                        "ufCrm_1716895716",
                        "ufCrm1716895716",
                        "uf_crm_1716895716",
                    )
                ),
            )
        )
    return deals


def transform_deal_contact_links(
    deal_id: int,
    rows: list[dict[str, Any]],
) -> list[DealContactLink]:
    links: list[DealContactLink] = []
    for row in rows:
        contact_id = _required_int(row, "CONTACT_ID", "contactId")
        links.append(
            DealContactLink(
                deal_id=_optional_int(_first(row, "DEAL_ID", "dealId")) or deal_id,
                contact_id=contact_id,
                is_primary=_bool(_first(row, "IS_PRIMARY", "isPrimary")),
                sort_order=_optional_int(_first(row, "SORT", "sort")),
                role_id=_optional_str(_first(row, "ROLE_ID", "roleId")),
            )
        )
    return links


def transform_deal_contact_links_from_deals(
    rows: list[dict[str, Any]],
) -> list[DealContactLink]:
    links_by_key: dict[tuple[int, int], DealContactLink] = {}
    for row in rows:
        deal_id = _required_int(row, "ID", "id")
        primary_contact_id = _optional_positive_int(_first(row, "CONTACT_ID", "contactId"))
        contact_ids = _contact_ids(_first(row, "CONTACT_IDS", "contactIds"))
        if primary_contact_id is not None:
            contact_ids.insert(0, primary_contact_id)

        for contact_id in contact_ids:
            key = (deal_id, contact_id)
            is_primary = contact_id == primary_contact_id
            existing = links_by_key.get(key)
            if existing is not None and existing.is_primary:
                continue
            links_by_key[key] = DealContactLink(
                deal_id=deal_id,
                contact_id=contact_id,
                is_primary=is_primary,
                sort_order=None,
                role_id=None,
            )
    return list(links_by_key.values())


def transform_deal_categories(rows: list[dict[str, Any]]) -> list[DealCategorySnapshot]:
    return [DealCategorySnapshot(category_id=_required_int(row, "ID", "id"), category_name=_required_str(row, "NAME", "name"), sort_order=_optional_int(_first(row, "SORT", "sort"))) for row in rows]


def transform_stages(rows: list[dict[str, Any]], *, category_id: int | None = None) -> list[StageSnapshot]:
    stages: list[StageSnapshot] = []
    for row in rows:
        stage_id = _required_str(row, "STATUS_ID", "statusId", "ID", "id")
        stages.append(
            StageSnapshot(
                stage_id=stage_id,
                category_id=category_id if category_id is not None else _optional_int(_first(row, "CATEGORY_ID", "categoryId")),
                status_group=_status_group(_first(row, "SEMANTICS", "semantics", "STATUS_SEMANTICS", "statusSemantics", "EXTRA")),
            )
        )
    return stages


def _contact_name(row: dict[str, Any], contact_id: int) -> str:
    full_name = _optional_str(_first(row, "FULL_NAME", "fullName"))
    if full_name:
        return full_name
    parts = [
        _optional_str(_first(row, "NAME", "name")),
        _optional_str(_first(row, "SECOND_NAME", "secondName")),
        _optional_str(_first(row, "LAST_NAME", "lastName")),
    ]
    name = " ".join(part for part in parts if part)
    return name or f"Contact {contact_id}"


def _status_group(value: Any) -> str:
    if isinstance(value, dict):
        value = _first(value, "SEMANTICS", "semantics")
    normalized = str(value or "").strip().lower()
    if normalized in {"s", "success", "won"}:
        return "won"
    if normalized in {"f", "failure", "lost", "apology"}:
        return "lost"
    return "open"


def parse_kev_held(value: Any) -> bool:
    if value is None or value is False:
        return False
    if value is True:
        return True
    if isinstance(value, (int, float, Decimal)):
        return value != 0

    normalized = str(value).strip().upper()
    if normalized in {"", "0", "N", "NO", "FALSE"}:
        return False
    if normalized in {"1", "Y", "YES", "TRUE"}:
        return True
    return False


def _required_int(row: dict[str, Any], *keys: str) -> int:
    value = _first(row, *keys)
    parsed = _optional_int(value)
    if parsed is None:
        raise ValueError(f"Required integer Bitrix field is missing: {keys[0]}.")
    return parsed


def _required_str(
    row: dict[str, Any],
    *keys: str,
    fallback: str | None = None,
) -> str:
    value = _optional_str(_first(row, *keys))
    if value:
        return value
    if fallback is not None:
        return fallback
    raise ValueError(f"Required text Bitrix field is missing: {keys[0]}.")


def _required_datetime(row: dict[str, Any], *keys: str) -> datetime:
    value = _optional_datetime(_first(row, *keys))
    if value is None:
        raise ValueError(f"Required datetime Bitrix field is missing: {keys[0]}.")
    return value


def _first(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row:
            return row[key]
    return None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _contact_ids(value: Any) -> list[int]:
    if value in (None, ""):
        return []

    contact_ids: list[int] = []
    for item in _contact_id_values(value):
        contact_id = _optional_positive_int(item)
        if contact_id is not None:
            contact_ids.append(contact_id)
    return contact_ids


def _contact_id_values(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    if isinstance(value, dict):
        for key in ("CONTACT_ID", "contactId", "ID", "id", "VALUE", "value"):
            if key in value:
                return [value[key]]
        values: list[Any] = []
        for item in value.values():
            values.extend(_contact_id_values(item))
        return values
    if isinstance(value, (list, tuple)):
        values: list[Any] = []
        for item in value:
            values.extend(_contact_id_values(item))
        return values
    if isinstance(value, str):
        return re.findall(r"\d+", value)
    return [value]


def _optional_positive_int(value: Any) -> int | None:
    parsed = _optional_int(value)
    if parsed is None or parsed <= 0:
        return None
    return parsed


def _decimal(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Bitrix amount field is invalid.") from exc


def _optional_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    return str(value or "").strip().upper() in {"Y", "YES", "TRUE", "1"}
