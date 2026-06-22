from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Iterable

from app.domain.models import ContactTypeRule


MISSING_CONTACT_TYPE_RULE_RAW_VALUE = "__MISSING__"


@dataclass(frozen=True)
class ResolvedContactType:
    normalized_type: str
    region: str
    priority: int
    source_raw_value: str


def resolve_contact_type(
    contact_type_raw: str | None,
    type_rules: Iterable[ContactTypeRule],
) -> ResolvedContactType | None:
    active_rules = {
        rule.raw_value: rule for rule in type_rules if rule.is_active
    }

    if _is_missing_raw_value(contact_type_raw):
        return _resolved(active_rules.get(MISSING_CONTACT_TYPE_RULE_RAW_VALUE))

    raw_value = str(contact_type_raw).strip()
    option_ids = parse_contact_type_option_ids(raw_value)
    if option_ids:
        candidates = [
            (rule.priority, option_id, rule)
            for option_id in option_ids
            for rule in (active_rules.get(str(option_id)),)
            if rule is not None
        ]
        if not candidates:
            return None
        return _resolved(min(candidates, key=lambda row: (row[0], row[1]))[2])

    return _resolved(active_rules.get(raw_value))


def parse_contact_type_option_ids(raw_value: str | None) -> tuple[int, ...]:
    if _is_missing_raw_value(raw_value):
        return ()

    try:
        parsed = ast.literal_eval(str(raw_value).strip())
    except (SyntaxError, ValueError):
        return ()

    if isinstance(parsed, int):
        values = [parsed]
    elif isinstance(parsed, (list, tuple)):
        values = parsed
    else:
        return ()

    option_ids: list[int] = []
    for value in values:
        try:
            option_id = int(value)
        except (TypeError, ValueError):
            continue
        if option_id > 0 and option_id not in option_ids:
            option_ids.append(option_id)
    return tuple(option_ids)


def _is_missing_raw_value(value: str | None) -> bool:
    if value is None:
        return True
    normalized = str(value).strip()
    return normalized == "" or normalized.lower() == "false" or normalized == "[]"


def _resolved(rule: ContactTypeRule | None) -> ResolvedContactType | None:
    if rule is None:
        return None
    return ResolvedContactType(
        normalized_type=rule.normalized_type,
        region=rule.region,
        priority=rule.priority,
        source_raw_value=rule.raw_value,
    )
