from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

import duckdb

from app.bitrix.client import BitrixClient, BitrixClientError
from app.bitrix.allowlist import build_deal_item_select
from app.bitrix.transform import (
    apply_actual_close_times,
    transform_deal_contact_links,
    transform_deal_contact_links_from_deals,
    transform_deal_stage_history,
    transform_deals,
)
from app.domain import ContactSnapshot, ContactTypeRule, DealContactLink, DealSnapshot, DealStageHistorySnapshot, StageSnapshot
from app.domain.contact_type_resolution import resolve_contact_type
from app.pipeline.normalization import normalize_local_data
from app.storage.snapshots import build_run_id
from app.storage.status import DatasetRunStatus, count_current_rows, store_dataset_run


MAX_EXPLICIT_DEAL_IDS = 20
EXPLICIT_RECONCILIATION_DATASET_NAME = "bitrix-explicit-reconciliation"
EXPLICIT_RECONCILIATION_DATASET_KIND = "bitrix_explicit_reconciliation"


@dataclass(frozen=True)
class LocalLinkedDealDiagnostic:
    deal_id: int
    raw_deal_exists: bool
    status_group: str | None
    is_primary: bool
    analytical_contact_id: int | None
    analytical_contact_name: str | None
    analytical_contact_type: str | None


@dataclass(frozen=True)
class ContactDealDiagnostic:
    contact_id: int
    contact_name: str | None
    contact_type_raw: str | None
    contact_type_normalized: str | None
    region_normalized: str | None
    priority: int | None
    local_linked_deals_count: int
    local_linked_deal_ids: tuple[int, ...]
    local_analytical_deals_count: int
    local_analytical_deal_ids: tuple[int, ...]
    linked_deals: tuple[LocalLinkedDealDiagnostic, ...]
    explanation: str


@dataclass(frozen=True)
class ExplicitDealLocalDiagnostic:
    deal_id: int
    raw_deal_exists: bool
    has_contact_link: bool
    linked_contact_ids: tuple[int, ...]
    analytical_contact_id: int | None
    analytical_contact_name: str | None
    analytical_contact_type: str | None
    counts_for_contact: bool
    divergence_reason: str


@dataclass(frozen=True)
class ExplicitContactDealDiagnostic:
    contact_id: int
    supplied_deal_ids: tuple[int, ...]
    deals: tuple[ExplicitDealLocalDiagnostic, ...]


@dataclass(frozen=True)
class BitrixExplicitDealRelation:
    deal_id: int
    bitrix_deal_exists: bool
    linked_contact_ids: tuple[int, ...]
    has_contact_link: bool
    is_primary: bool
    sort_order: int | None
    role_id: str | None
    divergence_reason: str


@dataclass(frozen=True)
class BitrixExplicitDealVerification:
    contact_id: int
    supplied_deal_ids: tuple[int, ...]
    bitrix_deal_ids: tuple[int, ...]
    relations: tuple[BitrixExplicitDealRelation, ...]
    confirmed_contact_deal_ids: tuple[int, ...]
    methods_used: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class ExplicitContactDealReconciliation:
    contact_id: int
    supplied_deal_ids: tuple[int, ...]
    confirmed_contact_deal_ids: tuple[int, ...]
    inserted_raw_deal_ids: tuple[int, ...]
    inserted_link_deal_ids: tuple[int, ...]
    skipped_deal_ids: tuple[int, ...]
    status: DatasetRunStatus
    local_after: ExplicitContactDealDiagnostic
    methods_used: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class BitrixItemDealContactRow:
    deal_id: int
    returned_contact_ids: tuple[int, ...]
    has_contact_link: bool


@dataclass(frozen=True)
class BitrixItemDealContactVerification:
    contact_id: int
    supplied_deal_ids: tuple[int, ...]
    selected_fields: tuple[str, ...]
    contact_related_fields: tuple[str, ...]
    returned_deal_ids: tuple[int, ...]
    rows: tuple[BitrixItemDealContactRow, ...]
    methods_used: tuple[str, ...]
    is_complete_for_contact: bool
    explanation: str


