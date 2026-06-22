from app.domain import (
    ContactSnapshot,
    ContactTypeRule,
    DealContactLink,
    MISSING_CONTACT_TYPE_RULE_RAW_VALUE,
)
from app.domain.contact_selection import select_analytical_contact


def contact(contact_id: int, contact_type_raw: str | None) -> ContactSnapshot:
    return ContactSnapshot(
        contact_id=contact_id,
        contact_name=f"Contact {contact_id}",
        contact_type_raw=contact_type_raw,
    )


def link(contact_id: int, is_primary: bool = False) -> DealContactLink:
    return DealContactLink(
        deal_id=100,
        contact_id=contact_id,
        is_primary=is_primary,
    )


def rule(raw_value: str, priority: int) -> ContactTypeRule:
    return ContactTypeRule(
        raw_value=raw_value,
        normalized_type=f"Type {raw_value}",
        priority=priority,
        region=f"Region {raw_value}",
    )


def test_best_type_priority_wins() -> None:
    contacts = {
        1: contact(1, "type-low"),
        2: contact(2, "type-high"),
    }
    rules = [rule("type-low", 20), rule("type-high", 10)]

    selected = select_analytical_contact(
        links=[link(1, is_primary=True), link(2)],
        contacts_by_id=contacts,
        type_rules=rules,
    )

    assert selected == 2


def test_primary_flag_breaks_equal_priority_ties() -> None:
    contacts = {
        1: contact(1, "type-a"),
        2: contact(2, "type-b"),
    }
    rules = [rule("type-a", 10), rule("type-b", 10)]

    selected = select_analytical_contact(
        links=[link(1), link(2, is_primary=True)],
        contacts_by_id=contacts,
        type_rules=rules,
    )

    assert selected == 2


def test_minimum_contact_id_breaks_remaining_ties() -> None:
    contacts = {
        1: contact(1, "type-a"),
        2: contact(2, "type-b"),
    }
    rules = [rule("type-a", 10), rule("type-b", 10)]

    selected = select_analytical_contact(
        links=[link(2), link(1)],
        contacts_by_id=contacts,
        type_rules=rules,
    )

    assert selected == 1


def test_deal_without_contacts_returns_none() -> None:
    selected = select_analytical_contact(
        links=[],
        contacts_by_id={},
        type_rules=[],
    )

    assert selected is None


def test_unknown_or_inactive_contact_type_is_not_selected() -> None:
    contacts = {
        1: contact(1, None),
        2: contact(2, "unknown"),
    }

    selected = select_analytical_contact(
        links=[link(2), link(1, is_primary=True)],
        contacts_by_id=contacts,
        type_rules=[],
    )

    assert selected is None


def test_missing_contact_type_rule_can_select_missing_contact() -> None:
    contacts = {
        1: contact(1, None),
        2: contact(2, "[67]"),
    }

    selected = select_analytical_contact(
        links=[link(2, is_primary=True), link(1)],
        contacts_by_id=contacts,
        type_rules=[
            ContactTypeRule(
                raw_value=MISSING_CONTACT_TYPE_RULE_RAW_VALUE,
                normalized_type="Конечный клиент",
                priority=4,
                region="Без региона",
            ),
            ContactTypeRule(
                raw_value="67",
                normalized_type="Поставщик",
                priority=99,
                region="Без региона",
                is_active=False,
            ),
        ],
    )

    assert selected == 1
