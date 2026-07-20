from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from functools import cmp_to_key
from math import ceil
from typing import Literal

import duckdb

from app.pipeline.normalization import UNDEFINED_VALUE
from app.storage import initialize_schema


NO_SALES_SEGMENT = "Нет продаж"
REACTIVATION_DAYS_THRESHOLD = 365
MONEY_QUANT = Decimal("0.01")
PERCENT_QUANT = Decimal("0.1")
ContactAnalyticsSortField = Literal[
    "contact_id",
    "contact_name",
    "contact_type_normalized",
    "region_normalized",
    "total_deals_count",
    "won_deals_count",
    "open_deals_count",
    "lost_deals_count",
    "budget_usd",
    "budget_in_work_usd",
    "lost_budget_usd",
    "revenue_usd",
    "estimated_profit_usd",
    "average_check_usd",
    "average_cycle_days",
    "last_won_date",
    "latest_deal_date",
]
DealAnalyticsSortField = Literal[
    "deal_id",
    "deal_name",
    "status_group",
    "contact_type_normalized",
    "region_normalized",
    "budget_usd",
    "estimated_profit_usd",
    "created_date",
    "closed_date",
    "category_id",
    "cycle_days",
]
AbcAnalyticsSortField = Literal[
    "contact_id",
    "contact_name",
    "contact_type_normalized",
    "base_revenue_usd",
    "base_revenue_share_percent",
    "base_cumulative_share_percent",
    "base_segment",
    "base_won_deals_count",
    "base_last_won_date",
    "target_revenue_usd",
    "target_segment",
    "segment_change",
    "migration_priority",
]
SortOrder = Literal["asc", "desc"]
CONTACT_ANALYTICS_SORT_FIELDS: tuple[str, ...] = (
    "contact_id",
    "contact_name",
    "contact_type_normalized",
    "region_normalized",
    "total_deals_count",
    "won_deals_count",
    "open_deals_count",
    "lost_deals_count",
    "budget_usd",
    "budget_in_work_usd",
    "lost_budget_usd",
    "revenue_usd",
    "estimated_profit_usd",
    "average_check_usd",
    "average_cycle_days",
    "last_won_date",
    "latest_deal_date",
)
DEAL_ANALYTICS_SORT_FIELDS: tuple[str, ...] = (
    "deal_id",
    "deal_name",
    "status_group",
    "contact_type_normalized",
    "region_normalized",
    "budget_usd",
    "estimated_profit_usd",
    "created_date",
    "closed_date",
)
ABC_ANALYTICS_SORT_FIELDS: tuple[str, ...] = (
    "contact_id",
    "contact_name",
    "contact_type_normalized",
    "base_revenue_usd",
    "base_revenue_share_percent",
    "base_cumulative_share_percent",
    "base_segment",
    "base_won_deals_count",
    "base_last_won_date",
    "target_revenue_usd",
    "target_segment",
    "segment_change",
    "migration_priority",
)


@dataclass(frozen=True)
class CurrencyConversionRow:
    deal_id: int
    amount_original: Decimal
    currency_original: str
    target_date: date
    rate_date: date
    source_rate_byn: Decimal
    usd_rate_byn: Decimal
    amount_usd: Decimal


@dataclass(frozen=True)
class ContactAnalyticsRow:
    contact_id: int
    contact_name: str
    contact_type_normalized: str
    region_normalized: str
    total_deals_count: int
    won_deals_count: int
    open_deals_count: int
    lost_deals_count: int
    budget_usd: Decimal
    budget_in_work_usd: Decimal
    lost_budget_usd: Decimal
    revenue_usd: Decimal
    estimated_profit_usd: Decimal
    first_won_date: date | None
    last_won_date: date | None
    latest_deal_date: date | None
    has_sales: bool
    average_check_usd: Decimal | None
    average_cycle_days: Decimal | None


@dataclass(frozen=True)
class ContactAnalyticsPage:
    total: int
    limit: int
    offset: int
    items: tuple[ContactAnalyticsRow, ...]
    filtered_total_deals_count: int
    filtered_won_deals_count: int
    filtered_open_deals_count: int
    filtered_lost_deals_count: int
    filtered_budget_usd: Decimal
    filtered_budget_in_work_usd: Decimal
    filtered_lost_budget_usd: Decimal
    filtered_revenue_usd: Decimal
    filtered_estimated_profit_usd: Decimal
    filtered_average_check_usd: Decimal | None
    filtered_average_cycle_days: Decimal | None


@dataclass(frozen=True)
class ContactWonRevenuePoint:
    closed_date: date
    revenue_usd: Decimal
    won_deals_count: int


@dataclass(frozen=True)
class ContactWonRevenueSeries:
    contact_id: int
    contact_name: str
    date_from: date | None
    date_to: date | None
    total_revenue_usd: Decimal
    won_deals_count: int
    points: tuple[ContactWonRevenuePoint, ...]


@dataclass(frozen=True)
class DealAnalyticsRow:
    deal_id: int
    deal_name: str
    status_group: str
    contact_type_normalized: str
    region_normalized: str
    budget_usd: Decimal
    estimated_profit_usd: Decimal
    created_date: date
    closed_date: date | None
    kev_held: bool
    category_id: int
    category_name: str | None
    cycle_days: int | None


@dataclass(frozen=True)
class DealAnalyticsPage:
    total: int
    limit: int
    offset: int
    filtered_budget_usd: Decimal
    filtered_revenue_usd: Decimal
    filtered_estimated_profit_usd: Decimal
    filtered_won_deals_count: int
    filtered_open_deals_count: int
    filtered_lost_deals_count: int
    filtered_average_check_usd: Decimal | None
    filtered_average_cycle_days: Decimal | None
    items: tuple[DealAnalyticsRow, ...]


@dataclass(frozen=True)
class KevConversionGroup:
    closed_deals_count: int
    won_deals_count: int
    lost_deals_count: int
    conversion_percent: Decimal | None


@dataclass(frozen=True)
class KevConversionReport:
    with_kev: KevConversionGroup
    without_kev: KevConversionGroup
    conversion_difference_percentage_points: Decimal | None
    date_from: date | None
    date_to: date | None


@dataclass(frozen=True)
class AbcPeriodMetric:
    revenue_usd: Decimal
    revenue_share_percent: Decimal
    cumulative_share_percent: Decimal
    segment: str
    won_deals_count: int
    last_won_date: date | None


@dataclass(frozen=True)
class AbcAnalyticsRow:
    contact_id: int
    contact_name: str
    contact_type_normalized: str
    base_revenue_usd: Decimal
    base_revenue_share_percent: Decimal
    base_cumulative_share_percent: Decimal
    base_segment: str
    base_won_deals_count: int
    base_last_won_date: date | None
    target_revenue_usd: Decimal
    target_segment: str
    segment_change: str
    migration_priority: str
    segment_changed: bool


@dataclass(frozen=True)
class AbcAnalyticsPage:
    total: int
    limit: int
    offset: int
    base_total_revenue_usd: Decimal
    target_total_revenue_usd: Decimal
    base_segment_counts: dict[str, int]
    target_segment_counts: dict[str, int]
    migration_priority_counts: dict[str, int]
    items: tuple[AbcAnalyticsRow, ...]


class AnalyticsDataUnavailableError(ValueError):
    pass


class ContactNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class AbcRow:
    contact_id: int
    contact_name: str
    contact_type_normalized: str
    region_normalized: str
    revenue_full_usd: Decimal
    revenue_12m_usd: Decimal
    abc_full: str
    abc_12m: str
    abc_change: str
    migration_priority: str


@dataclass(frozen=True)
class RfmRow:
    contact_id: int
    contact_name: str
    contact_type_normalized: str
    region_normalized: str
    recency_days: int | None
    frequency: int
    monetary_usd: Decimal
    r_score: int
    f_score: int
    m_score: int
    rfm_code: str
    segment: str
    needs_reactivation: bool


@dataclass(frozen=True)
class StaleDealRow:
    deal_id: int
    deal_name: str
    analytical_contact_id: int | None
    analytical_contact_name: str
    contact_type_normalized: str
    region_normalized: str
    created_date: date
    days_open: int
    stale_threshold_days: int
    days_over_threshold: int
    amount_original: Decimal
    currency_original: str
    amount_usd: Decimal


@dataclass(frozen=True)
class CycleMetricRow:
    group_name: str
    deals_count: int
    average_days: float
    median_days: float
    p75_days: int
    p90_days: int


@dataclass(frozen=True)
class DealCycleReport:
    overall: CycleMetricRow
    by_contact_type: tuple[CycleMetricRow, ...]
    by_region: tuple[CycleMetricRow, ...]


@dataclass(frozen=True)
class ConcentrationEntry:
    top_n: int
    revenue_usd: Decimal
    share_percent: Decimal


@dataclass(frozen=True)
class ConcentrationReport:
    total_revenue_usd: Decimal
    entries: tuple[ConcentrationEntry, ...]


@dataclass(frozen=True)
class TypeRegionAnalyticsRow:
    group_name: str
    contact_type_normalized: str | None
    region_normalized: str | None
    contact_count: int
    total_deals_count: int
    won_deals_count: int
    open_deals_count: int
    lost_deals_count: int
    revenue_usd: Decimal
    estimated_profit_usd: Decimal


@dataclass(frozen=True)
class TypeRegionAnalyticsReport:
    type_rows: tuple[TypeRegionAnalyticsRow, ...]
    region_rows: tuple[TypeRegionAnalyticsRow, ...]
    matrix_rows: tuple[TypeRegionAnalyticsRow, ...]


@dataclass(frozen=True)
class _ContactFact:
    contact_id: int
    contact_name: str
    contact_type_normalized: str
    region_normalized: str


@dataclass(frozen=True)
class _DealFact:
    deal_id: int
    deal_name: str
    amount_original: Decimal
    currency_original: str
    created_at: datetime
    closed_at: datetime | None
    status_group: str
    analytical_contact_id: int | None
    analytical_contact_name: str
    contact_type_normalized: str
    region_normalized: str
    kev_held: bool
    category_id: int
    category_name: str | None
    target_date: date
    rate_date: date
    source_rate_byn: Decimal
    usd_rate_byn: Decimal
    amount_usd: Decimal


def list_currency_conversions(
    connection: duckdb.DuckDBPyConnection,
) -> tuple[CurrencyConversionRow, ...]:
    return tuple(
        CurrencyConversionRow(
            deal_id=deal.deal_id,
            amount_original=deal.amount_original,
            currency_original=deal.currency_original,
            target_date=deal.target_date,
            rate_date=deal.rate_date,
            source_rate_byn=deal.source_rate_byn,
            usd_rate_byn=deal.usd_rate_byn,
            amount_usd=deal.amount_usd,
        )
        for deal in _load_deal_facts(connection)
    )


def list_contact_analytics(
    connection: duckdb.DuckDBPyConnection,
    *,
    limit: int = 50,
    offset: int = 0,
    date_from: date | None = None,
    date_to: date | None = None,
    deal_created_from: date | None = None,
    deal_created_to: date | None = None,
    category_id: int | None = None,
    search: str | None = None,
    contact_type: str | None = None,
    region: str | None = None,
    status: str | None = None,
    contact_id: int | None = None,
    sort: ContactAnalyticsSortField = "contact_id",
    order: SortOrder = "asc",
) -> ContactAnalyticsPage:
    if sort not in CONTACT_ANALYTICS_SORT_FIELDS:
        raise ValueError(f"Unsupported contact analytics sort field: {sort}")
    if order not in {"asc", "desc"}:
        raise ValueError(f"Unsupported contact analytics sort order: {order}")

    period_deals = [
        deal
        for deal in _load_deal_facts(connection)
        if _date_in_period(_reporting_date(deal), date_from, date_to)
        and _date_in_period(
            deal.created_at.date(),
            deal_created_from,
            deal_created_to,
        )
        and (category_id is None or deal.category_id == category_id)
    ]
    require_matching_deals = deal_created_from is not None or deal_created_to is not None or category_id is not None
    contacts = _filtered_contacts(
        _load_contacts(connection),
        deals=period_deals,
        search=search,
        contact_type=contact_type,
        region=region,
        status=status,
        contact_id=contact_id,
        require_matching_deals=require_matching_deals,
    )

    rows = _sort_contact_analytics_rows(
        tuple(
            _build_contact_analytics_row(contact, period_deals)
            for contact in contacts
        ),
        sort=sort,
        order=order,
    )
    filtered_deals = [deal for deal in period_deals if deal.analytical_contact_id in {contact.contact_id for contact in contacts}]
    return ContactAnalyticsPage(
        total=len(rows),
        limit=limit,
        offset=offset,
        items=rows[offset : offset + limit],
        **_selection_summary(filtered_deals),
    )


def get_contact_won_revenue_series(
    connection: duckdb.DuckDBPyConnection,
    *,
    contact_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
) -> ContactWonRevenueSeries:
    contact = next(
        (row for row in _load_contacts(connection) if row.contact_id == contact_id),
        None,
    )
    if contact is None:
        raise ContactNotFoundError(f"Contact {contact_id} was not found in local data.")

    revenue_by_date: dict[date, Decimal] = {}
    deals_count_by_date: dict[date, int] = {}
    for deal in _load_deal_facts(connection):
        if (
            deal.analytical_contact_id != contact_id
            or deal.status_group != "won"
            or deal.closed_at is None
            or not _date_in_period(deal.closed_at.date(), date_from, date_to)
        ):
            continue
        closed_date = deal.closed_at.date()
        revenue_by_date[closed_date] = _money(
            revenue_by_date.get(closed_date, Decimal("0")) + deal.amount_usd
        )
        deals_count_by_date[closed_date] = deals_count_by_date.get(closed_date, 0) + 1

    points = tuple(
        ContactWonRevenuePoint(
            closed_date=closed_date,
            revenue_usd=_money(revenue_by_date[closed_date]),
            won_deals_count=deals_count_by_date[closed_date],
        )
        for closed_date in sorted(revenue_by_date)
    )
    total_revenue_usd = _money(
        sum((point.revenue_usd for point in points), Decimal("0"))
    )
    return ContactWonRevenueSeries(
        contact_id=contact.contact_id,
        contact_name=contact.contact_name,
        date_from=date_from,
        date_to=date_to,
        total_revenue_usd=total_revenue_usd,
        won_deals_count=sum(point.won_deals_count for point in points),
        points=points,
    )