@dataclass(frozen=True)
class _BitrixExplicitDealFacts:
    verification: BitrixExplicitDealVerification
    deal_rows_by_id: dict[int, dict[str, object]]
    contact_links_by_deal_id: dict[int, DealContactLink]


def get_contact_deal_diagnostic(
    connection: duckdb.DuckDBPyConnection,
    contact_id: int,
) -> ContactDealDiagnostic:
    contact = _load_contact(connection, contact_id)
    priority: int | None = None
    if contact is not None:
        resolved_type = resolve_contact_type(contact.contact_type_raw, _load_type_rules(connection))
        if resolved_type is not None:
            priority = resolved_type.priority

    normalized_contact = connection.execute(
        """
        SELECT contact_type_normalized, region_normalized
        FROM normalized_contacts
        WHERE contact_id = ?
        """,
        [contact_id],
    ).fetchone()
    linked_deals = tuple(_load_linked_deals(connection, contact_id))
    analytical_deal_ids = tuple(
        row[0]
        for row in connection.execute(
            """
            SELECT deal_id
            FROM normalized_deals
            WHERE analytical_contact_id = ?
            ORDER BY deal_id
            """,
            [contact_id],
        ).fetchall()
    )
    linked_deal_ids = tuple(deal.deal_id for deal in linked_deals)

    return ContactDealDiagnostic(
        contact_id=contact_id,
        contact_name=contact.contact_name if contact is not None else None,
        contact_type_raw=contact.contact_type_raw if contact is not None else None,
        contact_type_normalized=normalized_contact[0] if normalized_contact else None,
        region_normalized=normalized_contact[1] if normalized_contact else None,
        priority=priority,
        local_linked_deals_count=len(linked_deal_ids),
        local_linked_deal_ids=linked_deal_ids,
        local_analytical_deals_count=len(analytical_deal_ids),
        local_analytical_deal_ids=analytical_deal_ids,
        linked_deals=linked_deals,
        explanation=_local_explanation(
            contact_exists=contact is not None,
            linked_deal_ids=linked_deal_ids,
            analytical_deal_ids=analytical_deal_ids,
        ),
    )


def get_explicit_contact_deal_diagnostic(
    connection: duckdb.DuckDBPyConnection,
    *,
    contact_id: int,
    deal_ids: tuple[int, ...],
) -> ExplicitContactDealDiagnostic:
    supplied_ids = _normalize_deal_ids(deal_ids)
    raw_deal_ids = _raw_deal_ids(connection, supplied_ids)
    linked_contact_ids_by_deal_id = _linked_contact_ids_by_deal_id(connection, supplied_ids)
    normalized_deals_by_id = _normalized_deals_by_id(connection, supplied_ids)

    rows = []
    for deal_id in supplied_ids:
        linked_contact_ids = linked_contact_ids_by_deal_id.get(deal_id, ())
        normalized_deal = normalized_deals_by_id.get(deal_id)
        analytical_contact_id = normalized_deal[0] if normalized_deal else None
        rows.append(
            ExplicitDealLocalDiagnostic(
                deal_id=deal_id,
                raw_deal_exists=deal_id in raw_deal_ids,
                has_contact_link=contact_id in linked_contact_ids,
                linked_contact_ids=linked_contact_ids,
                analytical_contact_id=analytical_contact_id,
                analytical_contact_name=normalized_deal[1] if normalized_deal else None,
                analytical_contact_type=normalized_deal[2] if normalized_deal else None,
                counts_for_contact=analytical_contact_id == contact_id,
                divergence_reason=_explicit_local_reason(
                    raw_deal_exists=deal_id in raw_deal_ids,
                    has_contact_link=contact_id in linked_contact_ids,
                    linked_contact_ids=linked_contact_ids,
                    analytical_contact_id=analytical_contact_id,
                    contact_id=contact_id,
                ),
            )
        )
    return ExplicitContactDealDiagnostic(
        contact_id=contact_id,
        supplied_deal_ids=supplied_ids,
        deals=tuple(rows),
    )


