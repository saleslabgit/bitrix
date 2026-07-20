from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AuthLoginRequest(BaseModel):
    username: str
    password: str


class AuthSessionResponse(BaseModel):
    auth_enabled: bool
    authenticated: bool
    username: str | None


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PipelineStatusResponse(ApiModel):
    run_id: str | None = None
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
    snapshot_paths: tuple[str, ...] = ()
    is_active: bool = False


class DatasetStorageStatusResponse(ApiModel):
    active_dataset: PipelineStatusResponse | None
    latest_run: PipelineStatusResponse | None


class LocalDataRefreshResponse(ApiModel):
    status: PipelineStatusResponse
    message: str
    contact_type_rules_count: int
    active_contact_type_rules_count: int
    currency_rate_rows_loaded: int
    currency_rate_currencies: tuple[str, ...] = ()


class DatasetProfileRunResponse(ApiModel):
    run_id: str | None = None
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
    is_active: bool = False


class TablePresenceResponse(ApiModel):
    table_name: str
    exists: bool


class CountByLabelResponse(ApiModel):
    label: str
    count: int


class CountByStageResponse(ApiModel):
    category_id: int | None
    stage_id: str
    count: int


class CountByTypeRegionResponse(ApiModel):
    contact_type_normalized: str
    region_normalized: str
    count: int


class DateRangeResponse(ApiModel):
    min_created_at: datetime | None
    max_created_at: datetime | None
    min_closed_at: datetime | None
    max_closed_at: datetime | None


class NormalizationProfileResponse(ApiModel):
    normalized_contacts_undefined_type_count: int
    normalized_contacts_undefined_region_count: int
    normalized_deals_undefined_type_count: int
    normalized_deals_undefined_region_count: int
    normalized_contacts_type_mostly_undefined: bool
    normalized_contacts_region_mostly_undefined: bool
    normalized_deals_type_mostly_undefined: bool
    normalized_deals_region_mostly_undefined: bool


class ContactTypeRulesProfileResponse(ApiModel):
    active_rules_count: int
    raw_values_without_active_rule: tuple[str, ...]


class LinkIntegrityProfileResponse(ApiModel):
    deals_without_analytical_contact_count: int
    deals_without_local_link_count: int
    links_missing_contact_count: int
    links_missing_deal_count: int


class DatasetProfileResponse(ApiModel):
    active_dataset: DatasetProfileRunResponse | None
    latest_run: DatasetProfileRunResponse | None
    snapshot_count: int
    expected_tables: tuple[TablePresenceResponse, ...]
    contact_type_raw_counts: tuple[CountByLabelResponse, ...]
    distinct_contact_type_raw_values_count: int
    contacts_missing_type_count: int
    link_integrity: LinkIntegrityProfileResponse
    status_group_counts: tuple[CountByLabelResponse, ...]
    currency_counts: tuple[CountByLabelResponse, ...]
    category_stage_counts: tuple[CountByStageResponse, ...]
    deal_date_range: DateRangeResponse
    normalization: NormalizationProfileResponse
    contact_type_rules: ContactTypeRulesProfileResponse
    normalized_deal_type_counts: tuple[CountByLabelResponse, ...]
    normalized_deal_region_counts: tuple[CountByLabelResponse, ...]
    normalized_deal_type_region_counts: tuple[CountByTypeRegionResponse, ...]


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


class LocalLinkedDealDiagnosticResponse(ApiModel):
    deal_id: int
    raw_deal_exists: bool
    status_group: str | None
    is_primary: bool
    analytical_contact_id: int | None
    analytical_contact_name: str | None
    analytical_contact_type: str | None


class ContactDealDiagnosticResponse(ApiModel):
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
    linked_deals: tuple[LocalLinkedDealDiagnosticResponse, ...]
    explanation: str


class BitrixContactDealVerificationResponse(ApiModel):
    contact_id: int
    supplied_deal_ids: tuple[int, ...]
    bitrix_deal_ids: tuple[int, ...]
    relations: tuple["BitrixExplicitDealRelationResponse", ...]
    confirmed_contact_deal_ids: tuple[int, ...]
    methods_used: tuple[str, ...]
    explanation: str


class ExplicitDealLocalDiagnosticResponse(ApiModel):
    deal_id: int
    raw_deal_exists: bool
    has_contact_link: bool
    linked_contact_ids: tuple[int, ...]
    analytical_contact_id: int | None
    analytical_contact_name: str | None
    analytical_contact_type: str | None
    counts_for_contact: bool
    divergence_reason: str


