"""Pure backend domain models and logic."""

from app.domain.contact_selection import select_analytical_contact
from app.domain.contact_type_resolution import (
    MISSING_CONTACT_TYPE_RULE_RAW_VALUE,
    ResolvedContactType,
    parse_contact_type_option_ids,
    resolve_contact_type,
)
from app.domain.models import (
    ContactSnapshot,
    ContactTypeRule,
    CurrencyRateSnapshot,
    DealCategorySnapshot,
    DealContactLink,
    DealSnapshot,
    StageSnapshot,
)

__all__ = [
    "ContactSnapshot",
    "ContactTypeRule",
    "CurrencyRateSnapshot",
    "DealCategorySnapshot",
    "DealContactLink",
    "DealSnapshot",
    "MISSING_CONTACT_TYPE_RULE_RAW_VALUE",
    "ResolvedContactType",
    "StageSnapshot",
    "parse_contact_type_option_ids",
    "resolve_contact_type",
    "select_analytical_contact",
]