def verify_bitrix_contact_deals(
    connection: duckdb.DuckDBPyConnection,
    *,
    client: BitrixClient,
    contact_id: int,
) -> BitrixExplicitDealVerification:
    local = get_contact_deal_diagnostic(connection, contact_id)
    facts = _collect_bitrix_explicit_deal_facts(
        client=client,
        contact_id=contact_id,
        deal_ids=local.local_linked_deal_ids,
    )
    return facts.verification


def verify_explicit_bitrix_contact_deals(
    *,
    client: BitrixClient,
    contact_id: int,
    deal_ids: tuple[int, ...],
) -> BitrixExplicitDealVerification:
    return _collect_bitrix_explicit_deal_facts(
        client=client,
        contact_id=contact_id,
        deal_ids=deal_ids,
    ).verification


def reconcile_explicit_contact_deals(
    connection: duckdb.DuckDBPyConnection,
    *,
    client: BitrixClient,
    contact_id: int,
    deal_ids: tuple[int, ...],
) -> ExplicitContactDealReconciliation:
    supplied_ids = _normalize_deal_ids(deal_ids)
    started_at = datetime.now(timezone.utc)
    facts = _collect_bitrix_explicit_deal_facts(
        client=client,
        contact_id=contact_id,
        deal_ids=supplied_ids,
    )
    confirmed_ids = facts.verification.confirmed_contact_deal_ids
    local_before = get_explicit_contact_deal_diagnostic(
        connection,
        contact_id=contact_id,
        deal_ids=supplied_ids,
    )
    local_before_by_id = {deal.deal_id: deal for deal in local_before.deals}
    raw_deal_ids = _raw_deal_ids(connection, supplied_ids)
    candidate_ids = tuple(
        deal_id for deal_id in confirmed_ids if deal_id in facts.deal_rows_by_id
    )
    transformed_by_id = {
        deal.deal_id: deal
        for deal in transform_deals(
            [facts.deal_rows_by_id[deal_id] for deal_id in candidate_ids],
            _load_stages(connection),
        )
    }
    closed_ids_to_resolve = tuple(
        deal_id
        for deal_id in candidate_ids
        if transformed_by_id[deal_id].status_group in {"won", "lost"}
    )
    history: list[DealStageHistorySnapshot] = []
    resolved_deals: list[DealSnapshot] = []
    resolution_error: ValueError | BitrixClientError | None = None
    try:
        if closed_ids_to_resolve:
            history = transform_deal_stage_history(
                client.list_deal_stage_history(closed_ids_to_resolve)
            )
            closed_id_set = set(closed_ids_to_resolve)
            history = [row for row in history if row.deal_id in closed_id_set]
        resolved_deals = apply_actual_close_times(
            [transformed_by_id[deal_id] for deal_id in candidate_ids],
            [facts.deal_rows_by_id[deal_id] for deal_id in candidate_ids],
            history,
        )
    except (ValueError, BitrixClientError) as exc:
        resolution_error = exc
    local_deal_state = _raw_deal_state(connection, candidate_ids)
    deals_to_write = [
        deal
        for deal in resolved_deals
        if _deal_requires_reconciliation(deal, local_deal_state.get(deal.deal_id))
    ]
    deal_rows_to_insert = tuple(
        deal.deal_id for deal in deals_to_write if deal.deal_id not in raw_deal_ids
    )
    link_rows_to_insert = tuple(
        deal_id
        for deal_id in confirmed_ids
        if deal_id in raw_deal_ids.union(deal_rows_to_insert)
        and not local_before_by_id[deal_id].has_contact_link
    )
    skipped_ids = tuple(
        deal_id
        for deal_id in confirmed_ids
        if deal_id not in raw_deal_ids and deal_id not in facts.deal_rows_by_id
    )

    status: DatasetRunStatus
    inserted_raw_deal_ids: tuple[int, ...] = ()
    inserted_link_deal_ids: tuple[int, ...] = ()
    if not confirmed_ids:
        status = _store_reconciliation_status(
            connection,
            state="error",
            message="No supplied deals were confirmed as linked to the contact by Bitrix.",
            started_at=started_at,
            is_active=False,
        )
    elif skipped_ids:
        status = _store_reconciliation_status(
            connection,
            state="error",
            message="Explicit reconciliation failed: confirmed deal facts are incomplete.",
            started_at=started_at,
            is_active=False,
        )
    elif resolution_error is not None:
        status = _store_reconciliation_status(
            connection,
            state="error",
            message="Explicit reconciliation failed: factual close data is unavailable.",
            started_at=started_at,
            is_active=False,
        )
    else:
        connection.execute("BEGIN TRANSACTION")
        try:
            _upsert_raw_deals(connection, deals_to_write)
            _upsert_raw_stage_history(connection, history)
            _insert_raw_links(
                connection,
                [
                    facts.contact_links_by_deal_id[deal_id]
                    for deal_id in link_rows_to_insert
                ],
            )
            normalize_local_data(connection)
            status = _build_reconciliation_status(
                connection,
                state="success",
                message=(
                    "Explicit contact-deal reconciliation completed: "
                    f"{len(link_rows_to_insert)} links inserted."
                ),
                started_at=started_at,
                is_active=True,
            )
            store_dataset_run(connection, status)
            connection.execute("COMMIT")
            inserted_raw_deal_ids = deal_rows_to_insert
            inserted_link_deal_ids = link_rows_to_insert
        except Exception:
            connection.execute("ROLLBACK")
            status = _store_reconciliation_status(
                connection,
                state="error",
                message="Explicit reconciliation failed before activation.",
                started_at=started_at,
                is_active=False,
            )

    local_after = get_explicit_contact_deal_diagnostic(
        connection,
        contact_id=contact_id,
        deal_ids=supplied_ids,
    )
    return ExplicitContactDealReconciliation(
        contact_id=contact_id,
        supplied_deal_ids=supplied_ids,
        confirmed_contact_deal_ids=confirmed_ids,
        inserted_raw_deal_ids=inserted_raw_deal_ids,
        inserted_link_deal_ids=inserted_link_deal_ids,
        skipped_deal_ids=skipped_ids,
        status=status,
        local_after=local_after,
        methods_used=(
            (*facts.verification.methods_used, "crm.stagehistory.list")
            if closed_ids_to_resolve
            else facts.verification.methods_used
        ),
        explanation=_reconciliation_explanation(
            confirmed_ids=confirmed_ids,
            inserted_link_ids=inserted_link_deal_ids,
            skipped_ids=skipped_ids,
        ),
    )


