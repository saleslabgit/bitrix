from collections.abc import Mapping, Sequence

from app.domain.models import ContactSnapshot, ContactTypeRule, DealContactLink
from app.domain.contact_type_resolution import resolve_contact_type


def select_analytical_contact(
    links: Sequence[DealContactLink],
    contacts_by_id: Mapping[int, ContactSnapshot],
    type_rules: Sequence[ContactTypeRule],
) -> int | None:
    if not links:
        return None

    candidates: list[tuple[int, bool, int]] = []
    for link in links:
        contact = contacts_by_id.get(link.contact_id)
        if contact is None:
            continue

        resolved_type = resolve_contact_type(contact.contact_type_raw, type_rules)
        if resolved_type is None:
            continue
        candidates.append(
            (resolved_type.priority, not link.is_primary, contact.contact_id)
        )

    if not candidates:
        return None

    return min(candidates)[2]