def list_deal_analytics(
    connection: duckdb.DuckDBPyConnection,
    *,
    limit: int = 50,
    offset: int = 0,
    deal_id: int | None = None,
    client_id: int | None = None,
    status: str | None = None,
    contact_type: str | None = None,
    region: str | None = None,
    client_search: str | None = None,
    deal_created_from: date | None = None,
    deal_created_to: date | None = None,
    kev_held: bool | None = None,
    category_id: int | None = None,
    sort: DealAnalyticsSortField = "deal_id",
    order: SortOrder = "asc",
) -> DealAnalyticsPage:
    if sort not in DEAL_ANALYTICS_SORT_FIELDS:
        raise ValueError(f"Unsupported deal analytics sort field: {sort}")
    if order not in {"asc", "desc"}:
        raise ValueError(f"Unsupported deal analytics sort order: {order}")

    normalized_client_search = client_search.strip().lower() if client_search else None
    if normalized_client_search == "":
        normalized_client_search = None
    deals = [
        deal
        for deal in _load_deal_facts(connection)
        if (deal_id is None or deal.deal_id == deal_id)
        and (client_id is None or deal.analytical_contact_id == client_id)
        and (status is None or deal.status_group == status)
        and (contact_type is None or deal.contact_type_normalized == contact_type)
        and (region is None or deal.region_normalized == region)
        and (kev_held is None or deal.kev_held is kev_held)
        and (category_id is None or deal.category_id == category_id)
        and (
            client_id is not None
            or normalized_client_search is None
            or normalized_client_search in deal.analytical_contact_name.lower()
        )
        and _date_in_period(deal.created_at.date(), deal_created_from, deal_created_to)
    ]
    filtered_rows = tuple(_build_deal_analytics_row(deal) for deal in deals)
    rows = _sort_deal_analytics_rows(
        filtered_rows,
        sort=sort,
        order=order,
    )
    return DealAnalyticsPage(
        total=len(rows),
        limit=limit,
        offset=offset,
        filtered_budget_usd=_money(
            sum((row.budget_usd for row in filtered_rows), Decimal("0"))
        ),
        filtered_revenue_usd=_money(
            sum(
                (
                    row.budget_usd
                    for row in filtered_rows
                    if row.status_group == "won"
                ),
                Decimal("0"),
            )
        ),
        filtered_estimated_profit_usd=_money(
            sum((row.estimated_profit_usd for row in filtered_rows), Decimal("0"))
        ),
        filtered_won_deals_count=sum(row.status_group == "won" for row in filtered_rows),
        filtered_open_deals_count=sum(row.status_group == "open" for row in filtered_rows),
        filtered_lost_deals_count=sum(row.status_group == "lost" for row in filtered_rows),
        filtered_average_check_usd=_average_check(deals),
        filtered_average_cycle_days=_average_cycle(deals),
        items=rows[offset : offset + limit],
    )


def get_kev_conversion_report(
    connection: duckdb.DuckDBPyConnection,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    contact_type: str | None = None,
    deal_created_from: date | None = None,
    deal_created_to: date | None = None,
    category_id: int | None = None,
) -> KevConversionReport:
    initialize_schema(connection)
    filters = ["status_group IN ('won', 'lost')", "actual_closed_at IS NOT NULL"]
    parameters: list[object] = []
    if date_from is not None:
        filters.append("CAST(actual_closed_at AS DATE) >= ?")
        parameters.append(date_from)
    if date_to is not None:
        filters.append("CAST(actual_closed_at AS DATE) <= ?")
        parameters.append(date_to)
    if contact_type is not None:
        filters.append("contact_type_normalized = ?")
        parameters.append(contact_type)
    if deal_created_from is not None:
        filters.append("CAST(created_at AS DATE) >= ?")
        parameters.append(deal_created_from)
    if deal_created_to is not None:
        filters.append("CAST(created_at AS DATE) <= ?")
        parameters.append(deal_created_to)
    if category_id is not None:
        filters.append("category_id = ?")
        parameters.append(category_id)

    rows = connection.execute(
        f"""
        SELECT
            kev_held,
            COUNT(*) AS closed_deals_count,
            COUNT(*) FILTER (WHERE status_group = 'won') AS won_deals_count,
            COUNT(*) FILTER (WHERE status_group = 'lost') AS lost_deals_count
        FROM normalized_deals
        WHERE {' AND '.join(filters)}
        GROUP BY kev_held
        """,
        parameters,
    ).fetchall()
    counts = {bool(row[0]): (int(row[1]), int(row[2]), int(row[3])) for row in rows}
    with_kev = _kev_conversion_group(counts.get(True, (0, 0, 0)))
    without_kev = _kev_conversion_group(counts.get(False, (0, 0, 0)))
    difference = (
        None
        if with_kev.conversion_percent is None or without_kev.conversion_percent is None
        else (with_kev.conversion_percent - without_kev.conversion_percent).quantize(
            PERCENT_QUANT,
            rounding=ROUND_HALF_UP,
        )
    )
    return KevConversionReport(
        with_kev=with_kev,
        without_kev=without_kev,
        conversion_difference_percentage_points=difference,
        date_from=date_from,
        date_to=date_to,
    )


def get_abc_report(
    connection: duckdb.DuckDBPyConnection,
    *,
    analysis_date: date | None = None,
) -> tuple[AbcRow, ...]:
    contacts = _load_contacts(connection)
    deals = _load_deal_facts(connection)
    anchor_date = analysis_date or _default_analysis_date(deals)
    last_12m_start = _one_year_before(anchor_date)

    full_revenue = _revenue_by_contact(deals, date_from=None, date_to=anchor_date)
    recent_revenue = _revenue_by_contact(
        deals,
        date_from=last_12m_start,
        date_to=anchor_date,
    )
    full_segments = _classify_abc(full_revenue)
    recent_segments = _classify_abc(recent_revenue)

    return tuple(
        AbcRow(
            contact_id=contact.contact_id,
            contact_name=contact.contact_name,
            contact_type_normalized=contact.contact_type_normalized,
            region_normalized=contact.region_normalized,
            revenue_full_usd=_money(full_revenue.get(contact.contact_id, Decimal("0"))),
            revenue_12m_usd=_money(recent_revenue.get(contact.contact_id, Decimal("0"))),
            abc_full=full_segments.get(contact.contact_id, NO_SALES_SEGMENT),
            abc_12m=recent_segments.get(contact.contact_id, NO_SALES_SEGMENT),
            abc_change=_abc_change(
                full_segments.get(contact.contact_id, NO_SALES_SEGMENT),
                recent_segments.get(contact.contact_id, NO_SALES_SEGMENT),
            ),
            migration_priority=_migration_priority(
                full_segments.get(contact.contact_id, NO_SALES_SEGMENT),
                recent_segments.get(contact.contact_id, NO_SALES_SEGMENT),
            ),
        )
        for contact in contacts
    )