def verify_bitrix_item_list_contact_links(
    *,
    client: BitrixClient,
    contact_id: int,
    deal_ids: tuple[int, ...],
) -> BitrixItemDealContactVerification:
    supplied_ids = _normalize_deal_ids(deal_ids)
    item_fields = client.get_deal_item_fields()
    selected_fields = build_deal_item_select(item_fields)
    item_rows = client.list_deal_items_with_select(
        selected_fields,
        filter_={"@id": list(supplied_ids)},
    )
    returned_deal_ids = tuple(sorted({_row_deal_id(row) for row in item_rows}))
    links = transform_deal_contact_links_from_deals(item_rows)
    contact_ids_by_deal_id: dict[int, list[int]] = {}
    for link in links:
        contact_ids_by_deal_id.setdefault(link.deal_id, []).append(link.contact_id)
    rows = tuple(
        BitrixItemDealContactRow(
            deal_id=deal_id,
            returned_contact_ids=tuple(sorted(contact_ids_by_deal_id.get(deal_id, ()))),
            has_contact_link=contact_id in contact_ids_by_deal_id.get(deal_id, ()),
        )
        for deal_id in supplied_ids
    )
    is_complete = set(returned_deal_ids) == set(supplied_ids) and all(
        row.has_contact_link for row in rows
    )
    return BitrixItemDealContactVerification(
        contact_id=contact_id,
        supplied_deal_ids=supplied_ids,
        selected_fields=selected_fields,
        contact_related_fields=tuple(
            field for field in selected_fields if "contact" in field.lower()
        ),
        returned_deal_ids=returned_deal_ids,
        rows=rows,
        methods_used=("crm.item.fields", "crm.item.list"),
        is_complete_for_contact=is_complete,
        explanation=_bitrix_item_list_explanation(is_complete),
    )


