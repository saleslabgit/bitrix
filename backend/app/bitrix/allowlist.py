CONTACT_BASE_SELECT = (
    "ID",
    "NAME",
    "SECOND_NAME",
    "LAST_NAME",
)

DEAL_SELECT = (
    "ID",
    "TITLE",
    "OPPORTUNITY",
    "CURRENCY_ID",
    "DATE_CREATE",
    "CLOSEDATE",
    "STAGE_ID",
    "CATEGORY_ID",
    "CONTACT_ID",
    "CONTACT_IDS",
)

LINK_ALLOWED_FIELDS = (
    "DEAL_ID",
    "CONTACT_ID",
    "IS_PRIMARY",
    "SORT",
    "ROLE_ID",
)

STAGE_ALLOWED_FIELDS = (
    "STATUS_ID",
    "NAME",
    "ENTITY_ID",
    "CATEGORY_ID",
    "SEMANTICS",
)

BITRIX_STAGE_ENTITY_ID = "DEAL_STAGE"

FORBIDDEN_FIELD_PARTS = (
    "PHONE",
    "EMAIL",
    "ADDRESS",
    "MESSENGER",
    "REQUISITE",
    "COMMENT",
    "COMMENTS",
    "FILE",
    "FILES",
    "ACTIVITY",
    "IM",
)


def build_contact_select(contact_type_field: str | None = None) -> tuple[str, ...]:
    fields = list(CONTACT_BASE_SELECT)
    if contact_type_field:
        _ensure_safe_configured_field(contact_type_field)
        fields.append(contact_type_field)
    return tuple(fields)


def build_deal_select() -> tuple[str, ...]:
    return DEAL_SELECT


def is_forbidden_field(field_name: str) -> bool:
    normalized = field_name.upper()
    return any(part in normalized for part in FORBIDDEN_FIELD_PARTS)


def _ensure_safe_configured_field(field_name: str) -> None:
    if is_forbidden_field(field_name):
        raise ValueError("Configured Bitrix contact type field is forbidden.")