def list_abc_analytics(
    connection: duckdb.DuckDBPyConnection,
    *,
    limit: int = 50,
    offset: int = 0,
    date_from: date | None = None,
    date_to: date | None = None,
    compare_date_from: date | None = None,
    compare_date_to: date | None = None,
    deal_created_from: date | None = None,
    deal_created_to: date | None = None,
    category_id: int | None = None,
    contact_id: int | None = None,
    search: str | None = None,
    contact_type: str | None = None,
    segment: str | None = None,
    migration_priority: str | None = None,
    changed_only: bool = False,
    sort: AbcAnalyticsSortField = "base_revenue_usd",
    order: SortOrder = "desc",
) -> AbcAnalyticsPage:
    if sort not in ABC_ANALYTICS_SORT_FIELDS:
        raise ValueError(f"Unsupported ABC analytics sort field: {sort}")
    if order not in {"asc", "desc"}:
        raise ValueError(f"Unsupported ABC analytics sort order: {order}")

    target_enabled = compare_date_from is not None or compare_date_to is not None
    contacts = {contact.contact_id: contact for contact in _load_contacts(connection)}
    deals = tuple(deal for deal in _load_deal_facts(connection) if _date_in_period(deal.created_at.date(), deal_created_from, deal_created_to) and (category_id is None or deal.category_id == category_id))
    base_metrics = _abc_period_metrics(
        deals,
        date_from=date_from,
        date_to=date_to,
    )
    target_metrics = (
        _abc_period_metrics(
            deals,
            date_from=compare_date_from,
            date_to=compare_date_to,
        )
        if target_enabled
        else {}
    )
    contact_ids = {
        contact_id
        for contact_id, metric in base_metrics.items()
        if metric.revenue_usd > 0
    }
    if target_enabled:
        contact_ids.update(
            contact_id
            for contact_id, metric in target_metrics.items()
            if metric.revenue_usd > 0
        )

    rows = []
    for row_contact_id in sorted(contact_ids):
        contact = contacts.get(row_contact_id)
        if contact is None:
            continue
        base_metric = base_metrics.get(
            row_contact_id,
            _empty_abc_period_metric(),
        )
        target_metric = target_metrics.get(
            row_contact_id,
            _empty_abc_period_metric(),
        )
        target_segment = target_metric.segment if target_enabled else base_metric.segment
        segment_change = _abc_change(base_metric.segment, target_segment)
        row_migration_priority = _migration_priority(base_metric.segment, target_segment)
        rows.append(
            AbcAnalyticsRow(
                contact_id=contact.contact_id,
                contact_name=contact.contact_name,
                contact_type_normalized=contact.contact_type_normalized,
                base_revenue_usd=base_metric.revenue_usd,
                base_revenue_share_percent=base_metric.revenue_share_percent,
                base_cumulative_share_percent=base_metric.cumulative_share_percent,
                base_segment=base_metric.segment,
                base_won_deals_count=base_metric.won_deals_count,
                base_last_won_date=base_metric.last_won_date,
                target_revenue_usd=target_metric.revenue_usd,
                target_segment=target_segment,
                segment_change=segment_change,
                migration_priority=row_migration_priority,
                segment_changed=segment_change != "Без изменений",
            )
        )

    normalized_search = search.strip().lower() if search else None
    if normalized_search == "":
        normalized_search = None
    filtered_rows = tuple(
        row
        for row in rows
        if (contact_id is None or row.contact_id == contact_id)
        and (normalized_search is None or normalized_search in row.contact_name.lower())
        and (contact_type is None or row.contact_type_normalized == contact_type)
        and (segment is None or row.base_segment == segment)
        and (
            migration_priority is None
            or row.migration_priority == migration_priority
        )
        and (not changed_only or row.segment_changed)
    )
    sorted_rows = _sort_abc_analytics_rows(filtered_rows, sort=sort, order=order)

    return AbcAnalyticsPage(
        total=len(sorted_rows),
        limit=limit,
        offset=offset,
        base_total_revenue_usd=_money(
            sum((row.base_revenue_usd for row in filtered_rows), Decimal("0"))
        ),
        target_total_revenue_usd=_money(
            sum((row.target_revenue_usd for row in filtered_rows), Decimal("0"))
        ),
        base_segment_counts=_count_labels(
            row.base_segment for row in filtered_rows
        ),
        target_segment_counts=_count_labels(
            row.target_segment for row in filtered_rows
        ),
        migration_priority_counts=_count_labels(
            row.migration_priority for row in filtered_rows
        ),
        items=sorted_rows[offset : offset + limit],
    )


def get_rfm_report(
    connection: duckdb.DuckDBPyConnection,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    analysis_date: date | None = None,
) -> tuple[RfmRow, ...]:
    contacts = _load_contacts(connection)
    deals = _load_deal_facts(connection)
    anchor_date = analysis_date or date_to or _default_analysis_date(deals)
    won_deals = [
        deal
        for deal in deals
        if deal.status_group == "won"
        and deal.closed_at is not None
        and _date_in_period(deal.closed_at.date(), date_from, date_to)
    ]

    won_by_contact = {
        contact.contact_id: [
            deal for deal in won_deals if deal.analytical_contact_id == contact.contact_id
        ]
        for contact in contacts
    }
    metrics = {
        contact_id: _rfm_metric_values(contact_deals, anchor_date)
        for contact_id, contact_deals in won_by_contact.items()
    }
    active_metrics = {
        contact_id: metric
        for contact_id, metric in metrics.items()
        if metric is not None
    }
    r_scores = _score_values(
        [metric[0] for metric in active_metrics.values()],
        higher_is_better=False,
    )
    f_scores = _score_values(
        [metric[1] for metric in active_metrics.values()],
        higher_is_better=True,
    )
    m_scores = _score_values(
        [metric[2] for metric in active_metrics.values()],
        higher_is_better=True,
    )

    history_wins_by_contact = {
        contact.contact_id: [
            deal
            for deal in deals
            if deal.analytical_contact_id == contact.contact_id
            and deal.status_group == "won"
            and deal.closed_at is not None
        ]
        for contact in contacts
    }

    rows = []
    for contact in contacts:
        metric = metrics[contact.contact_id]
        if metric is None:
            rows.append(
                RfmRow(
                    contact_id=contact.contact_id,
                    contact_name=contact.contact_name,
                    contact_type_normalized=contact.contact_type_normalized,
                    region_normalized=contact.region_normalized,
                    recency_days=None,
                    frequency=0,
                    monetary_usd=Decimal("0.00"),
                    r_score=0,
                    f_score=0,
                    m_score=0,
                    rfm_code="000",
                    segment=NO_SALES_SEGMENT,
                    needs_reactivation=False,
                )
            )
            continue

        recency_days, frequency, monetary_usd = metric
        r_score = r_scores[recency_days]
        f_score = f_scores[frequency]
        m_score = m_scores[monetary_usd]
        rows.append(
            RfmRow(
                contact_id=contact.contact_id,
                contact_name=contact.contact_name,
                contact_type_normalized=contact.contact_type_normalized,
                region_normalized=contact.region_normalized,
                recency_days=recency_days,
                frequency=frequency,
                monetary_usd=monetary_usd,
                r_score=r_score,
                f_score=f_score,
                m_score=m_score,
                rfm_code=f"{r_score}{f_score}{m_score}",
                segment=_rfm_segment(r_score, f_score, m_score, frequency),
                needs_reactivation=_needs_reactivation(
                    history_wins_by_contact[contact.contact_id],
                    anchor_date,
                ),
            )
        )

    return tuple(rows)


