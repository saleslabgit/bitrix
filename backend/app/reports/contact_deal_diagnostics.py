from __future__ import annotations

from dataclasses import dataclass

import duckdb

from app.bitrix.client import BitrixClient
from app.bitrix.transform import transform_deals
from app.domain import ContactSnapshot, ContactTypeRule, DealSnapshot, StageSnapshot
from app.domain.contact_type_resolution import resolve_contact_type
from app.pipeline.normalization import normalize_local_data


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
class BitrixContactDealVerification:
    contact_id: int
    bitrix_deals_count: int
    bitrix_deal_ids: tuple[int, ...]
    local_linked_deals_count: int
    local_linked_deal_ids: tuple[int, ...]
    local_analytical_deals_count: int
    local_analytical_deal_ids: tuple[int, ...]
    missing_local_link_deal_ids: tuple[int, ...]
    missing_raw_deal_ids: tuple[int, ...]
    correction_applied: bool
    raw_links_inserted: int
    raw_deals_inserted: int
    methods_used: tuple[str, ...]
    explanation: str


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


def verify_bitrix_contact_deals(
    connection: duckdb.DuckDBPyConnection,
    *,
    client: BitrixClient,
    contact_id: int,
    apply_local_correction: bool = False,
) -> BitrixContactDealVerification:
    bitrix_deal_rows = client.list_deals_for_contact(contact_id)
    bitrix_deal_ids = tuple(sorted({_row_deal_id(row) for row in bitrix_deal_rows}))
    before = get_contact_deal_diagnostic(connection, contact_id)
    missing_link_deal_ids = tuple(
        deal_id for deal_id in bitrix_deal_ids if deal_id not in before.local_linked_deal_ids
    )
    raw_deal_ids = _raw_deal_ids(connection, bitrix_deal_ids)
    missing_raw_deal_ids = tuple(
        deal_id for deal_id in bitrix_deal_ids if deal_id not in raw_deal_ids
    )

    raw_deals_inserted = 0
    raw_links_inserted = 0
    if apply_local_correction and missing_link_deal_ids:
        raw_deals_inserted, raw_links_inserted = _apply_contact_deal_correction(
            connection,
            contact_id=contact_id,
            bitrix_deal_rows=bitrix_deal_rows,
            missing_link_deal_ids=missing_link_deal_ids,
            missing_raw_deal_ids=missing_raw_deal_ids,
        )

    after = get_contact_deal_diagnostic(connection, contact_id)
    return BitrixContactDealVerification(
        contact_id=contact_id,
        bitrix_deals_count=len(bitrix_deal_ids),
        bitrix_deal_ids=bitrix_deal_ids,
        local_linked_deals_count=after.local_linked_deals_count,
        local_linked_deal_ids=after.local_linked_deal_ids,
        local_analytical_deals_count=after.local_analytical_deals_count,
        local_analytical_deal_ids=after.local_analytical_deal_ids,
        missing_local_link_deal_ids=tuple(
            deal_id for deal_id in bitrix_deal_ids if deal_id not in after.local_linked_deal_ids
        ),
        missing_raw_deal_ids=tuple(
            deal_id for deal_id in bitrix_deal_ids if deal_id not in _raw_deal_ids(connection, bitrix_deal_ids)
        ),
        correction_applied=apply_local_correction,
        raw_links_inserted=raw_links_inserted,
        raw_deals_inserted=raw_deals_inserted,
        methods_used=("crm.deal.list",),
        explanation=_bitrix_explanation(
            bitrix_deal_ids=bitrix_deal_ids,
            local_linked_deal_ids=after.local_linked_deal_ids,
            correction_applied=apply_local_correction,
        ),
    )


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


def _apply_contact_deal_correction(
    connection: duckdb.DuckDBPyConnection,
    *,
    contact_id: int,
    bitrix_deal_rows: list[dict[str, object]],
    missing_link_deal_ids: tuple[int, ...],
    missing_raw_deal_ids: tuple[int, ...],
) -> tuple[int, int]:
    rows_by_id = {_row_deal_id(row): row for row in bitrix_deal_rows}
    deals_to_insert = [
        deal
        for deal in transform_deals(
            [rows_by_id[deal_id] for deal_id in missing_raw_deal_ids],
            _load_stages(connection),
        )
    ]
    links_to_insert = [
        (
            deal_id,
            contact_id,
            _is_primary_contact(rows_by_id[deal_id], contact_id),
            None,
            None,
        )
        for deal_id in missing_link_deal_ids
    ]

    connection.execute("BEGIN TRANSACTION")
    try:
        _insert_raw_deals(connection, deals_to_insert)
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
            links_to_insert,
        )
        normalize_local_data(connection)
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    return len(deals_to_insert), len(links_to_insert)


def _insert_raw_deals(
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
            stage_id,
            category_id,
            status_group
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (deal_id) DO NOTHING
        """,
        [
            (
                deal.deal_id,
                deal.deal_name,
                deal.amount_original,
                deal.currency_original,
                deal.created_at,
                deal.closed_at,
                deal.stage_id,
                deal.category_id,
                deal.status_group,
            )
            for deal in deals
        ],
    )


def _row_deal_id(row: dict[str, object]) -> int:
    value = row.get("ID", row.get("id"))
    if value in (None, ""):
        raise ValueError("Bitrix deal row is missing ID.")
    return int(value)


def _is_primary_contact(row: dict[str, object], contact_id: int) -> bool:
    value = row.get("CONTACT_ID", row.get("contactId"))
    if value in (None, ""):
        return False
    return int(value) == contact_id


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


def _bitrix_explanation(
    *,
    bitrix_deal_ids: tuple[int, ...],
    local_linked_deal_ids: tuple[int, ...],
    correction_applied: bool,
) -> str:
    if len(bitrix_deal_ids) == len(local_linked_deal_ids):
        return "Bitrix filtered deals and local raw links agree for this contact."
    if correction_applied:
        return "Targeted local correction was applied, but some Bitrix deals are still missing locally."
    return (
        "Bitrix filtered deals include deal IDs that are absent from local "
        "raw_deal_contact_links for this contact."
    )