class ExplicitContactDealDiagnosticResponse(ApiModel):
    contact_id: int
    supplied_deal_ids: tuple[int, ...]
    deals: tuple[ExplicitDealLocalDiagnosticResponse, ...]


class BitrixExplicitDealRelationResponse(ApiModel):
    deal_id: int
    bitrix_deal_exists: bool
    linked_contact_ids: tuple[int, ...]
    has_contact_link: bool
    is_primary: bool
    sort_order: int | None
    role_id: str | None
    divergence_reason: str


class ExplicitContactDealReconciliationResponse(ApiModel):
    contact_id: int
    supplied_deal_ids: tuple[int, ...]
    confirmed_contact_deal_ids: tuple[int, ...]
    inserted_raw_deal_ids: tuple[int, ...]
    inserted_link_deal_ids: tuple[int, ...]
    skipped_deal_ids: tuple[int, ...]
    status: PipelineStatusResponse
    local_after: ExplicitContactDealDiagnosticResponse
    methods_used: tuple[str, ...]
    explanation: str


class BitrixItemDealContactRowResponse(ApiModel):
    deal_id: int
    returned_contact_ids: tuple[int, ...]
    has_contact_link: bool


class BitrixItemDealContactVerificationResponse(ApiModel):
    contact_id: int
    supplied_deal_ids: tuple[int, ...]
    selected_fields: tuple[str, ...]
    contact_related_fields: tuple[str, ...]
    returned_deal_ids: tuple[int, ...]
    rows: tuple[BitrixItemDealContactRowResponse, ...]
    methods_used: tuple[str, ...]
    is_complete_for_contact: bool
    explanation: str


class FilterMetadataResponse(ApiModel):
    contact_types: tuple[str, ...]
    regions: tuple[str, ...]
    statuses: tuple[str, ...]
    min_created_at: datetime | None
    max_created_at: datetime | None
    min_closed_at: datetime | None
    max_closed_at: datetime | None
    categories: tuple["DealCategoryOptionResponse", ...] = ()


class DealCategoryOptionResponse(ApiModel):
    category_id: int
    category_name: str


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


class ContactAnalyticsPageResponse(ApiModel):
    total: int
    limit: int = Field(gt=0, le=100)
    offset: int = Field(ge=0)
    items: tuple[ContactAnalyticsResponse, ...]
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


class ContactWonRevenuePointResponse(ApiModel):
    closed_date: date
    revenue_usd: Decimal
    won_deals_count: int


class ContactWonRevenueSeriesResponse(ApiModel):
    contact_id: int
    contact_name: str
    date_from: date | None
    date_to: date | None
    total_revenue_usd: Decimal
    won_deals_count: int
    points: tuple[ContactWonRevenuePointResponse, ...]


class DealAnalyticsResponse(ApiModel):
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


class DealAnalyticsPageResponse(ApiModel):
    total: int
    limit: int = Field(gt=0, le=100)
    offset: int = Field(ge=0)
    filtered_budget_usd: Decimal
    filtered_revenue_usd: Decimal
    filtered_estimated_profit_usd: Decimal
    filtered_won_deals_count: int
    filtered_open_deals_count: int
    filtered_lost_deals_count: int
    filtered_average_check_usd: Decimal | None
    filtered_average_cycle_days: Decimal | None
    items: tuple[DealAnalyticsResponse, ...]


class KevConversionGroupResponse(ApiModel):
    closed_deals_count: int
    won_deals_count: int
    lost_deals_count: int
    conversion_percent: Decimal | None


class KevConversionReportResponse(ApiModel):
    with_kev: KevConversionGroupResponse
    without_kev: KevConversionGroupResponse
    conversion_difference_percentage_points: Decimal | None
    date_from: date | None
    date_to: date | None


class AbcAnalyticsResponse(ApiModel):
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


class AbcAnalyticsPageResponse(ApiModel):
    total: int
    limit: int = Field(gt=0, le=100)
    offset: int = Field(ge=0)
    base_total_revenue_usd: Decimal
    target_total_revenue_usd: Decimal
    base_segment_counts: dict[str, int]
    target_segment_counts: dict[str, int]
    migration_priority_counts: dict[str, int]
    items: tuple[AbcAnalyticsResponse, ...]


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
