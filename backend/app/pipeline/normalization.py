from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

import duckdb

from app.domain import (
    ContactSnapshot,
    ContactTypeRule,
    DealContactLink,
    DealSnapshot,
    StageSnapshot,
    resolve_contact_type,
    select_analytical_contact,
)


UNDEFINED_VALUE = "Не определено"
NO_CONTACT_NAME = "Без контакта"


def normalize_local_data(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute("DELETE FROM normalized_deals")
    connection.execute("DELETE FROM normalized_contacts")

    contacts = _load_contacts(connection)
    deals = _load_deals(connection)
    links = _load_links(connection)
    stages = _load_stages(connection)
    type_rules = _load_type_rules(connection)

    normalized_contacts = {
        contact.contact_id: _normalize_contact(contact, type_rules)
        for contact in contacts.values()
    }

    normalized_contact_rows = [
        (
            contact_id,
            contact.contact_name,
            contact.contact_type_raw,
            normalized_type,
            normalized_region,
        )
        for contact_id, (
            contact,
            normalized_type,
            normalized_region,
        ) in normalized_contacts.items()
    ]
    if normalized_contact_rows:
        connection.executemany(
            """
            INSERT INTO normalized_contacts (
                contact_id,
                contact_name,
                contact_type_raw,
                contact_type_normalized,
                region_normalized
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            normalized_contact_rows,
        )

    links_by_deal_id: dict[int, list[DealContactLink]] = defaultdict(list)
    for link in links:
        links_by_deal_id[link.deal_id].append(link)

    stage_status_by_key = {
        (stage.stage_id, stage.category_id): stage.status_group for stage in stages
    }

    normalized_deal_rows = []
    for deal in deals:
        status_group = stage_status_by_key.get(
            (deal.stage_id, deal.category_id),
            deal.status_group,
        )
        analytical_contact_id = select_analytical_contact(
            links=links_by_deal_id.get(deal.deal_id, ()),
            contacts_by_id=contacts,
            type_rules=type_rules,
        )
        if analytical_contact_id is None:
            analytical_contact_name = NO_CONTACT_NAME
            contact_type_normalized = UNDEFINED_VALUE
            region_normalized = UNDEFINED_VALUE
        else:
            contact, contact_type_normalized, region_normalized = normalized_contacts[
                analytical_contact_id
            ]
            analytical_contact_name = contact.contact_name

        normalized_deal_rows.append(
            (
                deal.deal_id,
                deal.deal_name,
                deal.amount_original,
                deal.currency_original,
                deal.created_at,
                deal.closed_at,
                deal.stage_id,
                deal.category_id,
                status_group,
                analytical_contact_id,
                analytical_contact_name,
                contact_type_normalized,
                region_normalized,
                deal.kev_held,
            )
        )

    if normalized_deal_rows:
        connection.executemany(
            """
            INSERT INTO normalized_deals (
                deal_id,
                deal_name,
                amount_original,
                currency_original,
                created_at,
                closed_at,
                stage_id,
                category_id,
                status_group,
                analytical_contact_id,
                analytical_contact_name,
                contact_type_normalized,
                region_normalized,
                kev_held
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            normalized_deal_rows,
        )


def _normalize_contact(
    contact: ContactSnapshot,
    type_rules: list[ContactTypeRule],
) -> tuple[ContactSnapshot, str, str]:
    resolved_type = resolve_contact_type(contact.contact_type_raw, type_rules)
    if resolved_type is None:
        return contact, UNDEFINED_VALUE, UNDEFINED_VALUE

    return contact, resolved_type.normalized_type, resolved_type.region


def _load_contacts(
    connection: duckdb.DuckDBPyConnection,
) -> dict[int, ContactSnapshot]:
    rows = connection.execute(
        """
        SELECT contact_id, contact_name, contact_type_raw
        FROM raw_contacts
        ORDER BY contact_id
        """
    ).fetchall()
    return {
        row[0]: ContactSnapshot(
            contact_id=row[0],
            contact_name=row[1],
            contact_type_raw=row[2],
        )
        for row in rows
    }


def _load_deals(connection: duckdb.DuckDBPyConnection) -> list[DealSnapshot]:
    rows = connection.execute(
        """
        SELECT
            deal_id,
            deal_name,
            amount_original,
            currency_original,
            created_at,
            closed_at,
            stage_id,
            category_id,
            status_group
            ,kev_held
        FROM raw_deals
        ORDER BY deal_id
        """
    ).fetchall()
    return [
        DealSnapshot(
            deal_id=row[0],
            deal_name=row[1],
            amount_original=Decimal(row[2]),
            currency_original=row[3],
            created_at=_as_utc(row[4]),
            closed_at=_as_utc(row[5]) if row[5] is not None else None,
            stage_id=row[6],
            category_id=row[7],
            status_group=row[8],
            kev_held=row[9],
        )
        for row in rows
    ]


def _load_links(connection: duckdb.DuckDBPyConnection) -> list[DealContactLink]:
    rows = connection.execute(
        """
        SELECT deal_id, contact_id, is_primary, sort_order, role_id
        FROM raw_deal_contact_links
        ORDER BY deal_id, contact_id
        """
    ).fetchall()
    return [
        DealContactLink(
            deal_id=row[0],
            contact_id=row[1],
            is_primary=row[2],
            sort_order=row[3],
            role_id=row[4],
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


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