def _collect_bitrix_explicit_deal_facts(
    *,
    client: BitrixClient,
    contact_id: int,
    deal_ids: tuple[int, ...],
) -> _BitrixExplicitDealFacts:
    supplied_ids = _normalize_deal_ids(deal_ids)
    deal_rows = client.list_deals_by_ids(supplied_ids)
    deal_rows_by_id = {_row_deal_id(row): row for row in deal_rows}
    relations: list[BitrixExplicitDealRelation] = []
    contact_links_by_deal_id: dict[int, DealContactLink] = {}

    for deal_id in supplied_ids:
        links = transform_deal_contact_links(
            deal_id,
            client.get_deal_contact_links(deal_id),
        )
        linked_contact_ids = tuple(sorted({link.contact_id for link in links}))
        contact_link = next((link for link in links if link.contact_id == contact_id), None)
        if contact_link is not None:
            contact_links_by_deal_id[deal_id] = contact_link
        relations.append(
            BitrixExplicitDealRelation(
                deal_id=deal_id,
                bitrix_deal_exists=deal_id in deal_rows_by_id,
                linked_contact_ids=linked_contact_ids,
                has_contact_link=contact_link is not None,
                is_primary=contact_link.is_primary if contact_link else False,
                sort_order=contact_link.sort_order if contact_link else None,
                role_id=contact_link.role_id if contact_link else None,
                divergence_reason=_bitrix_relation_reason(
                    deal_exists=deal_id in deal_rows_by_id,
                    has_contact_link=contact_link is not None,
                ),
            )
        )

    confirmed_ids = tuple(
        relation.deal_id for relation in relations if relation.has_contact_link
    )
    verification = BitrixExplicitDealVerification(
        contact_id=contact_id,
        supplied_deal_ids=supplied_ids,
        bitrix_deal_ids=tuple(sorted(deal_rows_by_id)),
        relations=tuple(relations),
        confirmed_contact_deal_ids=confirmed_ids,
        methods_used=("crm.deal.list", "crm.deal.contact.items.get"),
        explanation=_bitrix_explicit_explanation(
            supplied_ids=supplied_ids,
            confirmed_ids=confirmed_ids,
        ),
    )
    return _BitrixExplicitDealFacts(
        verification=verification,
        deal_rows_by_id=deal_rows_by_id,
        contact_links_by_deal_id=contact_links_by_deal_id,
    )


def _normalize_deal_ids(deal_ids: tuple[int, ...]) -> tuple[int, ...]:
    normalized = tuple(sorted({int(deal_id) for deal_id in deal_ids if int(deal_id) > 0}))
    if not normalized:
        raise ValueError("At least one deal ID is required.")
    if len(normalized) > MAX_EXPLICIT_DEAL_IDS:
        raise ValueError(f"At most {MAX_EXPLICIT_DEAL_IDS} deal IDs are allowed.")
    return normalized


def _load_contact(
    connection: duckdb.DuckDBPyConnection,
    contact_id: int,
) -> ContactSnapshot | None:
    row = connection.execute(
        """
        SELECT contact_id, contact_name, contact_type_raw
        FROM raw_contacts
        WHERE contact_id = ?
        """,
        [contact_id],
    ).fetchone()
    if row is None:
        return None
    return ContactSnapshot(
        contact_id=row[0],
        contact_name=row[1],
        contact_type_raw=row[2],
    )