def get_deal_cycle_report(
    connection: duckdb.DuckDBPyConnection,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> DealCycleReport:
    closed_deals = [
        deal
        for deal in _load_deal_facts(connection)
        if deal.status_group in {"won", "lost"}
        and deal.closed_at is not None
        and _date_in_period(deal.closed_at.date(), date_from, date_to)
    ]
    durations = [_cycle_days(deal) for deal in closed_deals]
    valid_pairs = [
        (deal, duration)
        for deal, duration in zip(closed_deals, durations, strict=True)
        if duration >= 0
    ]

    return DealCycleReport(
        overall=_cycle_metric("Все", [duration for _, duration in valid_pairs]),
        by_contact_type=_grouped_cycle_metrics(
            valid_pairs,
            lambda deal: deal.contact_type_normalized,
        ),
        by_region=_grouped_cycle_metrics(
            valid_pairs,
            lambda deal: deal.region_normalized,
        ),
    )


def list_stale_open_deals(
    connection: duckdb.DuckDBPyConnection,
    *,
    analysis_date: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[StaleDealRow, ...]:
    deals = _load_deal_facts(connection)
    anchor_date = analysis_date or date_to or _default_analysis_date(deals)
    won_cycle_pairs = [
        (deal, _cycle_days(deal))
        for deal in deals
        if deal.status_group == "won" and deal.closed_at is not None
    ]
    won_cycle_pairs = [
        (deal, duration) for deal, duration in won_cycle_pairs if duration >= 0
    ]
    overall_threshold = _percentile(
        [duration for _, duration in won_cycle_pairs],
        Decimal("0.75"),
    )
    type_thresholds = {
        group: _percentile(durations, Decimal("0.75"))
        for group, durations in _durations_by_group(
            won_cycle_pairs,
            lambda deal: deal.contact_type_normalized,
        ).items()
    }

    rows = []
    for deal in deals:
        if deal.status_group != "open":
            continue
        if not _date_in_period(deal.created_at.date(), date_from, date_to):
            continue

        days_open = (anchor_date - deal.created_at.date()).days
        threshold = type_thresholds.get(deal.contact_type_normalized, overall_threshold)
        if days_open <= threshold:
            continue

        rows.append(
            StaleDealRow(
                deal_id=deal.deal_id,
                deal_name=deal.deal_name,
                analytical_contact_id=deal.analytical_contact_id,
                analytical_contact_name=deal.analytical_contact_name,
                contact_type_normalized=deal.contact_type_normalized,
                region_normalized=deal.region_normalized,
                created_date=deal.created_at.date(),
                days_open=days_open,
                stale_threshold_days=threshold,
                days_over_threshold=days_open - threshold,
                amount_original=deal.amount_original,
                currency_original=deal.currency_original,
                amount_usd=deal.amount_usd,
            )
        )

    return tuple(sorted(rows, key=lambda row: (-row.days_over_threshold, row.deal_id)))


def get_concentration_report(
    connection: duckdb.DuckDBPyConnection,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> ConcentrationReport:
    revenue_by_contact = _revenue_by_contact(
        _load_deal_facts(connection),
        date_from=date_from,
        date_to=date_to,
    )
    ordered_revenues = sorted(revenue_by_contact.values(), reverse=True)
    total_revenue = _money(sum(ordered_revenues, Decimal("0")))

    entries = []
    for top_n in (1, 3, 5):
        top_revenue = _money(sum(ordered_revenues[:top_n], Decimal("0")))
        entries.append(
            ConcentrationEntry(
                top_n=top_n,
                revenue_usd=top_revenue,
                share_percent=_percent(top_revenue, total_revenue),
            )
        )

    return ConcentrationReport(
        total_revenue_usd=total_revenue,
        entries=tuple(entries),
    )


def get_type_region_analytics(
    connection: duckdb.DuckDBPyConnection,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> TypeRegionAnalyticsReport:
    contacts = _load_contacts(connection)
    deals = [
        deal
        for deal in _load_deal_facts(connection)
        if _date_in_period(_reporting_date(deal), date_from, date_to)
    ]

    return TypeRegionAnalyticsReport(
        type_rows=_group_type_region_rows(
            contacts,
            deals,
            key=lambda contact_type, region: (contact_type, None),
            group_name=lambda contact_type, region: contact_type,
        ),
        region_rows=_group_type_region_rows(
            contacts,
            deals,
            key=lambda contact_type, region: (None, region),
            group_name=lambda contact_type, region: region,
        ),
        matrix_rows=_group_type_region_rows(
            contacts,
            deals,
            key=lambda contact_type, region: (contact_type, region),
            group_name=lambda contact_type, region: f"{region} / {contact_type}",
        ),
    )


def _load_contacts(
    connection: duckdb.DuckDBPyConnection,
) -> tuple[_ContactFact, ...]:
    initialize_schema(connection)
    rows = connection.execute(
        """
        SELECT
            contact_id,
            contact_name,
            contact_type_normalized,
            region_normalized
        FROM normalized_contacts
        ORDER BY contact_id
        """
    ).fetchall()
    return tuple(
        _ContactFact(
            contact_id=row[0],
            contact_name=row[1],
            contact_type_normalized=row[2],
            region_normalized=row[3],
        )
        for row in rows
    )


def _load_deal_facts(
    connection: duckdb.DuckDBPyConnection,
) -> tuple[_DealFact, ...]:
    initialize_schema(connection)
    rates = _load_rates(connection)
    rows = connection.execute(
        """
        SELECT
            deal_id,
            deal_name,
            amount_original,
            currency_original,
            created_at,
            actual_closed_at,
            status_group,
            analytical_contact_id,
            analytical_contact_name,
            contact_type_normalized,
            region_normalized,
            kev_held,
            normalized_deals.category_id,
            categories.category_name
        FROM normalized_deals
        LEFT JOIN raw_deal_categories categories
          ON categories.category_id = normalized_deals.category_id
        ORDER BY deal_id
        """
    ).fetchall()

    deals = []
    for row in rows:
        created_at = _as_utc(row[4])
        closed_at = _as_utc(row[5]) if row[5] is not None else None
        target_date = (closed_at or created_at).date()
        source_rate_byn, usd_rate_byn, rate_date = _select_rate(
            rates,
            currency=row[3],
            target_date=target_date,
        )
        amount_original = Decimal(row[2])
        amount_usd = _money(amount_original * source_rate_byn / usd_rate_byn)
        deals.append(
            _DealFact(
                deal_id=row[0],
                deal_name=row[1],
                amount_original=amount_original,
                currency_original=row[3],
                created_at=created_at,
                closed_at=closed_at,
                status_group=row[6],
                analytical_contact_id=row[7],
                analytical_contact_name=row[8],
                contact_type_normalized=row[9],
                region_normalized=row[10],
                kev_held=row[11],
                category_id=int(row[12]),
                category_name=row[13],
                target_date=target_date,
                rate_date=rate_date,
                source_rate_byn=source_rate_byn,
                usd_rate_byn=usd_rate_byn,
                amount_usd=amount_usd,
            )
        )

    return tuple(deals)


def _load_rates(
    connection: duckdb.DuckDBPyConnection,
) -> dict[str, list[tuple[date, Decimal, Decimal]]]:
    rows = connection.execute(
        """
        SELECT currency, rate_date, source_rate_byn, usd_rate_byn
        FROM currency_rates
        ORDER BY currency, rate_date
        """
    ).fetchall()
    rates: dict[str, list[tuple[date, Decimal, Decimal]]] = {}
    for currency, rate_date, source_rate_byn, usd_rate_byn in rows:
        rates.setdefault(currency, []).append(
            (rate_date, Decimal(source_rate_byn), Decimal(usd_rate_byn))
        )
    return rates


def _select_rate(
    rates: dict[str, list[tuple[date, Decimal, Decimal]]],
    *,
    currency: str,
    target_date: date,
) -> tuple[Decimal, Decimal, date]:
    if currency == "USD":
        candidates = [row for row in rates.get(currency, ()) if row[0] <= target_date]
        if candidates:
            rate_date, source_rate_byn, usd_rate_byn = candidates[-1]
            return source_rate_byn, usd_rate_byn, rate_date
        return Decimal("1.00000000"), Decimal("1.00000000"), target_date

    candidates = [
        row for row in rates.get(currency, ()) if row[0] <= target_date
    ]
    if not candidates:
        raise AnalyticsDataUnavailableError(
            "Local currency rates are unavailable for the active dataset. "
            "Refresh local data and retry."
        )

    rate_date, source_rate_byn, usd_rate_byn = candidates[-1]
    return source_rate_byn, usd_rate_byn, rate_date


def _filtered_contacts(
    contacts: tuple[_ContactFact, ...],
    *,
    deals: list[_DealFact],
    search: str | None,
    contact_type: str | None,
    region: str | None,
    status: str | None,
    contact_id: int | None,
    require_matching_deals: bool,
) -> tuple[_ContactFact, ...]:
    filtered = []
    for contact in contacts:
        contact_deals = [
            deal for deal in deals if deal.analytical_contact_id == contact.contact_id
        ]
        if contact_id is not None and contact.contact_id != contact_id:
            continue
        if search and search.lower() not in contact.contact_name.lower():
            continue
        if contact_type and contact.contact_type_normalized != contact_type:
            continue
        if region and contact.region_normalized != region:
            continue
        if require_matching_deals and not contact_deals:
            continue
        if status and not any(deal.status_group == status for deal in contact_deals):
            continue
        filtered.append(contact)
    return tuple(filtered)


def _sort_contact_analytics_rows(
    rows: tuple[ContactAnalyticsRow, ...],
    *,
    sort: str,
    order: SortOrder,
) -> tuple[ContactAnalyticsRow, ...]:
    descending = order == "desc"

    def compare(left: ContactAnalyticsRow, right: ContactAnalyticsRow) -> int:
        left_value = _contact_analytics_sort_value(left, sort)
        right_value = _contact_analytics_sort_value(right, sort)

        if left_value is None and right_value is None:
            return _compare(left.contact_id, right.contact_id)
        if left_value is None:
            return 1
        if right_value is None:
            return -1

        result = _compare(left_value, right_value)
        if result and descending:
            return -result
        if result:
            return result
        return _compare(left.contact_id, right.contact_id)

    return tuple(sorted(rows, key=cmp_to_key(compare)))


def _sort_deal_analytics_rows(
    rows: tuple[DealAnalyticsRow, ...],
    *,
    sort: str,
    order: SortOrder,
) -> tuple[DealAnalyticsRow, ...]:
    descending = order == "desc"

    def compare(left: DealAnalyticsRow, right: DealAnalyticsRow) -> int:
        left_value = _deal_analytics_sort_value(left, sort)
        right_value = _deal_analytics_sort_value(right, sort)

        if left_value is None and right_value is None:
            return _compare(left.deal_id, right.deal_id)
        if left_value is None:
            return 1
        if right_value is None:
            return -1

        result = _compare(left_value, right_value)
        if result and descending:
            return -result
        if result:
            return result
        return _compare(left.deal_id, right.deal_id)

    return tuple(sorted(rows, key=cmp_to_key(compare)))


def _sort_abc_analytics_rows(
    rows: tuple[AbcAnalyticsRow, ...],
    *,
    sort: str,
    order: SortOrder,
) -> tuple[AbcAnalyticsRow, ...]:
    descending = order == "desc"

    def compare(left: AbcAnalyticsRow, right: AbcAnalyticsRow) -> int:
        left_value = _abc_analytics_sort_value(left, sort)
        right_value = _abc_analytics_sort_value(right, sort)

        if left_value is None and right_value is None:
            return _compare(left.contact_id, right.contact_id)
        if left_value is None:
            return 1
        if right_value is None:
            return -1

        result = _compare(left_value, right_value)
        if result and descending:
            return -result
        if result:
            return result
        return _compare(left.contact_id, right.contact_id)

    return tuple(sorted(rows, key=cmp_to_key(compare)))


def _contact_analytics_sort_value(
    row: ContactAnalyticsRow,
    sort: str,
) -> int | str | Decimal | date | None:
    value = getattr(row, sort)
    if isinstance(value, str):
        return value.lower()
    return value


def _deal_analytics_sort_value(
    row: DealAnalyticsRow,
    sort: str,
) -> int | str | Decimal | date | None:
    value = getattr(row, sort)
    if isinstance(value, str):
        return value.lower()
    return value


def _abc_analytics_sort_value(
    row: AbcAnalyticsRow,
    sort: str,
) -> int | str | Decimal | date | None:
    value = getattr(row, sort)
    if isinstance(value, str):
        return value.lower()
    return value


def _compare(left: object, right: object) -> int:
    if left < right:  # type: ignore[operator]
        return -1
    if left > right:  # type: ignore[operator]
        return 1
    return 0


def _build_contact_analytics_row(
    contact: _ContactFact,
    deals: list[_DealFact],
) -> ContactAnalyticsRow:
    contact_deals = [
        deal for deal in deals if deal.analytical_contact_id == contact.contact_id
    ]
    won_deals = [
        deal
        for deal in contact_deals
        if deal.status_group == "won" and deal.closed_at is not None
    ]
    open_deals = [deal for deal in contact_deals if deal.status_group == "open"]
    lost_deals = [deal for deal in contact_deals if deal.status_group == "lost"]
    budget_usd = _money(sum((deal.amount_usd for deal in contact_deals), Decimal("0")))
    budget_in_work_usd = _money(
        sum((deal.amount_usd for deal in open_deals), Decimal("0"))
    )
    lost_budget_usd = _money(sum((deal.amount_usd for deal in lost_deals), Decimal("0")))
    revenue_usd = _money(sum((deal.amount_usd for deal in won_deals), Decimal("0")))
    won_dates = sorted(deal.closed_at.date() for deal in won_deals if deal.closed_at)
    deal_dates = [
        deal_at.date()
        for deal in contact_deals
        for deal_at in (deal.created_at, deal.closed_at)
        if deal_at is not None
    ]

    return ContactAnalyticsRow(
        contact_id=contact.contact_id,
        contact_name=contact.contact_name,
        contact_type_normalized=contact.contact_type_normalized,
        region_normalized=contact.region_normalized,
        total_deals_count=len(contact_deals),
        won_deals_count=len(won_deals),
        open_deals_count=len(open_deals),
        lost_deals_count=len(lost_deals),
        budget_usd=budget_usd,
        budget_in_work_usd=budget_in_work_usd,
        lost_budget_usd=lost_budget_usd,
        revenue_usd=revenue_usd,
        estimated_profit_usd=_profit(revenue_usd),
        first_won_date=won_dates[0] if won_dates else None,
        last_won_date=won_dates[-1] if won_dates else None,
        latest_deal_date=max(deal_dates) if deal_dates else None,
        has_sales=revenue_usd > 0,
        average_check_usd=_average_check(contact_deals),
        average_cycle_days=_average_cycle(contact_deals),
    )


def _build_deal_analytics_row(deal: _DealFact) -> DealAnalyticsRow:
    budget_usd = _money(deal.amount_usd)
    return DealAnalyticsRow(
        deal_id=deal.deal_id,
        deal_name=deal.deal_name,
        status_group=deal.status_group,
        contact_type_normalized=deal.contact_type_normalized,
        region_normalized=deal.region_normalized,
        budget_usd=budget_usd,
        estimated_profit_usd=_profit(budget_usd) if deal.status_group == "won" else Decimal("0.00"),
        created_date=deal.created_at.date(),
        closed_date=deal.closed_at.date() if deal.closed_at else None,
        kev_held=deal.kev_held,
        category_id=deal.category_id,
        category_name=deal.category_name,
        cycle_days=_cycle_days(deal),
    )


def _cycle_days(deal: _DealFact) -> int | None:
    if deal.status_group not in {"won", "lost"} or deal.closed_at is None:
        return None
    days = (deal.closed_at.date() - deal.created_at.date()).days
    return days if days >= 0 else None


def _average_cycle(deals: list[_DealFact] | tuple[_DealFact, ...]) -> Decimal | None:
    values = [days for deal in deals if (days := _cycle_days(deal)) is not None]
    if not values:
        return None
    return (Decimal(sum(values)) / Decimal(len(values))).quantize(PERCENT_QUANT, rounding=ROUND_HALF_UP)


def _average_check(deals: list[_DealFact] | tuple[_DealFact, ...]) -> Decimal | None:
    won = [deal for deal in deals if deal.status_group == "won"]
    if not won:
        return None
    return _money(sum((deal.amount_usd for deal in won), Decimal("0")) / Decimal(len(won)))


def _selection_summary(deals: list[_DealFact]) -> dict[str, object]:
    won = [deal for deal in deals if deal.status_group == "won"]
    open_deals = [deal for deal in deals if deal.status_group == "open"]
    lost = [deal for deal in deals if deal.status_group == "lost"]
    revenue = _money(sum((deal.amount_usd for deal in won), Decimal("0")))
    return {
        "filtered_total_deals_count": len(deals), "filtered_won_deals_count": len(won),
        "filtered_open_deals_count": len(open_deals), "filtered_lost_deals_count": len(lost),
        "filtered_budget_usd": _money(sum((deal.amount_usd for deal in deals), Decimal("0"))),
        "filtered_budget_in_work_usd": _money(sum((deal.amount_usd for deal in open_deals), Decimal("0"))),
        "filtered_lost_budget_usd": _money(sum((deal.amount_usd for deal in lost), Decimal("0"))),
        "filtered_revenue_usd": revenue, "filtered_estimated_profit_usd": _profit(revenue),
        "filtered_average_check_usd": _average_check(deals), "filtered_average_cycle_days": _average_cycle(deals),
    }


def _kev_conversion_group(counts: tuple[int, int, int]) -> KevConversionGroup:
    closed_count, won_count, lost_count = counts
    return KevConversionGroup(
        closed_deals_count=closed_count,
        won_deals_count=won_count,
        lost_deals_count=lost_count,
        conversion_percent=(
            None
            if closed_count == 0
            else _percent(Decimal(won_count), Decimal(closed_count))
        ),
    )


def _abc_period_metrics(
    deals: tuple[_DealFact, ...],
    *,
    date_from: date | None,
    date_to: date | None,
) -> dict[int, AbcPeriodMetric]:
    won_by_contact: dict[int, list[_DealFact]] = {}
    for deal in deals:
        if (
            deal.analytical_contact_id is None
            or deal.status_group != "won"
            or deal.closed_at is None
            or not _date_in_period(deal.closed_at.date(), date_from, date_to)
        ):
            continue
        won_by_contact.setdefault(deal.analytical_contact_id, []).append(deal)

    revenue_by_contact = {
        contact_id: _money(sum((deal.amount_usd for deal in contact_deals), Decimal("0")))
        for contact_id, contact_deals in won_by_contact.items()
    }
    total_revenue = sum(
        (revenue for revenue in revenue_by_contact.values() if revenue > 0),
        Decimal("0"),
    )
    if total_revenue <= 0:
        return {
            contact_id: AbcPeriodMetric(
                revenue_usd=_money(revenue),
                revenue_share_percent=Decimal("0.0"),
                cumulative_share_percent=Decimal("0.0"),
                segment=NO_SALES_SEGMENT,
                won_deals_count=len(contact_deals),
                last_won_date=max(
                    deal.closed_at.date() for deal in contact_deals if deal.closed_at
                ),
            )
            for contact_id, contact_deals in won_by_contact.items()
            for revenue in (revenue_by_contact[contact_id],)
        }

    metrics: dict[int, AbcPeriodMetric] = {}
    cumulative = Decimal("0")
    for contact_id, revenue in sorted(
        (
            (contact_id, revenue)
            for contact_id, revenue in revenue_by_contact.items()
            if revenue > 0
        ),
        key=lambda row: (-row[1], row[0]),
    ):
        prior_share = cumulative / total_revenue
        if prior_share < Decimal("0.80"):
            segment = "A"
        elif prior_share < Decimal("0.95"):
            segment = "B"
        else:
            segment = "C"
        cumulative += revenue
        contact_deals = won_by_contact[contact_id]
        metrics[contact_id] = AbcPeriodMetric(
            revenue_usd=_money(revenue),
            revenue_share_percent=_percent(revenue, total_revenue),
            cumulative_share_percent=_percent(cumulative, total_revenue),
            segment=segment,
            won_deals_count=len(contact_deals),
            last_won_date=max(
                deal.closed_at.date() for deal in contact_deals if deal.closed_at
            ),
        )
    return metrics


def _empty_abc_period_metric() -> AbcPeriodMetric:
    return AbcPeriodMetric(
        revenue_usd=Decimal("0.00"),
        revenue_share_percent=Decimal("0.0"),
        cumulative_share_percent=Decimal("0.0"),
        segment=NO_SALES_SEGMENT,
        won_deals_count=0,
        last_won_date=None,
    )


def _revenue_by_contact(
    deals: tuple[_DealFact, ...],
    *,
    date_from: date | None,
    date_to: date | None,
) -> dict[int, Decimal]:
    revenue: dict[int, Decimal] = {}
    for deal in deals:
        if (
            deal.analytical_contact_id is None
            or deal.status_group != "won"
            or deal.closed_at is None
            or not _date_in_period(deal.closed_at.date(), date_from, date_to)
        ):
            continue
        revenue[deal.analytical_contact_id] = _money(
            revenue.get(deal.analytical_contact_id, Decimal("0")) + deal.amount_usd
        )
    return revenue


def _classify_abc(revenue_by_contact: dict[int, Decimal]) -> dict[int, str]:
    positive_rows = [
        (contact_id, revenue)
        for contact_id, revenue in revenue_by_contact.items()
        if revenue > 0
    ]
    total_revenue = sum((revenue for _, revenue in positive_rows), Decimal("0"))
    if total_revenue <= 0:
        return {}

    segments = {}
    cumulative = Decimal("0")
    for contact_id, revenue in sorted(positive_rows, key=lambda row: (-row[1], row[0])):
        prior_share = cumulative / total_revenue
        if prior_share < Decimal("0.80"):
            segment = "A"
        elif prior_share < Decimal("0.95"):
            segment = "B"
        else:
            segment = "C"
        segments[contact_id] = segment
        cumulative += revenue

    return segments


def _abc_change(abc_full: str, abc_12m: str) -> str:
    if abc_full == abc_12m:
        return "Без изменений"
    return f"{abc_full} -> {abc_12m}"


def _migration_priority(abc_full: str, abc_12m: str) -> str:
    if abc_full == abc_12m:
        return "без изменений"
    if abc_full == "A" and abc_12m in {NO_SALES_SEGMENT, "C"}:
        return "срочно"
    if (abc_full, abc_12m) in {("A", "B"), ("B", NO_SALES_SEGMENT)}:
        return "важно"
    if (abc_full, abc_12m) in {("B", "C"), ("C", NO_SALES_SEGMENT)}:
        return "наблюдать"
    if abc_full in {"B", "C"} and abc_12m == "A":
        return "развивать"
    if abc_full == NO_SALES_SEGMENT and abc_12m == "A":
        return "закрепить"
    return "изменение"


def _rfm_metric_values(
    deals: list[_DealFact],
    analysis_date: date,
) -> tuple[int, int, Decimal] | None:
    if not deals:
        return None

    last_won_date = max(deal.closed_at.date() for deal in deals if deal.closed_at)
    recency_days = max((analysis_date - last_won_date).days, 0)
    frequency = len(deals)
    monetary_usd = _money(sum((deal.amount_usd for deal in deals), Decimal("0")))
    return recency_days, frequency, monetary_usd


def _score_values(
    values: list[int] | list[Decimal],
    *,
    higher_is_better: bool,
) -> dict[int, int] | dict[Decimal, int]:
    unique_values = sorted(set(values))
    if not unique_values:
        return {}
    if len(unique_values) == 1:
        return {unique_values[0]: 5}

    scores = {}
    for index, value in enumerate(unique_values, start=1):
        ascending_score = max(1, min(5, ceil(index * 5 / len(unique_values))))
        scores[value] = ascending_score if higher_is_better else 6 - ascending_score
    return scores


def _rfm_segment(
    r_score: int,
    f_score: int,
    m_score: int,
    frequency: int,
) -> str:
    if r_score >= 4 and f_score >= 4 and m_score >= 4:
        return "Лучшие"
    if r_score <= 2 and (f_score >= 4 or m_score >= 4):
        return "Ценные под риском"
    if frequency == 1 and r_score >= 4:
        return "Новые"
    if r_score >= 3 and f_score >= 3:
        return "Лояльные"
    if frequency == 1:
        return "Одноразовые"
    return "Остальные"


def _needs_reactivation(
    all_won_deals: list[_DealFact],
    analysis_date: date,
) -> bool:
    if len(all_won_deals) < 2:
        return False
    last_won_date = max(deal.closed_at.date() for deal in all_won_deals if deal.closed_at)
    return (analysis_date - last_won_date).days > REACTIVATION_DAYS_THRESHOLD


def _count_labels(labels) -> dict[str, int]:
    counts: dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def _grouped_cycle_metrics(
    pairs: list[tuple[_DealFact, int]],
    group_key,
) -> tuple[CycleMetricRow, ...]:
    grouped = _durations_by_group(pairs, group_key)
    return tuple(
        _cycle_metric(group_name, durations)
        for group_name, durations in sorted(grouped.items())
    )


def _durations_by_group(
    pairs: list[tuple[_DealFact, int]],
    group_key,
) -> dict[str, list[int]]:
    grouped: dict[str, list[int]] = {}
    for deal, duration in pairs:
        grouped.setdefault(group_key(deal), []).append(duration)
    return grouped


def _cycle_metric(group_name: str, durations: list[int]) -> CycleMetricRow:
    if not durations:
        return CycleMetricRow(
            group_name=group_name,
            deals_count=0,
            average_days=0.0,
            median_days=0.0,
            p75_days=0,
            p90_days=0,
        )

    sorted_durations = sorted(durations)
    return CycleMetricRow(
        group_name=group_name,
        deals_count=len(sorted_durations),
        average_days=round(sum(sorted_durations) / len(sorted_durations), 2),
        median_days=_median(sorted_durations),
        p75_days=_percentile(sorted_durations, Decimal("0.75")),
        p90_days=_percentile(sorted_durations, Decimal("0.90")),
    )


def _group_type_region_rows(
    contacts: tuple[_ContactFact, ...],
    deals: list[_DealFact],
    *,
    key,
    group_name,
) -> tuple[TypeRegionAnalyticsRow, ...]:
    groups = {
        key(contact.contact_type_normalized, contact.region_normalized)
        for contact in contacts
    }
    groups.update(
        key(deal.contact_type_normalized, deal.region_normalized)
        for deal in deals
    )

    rows = []
    for contact_type, region in sorted(
        groups,
        key=lambda row: (row[0] or "", row[1] or ""),
    ):
        group_contacts = [
            contact
            for contact in contacts
            if key(contact.contact_type_normalized, contact.region_normalized)
            == (contact_type, region)
        ]
        group_deals = [
            deal
            for deal in deals
            if key(deal.contact_type_normalized, deal.region_normalized)
            == (contact_type, region)
        ]
        won_deals = [deal for deal in group_deals if deal.status_group == "won"]
        revenue = _money(sum((deal.amount_usd for deal in won_deals), Decimal("0")))
        rows.append(
            TypeRegionAnalyticsRow(
                group_name=group_name(
                    contact_type or UNDEFINED_VALUE,
                    region or UNDEFINED_VALUE,
                ),
                contact_type_normalized=contact_type,
                region_normalized=region,
                contact_count=len(group_contacts),
                total_deals_count=len(group_deals),
                won_deals_count=len(won_deals),
                open_deals_count=sum(deal.status_group == "open" for deal in group_deals),
                lost_deals_count=sum(deal.status_group == "lost" for deal in group_deals),
                revenue_usd=revenue,
                estimated_profit_usd=_profit(revenue),
            )
        )

    return tuple(rows)


def _cycle_days(deal: _DealFact) -> int:
    if deal.closed_at is None:
        return 0
    return (deal.closed_at.date() - deal.created_at.date()).days


def _median(values: list[int]) -> float:
    midpoint = len(values) // 2
    if len(values) % 2:
        return float(values[midpoint])
    return round((values[midpoint - 1] + values[midpoint]) / 2, 2)


def _percentile(values: list[int], percentile: Decimal) -> int:
    if not values:
        return 0
    sorted_values = sorted(values)
    index = max(0, ceil(len(sorted_values) * float(percentile)) - 1)
    return sorted_values[index]


def _reporting_date(deal: _DealFact) -> date:
    if deal.status_group == "open":
        return deal.created_at.date()
    return (deal.closed_at or deal.created_at).date()


def _date_in_period(
    value: date | None,
    date_from: date | None,
    date_to: date | None,
) -> bool:
    if value is None:
        return False
    if date_from is not None and value < date_from:
        return False
    if date_to is not None and value > date_to:
        return False
    return True


def _default_analysis_date(deals: tuple[_DealFact, ...]) -> date:
    if not deals:
        return datetime.now(timezone.utc).date()
    return max(_reporting_date(deal) for deal in deals)


def _one_year_before(value: date) -> date:
    try:
        return value.replace(year=value.year - 1)
    except ValueError:
        return value.replace(year=value.year - 1, day=28)


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def _profit(revenue_usd: Decimal) -> Decimal:
    return _money(revenue_usd * Decimal("0.50"))


def _percent(part: Decimal, total: Decimal) -> Decimal:
    if total <= 0:
        return Decimal("0.0")
    return (part / total * Decimal("100")).quantize(
        PERCENT_QUANT,
        rounding=ROUND_HALF_UP,
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
