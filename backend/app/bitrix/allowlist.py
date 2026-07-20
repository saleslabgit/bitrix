CONTACT_BASE_SELECT = (
    "ID",
    "NAME",
    "SECOND_NAME",
    "LAST_NAME",
)

KEV_DEAL_FIELD = "UF_CRM_1716895716"

DEAL_SELECT = (
    "ID",
    "TITLE",
    "OPPORTUNITY",
    "CURRENCY_ID",
    "DATE_CREATE",
    "CLOSEDATE",
    "MOVED_TIME",
    "STAGE_ID",
    "CATEGORY_ID",
    "CONTACT_ID",
    "CONTACT_IDS",
    KEV_DEAL_FIELD,
)

DEAL_ITEM_FIELD_CANDIDATES = {
    "id": ("id", "ID"),
    "title": ("title", "TITLE"),
    "opportunity": ("opportunity", "OPPORTUNITY"),
    "currency": ("currencyId", "currency_id", "CURRENCY_ID"),
    "created_time": ("createdTime", "created_at", "DATE_CREATE"),
    "closed_time": ("closedTime", "closedate", "closed_at", "CLOSEDATE"),
    "moved_time": ("movedTime", "moved_time", "MOVED_TIME"),
    "stage": ("stageId", "stage_id", "STAGE_ID"),
    "category": ("categoryId", "category_id", "CATEGORY_ID"),
    "primary_contact": ("contactId", "contact_id", "CONTACT_ID"),
    "contact_list": ("contactIds", "contact_ids", "CONTACT_IDS"),
    "kev_held": (
        "ufCrm_1716895716",
        "ufCrm1716895716",
        "UF_CRM_1716895716",
        "uf_crm_1716895716",
    ),
}

LINK_ALLOWED_FIELDS = (
    "DEAL_ID",
    "CONTACT_ID",
    "IS_PRIMARY",
    "SORT",
    "ROLE_ID",
)

STAGE_HISTORY_SELECT = (
    "ID",
    "TYPE_ID",
    "OWNER_ID",
    "CREATED_TIME",
    "CATEGORY_ID",
    "STAGE_ID",
    "STAGE_SEMANTIC_ID",
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
)

FORBIDDEN_FIELD_EXACT = {"*", "FM", "IM"}


def build_contact_select(contact_type_field: str | None = None) -> tuple[str, ...]:
    fields = list(CONTACT_BASE_SELECT)
    if contact_type_field:
        _ensure_safe_configured_field(contact_type_field)
        fields.append(contact_type_field)
    return tuple(fields)


def build_deal_select() -> tuple[str, ...]:
    return DEAL_SELECT


def build_deal_item_select(item_fields: dict[str, object]) -> tuple[str, ...]:
    available_fields = set(item_fields)
    selected: list[str] = []
    for candidates in DEAL_ITEM_FIELD_CANDIDATES.values():
        field_name = _first_safe_available_field(candidates, available_fields)
        if field_name is not None:
            selected.append(field_name)
    return tuple(dict.fromkeys(selected))


def is_forbidden_field(field_name: str) -> bool:
    normalized = field_name.upper()
    return normalized in FORBIDDEN_FIELD_EXACT or any(
        part in normalized for part in FORBIDDEN_FIELD_PARTS
    )


def _first_safe_available_field(
    candidates: tuple[str, ...],
    available_fields: set[str],
) -> str | None:
    for field_name in candidates:
        if field_name in available_fields and not is_forbidden_field(field_name):
            return field_name
    return None


def _ensure_safe_configured_field(field_name: str) -> None:
    if is_forbidden_field(field_name):
        raise ValueError("Configured Bitrix contact type field is forbidden.")
