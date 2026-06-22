from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import duckdb

from app.storage import initialize_schema


@dataclass(frozen=True)
class FilterMetadata:
    contact_types: tuple[str, ...]
    regions: tuple[str, ...]
    statuses: tuple[str, ...]
    min_created_at: datetime | None
    max_created_at: datetime | None
    min_closed_at: datetime | None
    max_closed_at: datetime | None


@dataclass(frozen=True)
class ContactSummaryRow:
    contact_id: int
    contact_name: str
    contact_type_raw: str | None
    contact_type_normalized: str
    region_normalized: str
    total_deals_count: int
    won_deals_count: int
    open_deals_count: int
    lost_deals_count: int
    total_amount_original: Decimal


@dataclass(frozen=True)
class ContactSummaryPage:
    total: int
    limit: int
    offset: int
    items: tuple[ContactSummaryRow, ...]


def get_filter_metadata(connection: duckdb.DuckDBPyConnection) -> FilterMetadata:
    initialize_schema(connection)
    contact_types = _single_column(
        connection,
        """
        SELECT DISTINCT contact_type_normalized
        FROM normalized_contacts
        WHERE contact_type_normalized IS NOT NULL
        AND contact_type_normalized != ''
        ORDER BY contact_type_normalized
        """,
    )
    regions = _single_column(
        connection,
        """
        SELECT DISTINCT region_normalized
        FROM normalized_contacts
        WHERE region_normalized IS NOT NULL
        AND region_normalized != ''
        ORDER BY region_normalized
        """,
    )
    statuses = _single_column(
        connection,
        """
        SELECT DISTINCT status_group
        FROM normalized_deals
        WHERE status_group IS NOT NULL
        AND status_group != ''
        ORDER BY status_group
        """,
    )
    period_row = connection.execute(
        """
        SELECT
            MIN(created_at),
            MAX(created_at),
            MIN(closed_at),
            MAX(closed_at)
        FROM normalized_deals
        """
    ).fetchone()
    if period_row is None:
        period_row = (None, None, None, None)
    return FilterMetadata(
        contact_types=contact_types,
        regions=regions,
        statuses=statuses,
        min_created_at=period_row[0],
        max_created_at=period_row[1],
        min_closed_at=period_row[2],
        max_closed_at=period_row[3],
    )


def list_contact_summaries(
    connection: duckdb.DuckDBPyConnection,
    *,
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
    contact_type: str | None = None,
    region: str | None = None,
    status: str | None = None,
) -> ContactSummaryPage:
    filters = []
    params: list[object] = []

    if search:
        filters.append("lower(contact_name) LIKE ?")
        params.append(f"%{search.lower()}%")
    if contact_type:
        filters.append("contact_type_normalized = ?")
        params.append(contact_type)
    if region:
        filters.append("region_normalized = ?")
        params.append(region)
    if status:
        filters.append(
            """
            EXISTS (
                SELECT 1
                FROM normalized_deals status_deals
                WHERE status_deals.analytical_contact_id = normalized_contacts.contact_id
                AND status_deals.status_group = ?
            )
            """
        )
        params.append(status)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    total = connection.execute(
        f"SELECT COUNT(*) FROM normalized_contacts {where_clause}",
        params,
    ).fetchone()[0]

    rows = connection.execute(
        f"""
        SELECT
            contact_id,
            contact_name,
            contact_type_raw,
            contact_type_normalized,
            region_normalized,
            (
                SELECT COUNT(*)
                FROM normalized_deals deals
                WHERE deals.analytical_contact_id = normalized_contacts.contact_id
            ) AS total_deals_count,
            (
                SELECT COUNT(*)
                FROM normalized_deals deals
                WHERE deals.analytical_contact_id = normalized_contacts.contact_id
                AND deals.status_group = 'won'
            ) AS won_deals_count,
            (
                SELECT COUNT(*)
                FROM normalized_deals deals
                WHERE deals.analytical_contact_id = normalized_contacts.contact_id
                AND deals.status_group = 'open'
            ) AS open_deals_count,
            (
                SELECT COUNT(*)
                FROM normalized_deals deals
                WHERE deals.analytical_contact_id = normalized_contacts.contact_id
                AND deals.status_group = 'lost'
            ) AS lost_deals_count,
            (
                SELECT COALESCE(SUM(amount_original), 0)
                FROM normalized_deals deals
                WHERE deals.analytical_contact_id = normalized_contacts.contact_id
            ) AS total_amount_original
        FROM normalized_contacts
        {where_clause}
        ORDER BY contact_id
        LIMIT ?
        OFFSET ?
        """,
        [*params, limit, offset],
    ).fetchall()

    return ContactSummaryPage(
        total=total,
        limit=limit,
        offset=offset,
        items=tuple(
            ContactSummaryRow(
                contact_id=row[0],
                contact_name=row[1],
                contact_type_raw=row[2],
                contact_type_normalized=row[3],
                region_normalized=row[4],
                total_deals_count=row[5],
                won_deals_count=row[6],
                open_deals_count=row[7],
                lost_deals_count=row[8],
                total_amount_original=Decimal(row[9]),
            )
            for row in rows
        ),
    )


def _single_column(
    connection: duckdb.DuckDBPyConnection,
    query: str,
) -> tuple[str, ...]:
    return tuple(row[0] for row in connection.execute(query).fetchall())