def _load_linked_deals(
    connection: duckdb.DuckDBPyConnection,
    contact_id: int,
) -> list[LocalLinkedDealDiagnostic]:
    rows = connection.execute(
        """
        SELECT
            links.deal_id,
            raw_deals.deal_id IS NOT NULL AS raw_deal_exists,
            raw_deals.status_group,
            links.is_primary,
            normalized_deals.analytical_contact_id,
            normalized_deals.analytical_contact_name,
            normalized_deals.contact_type_normalized
        FROM raw_deal_contact_links AS links
        LEFT JOIN raw_deals ON raw_deals.deal_id = links.deal_id
        LEFT JOIN normalized_deals ON normalized_deals.deal_id = links.deal_id
        WHERE links.contact_id = ?
        ORDER BY links.deal_id
        """,
        [contact_id],
    ).fetchall()
    return [
        LocalLinkedDealDiagnostic(
            deal_id=row[0],
            raw_deal_exists=row[1],
            status_group=row[2],
            is_primary=row[3],
            analytical_contact_id=row[4],
            analytical_contact_name=row[5],
            analytical_contact_type=row[6],
        )
        for row in rows
    ]


def _load_type_rules(
    connection: duckdb.DuckDBPyConnection,
) -> list[ContactTypeRule]:
    rows = connection.execute(
        """
        SELECT raw_value, normalized_type, priority, region, is_active
        FROM contact_type_rules
        ORDER BY raw_value
        """
    ).fetchall()
    return [
        ContactTypeRule(
            raw_value=row[0],
            normalized_type=row[1],
            priority=row[2],
            region=row[3],
            is_active=row[4],
        )
        for row in rows
    ]


def _load_stages(connection: duckdb.DuckDBPyConnection) -> list[StageSnapshot]:
    rows = connection.execute(
        """
        SELECT stage_id, category_id, status_group
        FROM raw_stages
        ORDER BY stage_id, category_id
        """
    ).fetchall()
    return [
        StageSnapshot(
            stage_id=row[0],
            category_id=row[1],
            status_group=row[2],
        )
        for row in rows
    ]


def _raw_deal_ids(
    connection: duckdb.DuckDBPyConnection,
    deal_ids: tuple[int, ...],
) -> set[int]:
    if not deal_ids:
        return set()
    placeholders = ", ".join("?" for _ in deal_ids)
    rows = connection.execute(
        f"""
        SELECT deal_id
        FROM raw_deals
        WHERE deal_id IN ({placeholders})
        """,
        list(deal_ids),
    ).fetchall()
    return {row[0] for row in rows}


def _raw_deal_state(
    connection: duckdb.DuckDBPyConnection,
    deal_ids: tuple[int, ...],
) -> dict[int, DealSnapshot]:
    if not deal_ids:
        return {}
    placeholders = ", ".join("?" for _ in deal_ids)
    rows = connection.execute(
        f"""
        SELECT deal_id, deal_name, amount_original, currency_original,
               created_at, planned_close_at, actual_closed_at, stage_id,
               category_id, status_group, kev_held
        FROM raw_deals WHERE deal_id IN ({placeholders})
        """,
        list(deal_ids),
    ).fetchall()
    return {
        row[0]: DealSnapshot(
            deal_id=row[0],
            deal_name=row[1],
            amount_original=Decimal(row[2]),
            currency_original=row[3],
            created_at=_as_utc(row[4]),
            planned_close_at=_as_utc(row[5]) if row[5] is not None else None,
            actual_closed_at=_as_utc(row[6]) if row[6] is not None else None,
            stage_id=row[7],
            category_id=row[8],
            status_group=row[9],
            kev_held=row[10],
        )
        for row in rows
    }


def _deal_requires_reconciliation(
    deal: DealSnapshot,
    local_state: DealSnapshot | None,
) -> bool:
    return local_state is None or deal != local_state


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _linked_contact_ids_by_deal_id(
    connection: duckdb.DuckDBPyConnection,
    deal_ids: tuple[int, ...],
) -> dict[int, tuple[int, ...]]:
    if not deal_ids:
        return {}
    placeholders = ", ".join("?" for _ in deal_ids)
    rows = connection.execute(
        f"""
        SELECT deal_id, contact_id
        FROM raw_deal_contact_links
        WHERE deal_id IN ({placeholders})
        ORDER BY deal_id, contact_id
        """,
        list(deal_ids),
    ).fetchall()
    result: dict[int, list[int]] = {}
    for deal_id, contact_id in rows:
        result.setdefault(deal_id, []).append(contact_id)
    return {deal_id: tuple(contact_ids) for deal_id, contact_ids in result.items()}


