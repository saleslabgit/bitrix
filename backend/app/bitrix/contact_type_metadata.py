from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BitrixEnumOption:
    option_id: int
    label: str


def extract_contact_type_enum_options(
    contact_fields_metadata: dict[str, Any],
    *,
    contact_type_field: str,
) -> tuple[BitrixEnumOption, ...]:
    field_metadata = contact_fields_metadata.get(contact_type_field)
    if not isinstance(field_metadata, dict):
        return ()

    items = _enum_items(field_metadata)
    options: list[BitrixEnumOption] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        option_id = _option_id(item)
        label = _option_label(item)
        if option_id is None or label is None:
            continue
        options.append(BitrixEnumOption(option_id=option_id, label=label))

    return tuple(sorted(options, key=lambda option: option.option_id))


def _enum_items(field_metadata: dict[str, Any]) -> list[Any]:
    for key in ("items", "ITEMS", "list", "LIST", "enum", "ENUM"):
        value = field_metadata.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            return list(value.values())
    return []


def _option_id(item: dict[str, Any]) -> int | None:
    value = _first(item, "ID", "id", "VALUE_ID", "valueId")
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _option_label(item: dict[str, Any]) -> str | None:
    value = _first(item, "VALUE", "value", "NAME", "name", "TITLE", "title")
    if value is None:
        return None
    label = str(value).strip()
    return label or None


def _first(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in item:
            return item[key]
    return None
