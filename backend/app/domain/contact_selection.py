from collections.abc import Mapping, Sequence

from app.domain.models import ContactSnapshot, ContactTypeRule, DealContactLink


def select_analytical_contact(
    links: Sequence[DealContactLink],
    contacts_by_id: Mapping[int, ContactSnapshot],
    type_rules: Sequence[ContactTypeRule],
) -> int | None:
    if not links:
        return None

    active_priorities = {
        rule.raw_value: rule.priority for rule in type_rules if rule.is_active
    }
    fallback_priority = (
        max(active_priorities.values()) + 1 if active_priorities else 0
    )

    candidates: list[tuple[int, bool, int]] = []
    for link in links:
        contact = contacts_by_id.get(link.contact_id)
        if contact is None:
            continue

        priority = active_priorities.get(
            contact.contact_type_raw,
            fallback_priority,
        )
        candidates.append((priority, not link.is_primary, contact.contact_id))

    if not candidates:
        return None

    return min(candidates)[2]