def _normalized_deals_by_id(
    connection: duckdb.DuckDBPyConnection,
    deal_ids: tuple[int, ...],
) -> dict[int, tuple[int | None, str | None, str | None]]:
    if not deal_ids:
        return {}
    placeholders = ", ".join("?" for _ in deal_ids)
    rows = connection.execute(
        f"""
        SELECT
            deal_id,
            analytical_contact_id,
            analytical_contact_name,
            contact_type_normalized
        FROM normalized_deals
        WHERE deal_id IN ({placeholders})
        """,
        list(deal_ids),
    ).fetchall()
    return {row[0]: (row[1], row[2], row[3]) for row in rows}


def _upsert_raw_deals(
    connection: duckdb.DuckDBPyConnection,
    deals: list[DealSnapshot],
) -> None:
    if not deals:
        return
    connection.executemany(
        """
        INSERT INTO raw_deals (
            deal_id,
            deal_name,
            amount_original,
            currency_original,
            created_at,
            closed_at,
            planned_close_at,
            actual_closed_at,
            stage_id,
            category_id,
            status_group,
            kev_held
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (deal_id) DO UPDATE SET
            deal_name = excluded.deal_name,
            amount_original = excluded.amount_original,
            currency_original = excluded.currency_original,
            created_at = excluded.created_at,
            closed_at = NULL,
            planned_close_at = excluded.planned_close_at,
            actual_closed_at = excluded.actual_closed_at,
            stage_id = excluded.stage_id,
            category_id = excluded.category_id,
            status_group = excluded.status_group,
            kev_held = excluded.kev_held
        """,
        [
            (
                deal.deal_id,
                deal.deal_name,
                deal.amount_original,
                deal.currency_original,
                deal.created_at,
                None,
                deal.planned_close_at,
                deal.actual_closed_at,
                deal.stage_id,
                deal.category_id,
                deal.status_group,
                deal.kev_held,
            )
            for deal in deals
        ],
    )


def _upsert_raw_stage_history(
    connection: duckdb.DuckDBPyConnection,
    history: list[DealStageHistorySnapshot],
) -> None:
    if not history:
        return
    connection.executemany(
        """
        INSERT INTO raw_deal_stage_history (
            history_id, deal_id, type_id, created_at, category_id, stage_id, stage_semantic_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (history_id) DO UPDATE SET
            deal_id = excluded.deal_id,
            type_id = excluded.type_id,
            created_at = excluded.created_at,
            category_id = excluded.category_id,
            stage_id = excluded.stage_id,
            stage_semantic_id = excluded.stage_semantic_id
        """,
        [
            (
                row.history_id,
                row.deal_id,
                row.type_id,
                row.created_at,
                row.category_id,
                row.stage_id,
                row.stage_semantic_id,
            )
            for row in history
        ],
    )


def _insert_raw_links(
    connection: duckdb.DuckDBPyConnection,
    links: list[DealContactLink],
) -> None:
    if not links:
        return
    connection.executemany(
        """
        INSERT INTO raw_deal_contact_links (
            deal_id,
            contact_id,
            is_primary,
            sort_order,
            role_id
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (deal_id, contact_id) DO NOTHING
        """,
        [
            (
                link.deal_id,
                link.contact_id,
                link.is_primary,
                link.sort_order,
                link.role_id,
            )
            for link in links
        ],
    )


def _store_reconciliation_status(
    connection: duckdb.DuckDBPyConnection,
    *,
    state: str,
    message: str,
    started_at: datetime,
    is_active: bool,
) -> DatasetRunStatus:
    status = _build_reconciliation_status(
        connection,
        state=state,
        message=message,
        started_at=started_at,
        is_active=is_active,
    )
    store_dataset_run(connection, status)
    return status


