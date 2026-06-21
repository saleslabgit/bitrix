from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PipelineStatusResponse(ApiModel):
    dataset_name: str
    dataset_kind: str
    state: str
    message: str
    raw_contacts_count: int
    raw_deals_count: int
    raw_links_count: int
    normalized_contacts_count: int
    normalized_deals_count: int
    started_at: datetime | None
    finished_at: datetime | None


class BitrixDiscoveryResponse(ApiModel):
    state: str
    message: str
    configured_contact_type_field: str | None
    contact_type_field_exists: bool | None
    contact_fields_count: int
    deal_fields_count: int
    allowed_contact_fields: tuple[str, ...]
    allowed_deal_fields: tuple[str, ...]
    candidate_contact_type_fields: tuple[str, ...]
    missing_required_contact_fields: tuple[str, ...]
    missing_required_deal_fields: tuple[str, ...]


class FilterMetadataResponse(ApiModel):
    contact_types: tuple[str, ...]
    regions: tuple[str, ...]
    statuses: tuple[str, ...]
    min_created_at: datetime | None
    max_created_at: datetime | None
    min_closed_at: datetime | None
    max_closed_at: datetime | None


class ContactSummaryResponse(ApiModel):
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


class ContactSummaryPageResponse(ApiModel):
    total: int
    limit: int = Field(gt=0, le=100)
    offset: int = Field(ge=0)
    items: tuple[ContactSummaryResponse, ...]


class ContactAnalyticsResponse(ApiModel):
    contact_id: int
    contact_name: str
    contact_type_normalized: str
    region_normalized: str
    total_deals_count: int
    won_deals_count: int
    open_deals_count: int
    lost_deals_count: int
    revenue_usd: Decimal
    estimated_profit_usd: Decimal
    first_won_date: date | None
    last_won_date: date | None
    latest_deal_date: date | None
    has_sales: bool


class ContactAnalyticsPageResponse(ApiModel):
    total: int
    limit: int = Field(gt=0, le=100)
    offset: int = Field(ge=0)
    items: tuple[ContactAnalyticsResponse, ...]


class AbcResponse(ApiModel):
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


class RfmResponse(ApiModel):
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


class StaleDealResponse(ApiModel):
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


class CycleMetricResponse(ApiModel):
    group_name: str
    deals_count: int
    average_days: float
    median_days: float
    p75_days: int
    p90_days: int


class DealCycleReportResponse(ApiModel):
    overall: CycleMetricResponse
    by_contact_type: tuple[CycleMetricResponse, ...]
    by_region: tuple[CycleMetricResponse, ...]


class ConcentrationEntryResponse(ApiModel):
    top_n: int
    revenue_usd: Decimal
    share_percent: Decimal


class ConcentrationReportResponse(ApiModel):
    total_revenue_usd: Decimal
    entries: tuple[ConcentrationEntryResponse, ...]


class TypeRegionAnalyticsResponse(ApiModel):
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


class TypeRegionAnalyticsReportResponse(ApiModel):
    type_rows: tuple[TypeRegionAnalyticsResponse, ...]
    region_rows: tuple[TypeRegionAnalyticsResponse, ...]
    matrix_rows: tuple[TypeRegionAnalyticsResponse, ...]