def _build_reconciliation_status(
    connection: duckdb.DuckDBPyConnection,
    *,
    state: str,
    message: str,
    started_at: datetime,
    is_active: bool,
) -> DatasetRunStatus:
    finished_at = datetime.now(timezone.utc)
    return DatasetRunStatus(
        run_id=build_run_id(EXPLICIT_RECONCILIATION_DATASET_KIND, started_at),
        dataset_name=EXPLICIT_RECONCILIATION_DATASET_NAME,
        dataset_kind=EXPLICIT_RECONCILIATION_DATASET_KIND,
        state=state,
        message=message,
        started_at=started_at,
        finished_at=finished_at,
        snapshot_paths=(),
        is_active=is_active,
        **count_current_rows(connection),
    )


def _row_deal_id(row: dict[str, object]) -> int:
    value = row.get("ID", row.get("id"))
    if value in (None, ""):
        raise ValueError("Bitrix deal row is missing ID.")
    return int(value)


def _local_explanation(
    *,
    contact_exists: bool,
    linked_deal_ids: tuple[int, ...],
    analytical_deal_ids: tuple[int, ...],
) -> str:
    if not contact_exists:
        return "Contact is absent from local raw_contacts."
    if len(linked_deal_ids) == len(analytical_deal_ids):
        return (
            "Local raw links and normalized analytical deals agree. If Bitrix "
            "shows more deals, the divergence is before local analytical "
            "contact selection, in Bitrix extraction/link reconstruction."
        )
    if len(linked_deal_ids) > len(analytical_deal_ids):
        return (
            "Local links contain deals that are assigned to another analytical "
            "contact or have incomplete local facts."
        )
    return "Local analytical deals include deals not present in local raw links."


def _explicit_local_reason(
    *,
    raw_deal_exists: bool,
    has_contact_link: bool,
    linked_contact_ids: tuple[int, ...],
    analytical_contact_id: int | None,
    contact_id: int,
) -> str:
    if not raw_deal_exists:
        return "missing_raw_deal"
    if has_contact_link and analytical_contact_id == contact_id:
        return "counts_for_contact"
    if has_contact_link:
        return "linked_but_assigned_to_another_analytical_contact"
    if not linked_contact_ids:
        return "missing_local_link_no_local_contacts"
    return "missing_contact_link_assigned_to_another_contact"


def _bitrix_relation_reason(
    *,
    deal_exists: bool,
    has_contact_link: bool,
) -> str:
    if deal_exists and has_contact_link:
        return "bitrix_deal_and_contact_relation_confirmed"
    if has_contact_link:
        return "bitrix_contact_relation_confirmed_but_deal_list_missing"
    if deal_exists:
        return "bitrix_deal_exists_without_contact_relation"
    return "bitrix_deal_not_returned_and_contact_relation_absent"


def _bitrix_explicit_explanation(
    *,
    supplied_ids: tuple[int, ...],
    confirmed_ids: tuple[int, ...],
) -> str:
    if len(confirmed_ids) == len(supplied_ids):
        return "Bitrix confirmed the contact relation for every supplied deal."
    if confirmed_ids:
        return "Bitrix confirmed the contact relation for only some supplied deals."
    return "Bitrix did not confirm the contact relation for any supplied deal."


def _reconciliation_explanation(
    *,
    confirmed_ids: tuple[int, ...],
    inserted_link_ids: tuple[int, ...],
    skipped_ids: tuple[int, ...],
) -> str:
    if not confirmed_ids:
        return "No local data was changed because Bitrix did not confirm any supplied relation."
    if skipped_ids:
        return "Some confirmed deals were skipped because safe deal rows were unavailable."
    return f"Reconciliation inserted {len(inserted_link_ids)} missing local links."


def _bitrix_item_list_explanation(is_complete: bool) -> str:
    if is_complete:
        return "crm.item.list returned every supplied deal and included the contact relation for each one."
    return "crm.item.list did not return a complete supplied-deal/contact relation set."
