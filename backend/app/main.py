from datetime import date

from fastapi import FastAPI, Query

from app.api.models import (
    AbcResponse,
    BitrixContactDealVerificationResponse,
    BitrixDiscoveryResponse,
    ConcentrationReportResponse,
    ContactDealDiagnosticResponse,
    ContactAnalyticsPageResponse,
    ContactSummaryPageResponse,
    DatasetStorageStatusResponse,
    DatasetProfileResponse,
    DealCycleReportResponse,
    ExplicitContactDealDiagnosticResponse,
    ExplicitContactDealReconciliationResponse,
    FilterMetadataResponse,
    LocalDataRefreshResponse,
    PipelineStatusResponse,
    RfmResponse,
    StaleDealResponse,
    TypeRegionAnalyticsReportResponse,
)
from app.bitrix.client import BitrixClient, BitrixClientError
from app.bitrix.discovery import BitrixDiscoveryResult, discover_bitrix_metadata
from app.bitrix.ingestion import (
    BITRIX_MANUAL_DATASET_KIND,
    BITRIX_MANUAL_DATASET_NAME,
    get_latest_bitrix_ingestion_status,
    run_bitrix_manual_ingestion,
    store_bitrix_ingestion_error,
)
from app.core.config import get_settings
from app.local_database import get_connection
from app.pipeline.currency_rates import NbrbRateClient
from app.pipeline.manual_refresh import run_full_bitrix_manual_refresh
from app.pipeline.synthetic import get_latest_pipeline_status, run_synthetic_pipeline
from app.reports.analytics import (
    get_abc_report,
    get_concentration_report,
    get_deal_cycle_report,
    get_rfm_report,
    get_type_region_analytics,
    list_contact_analytics,
    list_stale_open_deals,
)
from app.reports.contact_deal_diagnostics import (
    get_contact_deal_diagnostic,
    get_explicit_contact_deal_diagnostic,
    reconcile_explicit_contact_deals,
    verify_explicit_bitrix_contact_deals,
    verify_bitrix_contact_deals,
)
from app.reports.local import get_filter_metadata, list_contact_summaries
from app.reports.profile import get_dataset_profile
from app.storage.status import get_dataset_storage_status


settings = get_settings()

app = FastAPI(title=settings.name, debug=settings.debug)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.env}


@app.get("/api/sync/status", response_model=PipelineStatusResponse)
def sync_status() -> PipelineStatusResponse:
    status = get_latest_pipeline_status(get_connection())
    if status is None:
        return PipelineStatusResponse(
            run_id=None,
            dataset_name="synthetic-fixture",
            dataset_kind="local_synthetic",
            state="not_run",
            message="Local synthetic fixture pipeline has not been run.",
            raw_contacts_count=0,
            raw_deals_count=0,
            raw_links_count=0,
            normalized_contacts_count=0,
            normalized_deals_count=0,
            started_at=None,
            finished_at=None,
            snapshot_paths=(),
            is_active=False,
        )

    return PipelineStatusResponse.model_validate(status)


@app.post("/api/sync/run", response_model=PipelineStatusResponse)
def run_local_synthetic_sync() -> PipelineStatusResponse:
    status = run_synthetic_pipeline(
        get_connection(),
        data_dir=settings.data_dir,
    )
    return PipelineStatusResponse.model_validate(status)


@app.get("/api/datasets/status", response_model=DatasetStorageStatusResponse)
def dataset_status() -> DatasetStorageStatusResponse:
    status = get_dataset_storage_status(get_connection())
    return DatasetStorageStatusResponse.model_validate(status)


@app.get("/api/datasets/profile", response_model=DatasetProfileResponse)
def dataset_profile() -> DatasetProfileResponse:
    profile = get_dataset_profile(get_connection())
    return DatasetProfileResponse.model_validate(profile)


@app.get("/api/bitrix/discovery", response_model=BitrixDiscoveryResponse)
def bitrix_discovery() -> BitrixDiscoveryResponse:
    try:
        client = _build_bitrix_client()
        result = discover_bitrix_metadata(
            client,
            contact_type_field=settings.bitrix_contact_type_field,
        )
    except (BitrixClientError, ValueError) as exc:
        result = BitrixDiscoveryResult(
            state="error",
            message=str(exc),
            configured_contact_type_field=settings.bitrix_contact_type_field,
            contact_type_field_exists=None,
            contact_fields_count=0,
            deal_fields_count=0,
            allowed_contact_fields=(),
            allowed_deal_fields=(),
            candidate_contact_type_fields=(),
            missing_required_contact_fields=(),
            missing_required_deal_fields=(),
        )
    return BitrixDiscoveryResponse.model_validate(result)


@app.get(
    "/api/internal/diagnostics/contacts/{contact_id}/deal-links",
    response_model=ContactDealDiagnosticResponse,
)
def contact_deal_diagnostic(contact_id: int) -> ContactDealDiagnosticResponse:
    diagnostic = get_contact_deal_diagnostic(get_connection(), contact_id)
    return ContactDealDiagnosticResponse.model_validate(diagnostic)


@app.post(
    "/api/internal/diagnostics/contacts/{contact_id}/verify-bitrix-deals",
    response_model=BitrixContactDealVerificationResponse,
)
def verify_contact_deals_in_bitrix(
    contact_id: int,
) -> BitrixContactDealVerificationResponse:
    client = _build_bitrix_client()
    verification = verify_bitrix_contact_deals(
        get_connection(),
        client=client,
        contact_id=contact_id,
    )
    return BitrixContactDealVerificationResponse.model_validate(verification)


@app.get(
    "/api/internal/diagnostics/contacts/{contact_id}/explicit-deals",
    response_model=ExplicitContactDealDiagnosticResponse,
)
def explicit_contact_deal_diagnostic(
    contact_id: int,
    deal_ids: list[int] = Query(...),
) -> ExplicitContactDealDiagnosticResponse:
    diagnostic = get_explicit_contact_deal_diagnostic(
        get_connection(),
        contact_id=contact_id,
        deal_ids=tuple(deal_ids),
    )
    return ExplicitContactDealDiagnosticResponse.model_validate(diagnostic)


@app.post(
    "/api/internal/diagnostics/contacts/{contact_id}/verify-bitrix-explicit-deals",
    response_model=BitrixContactDealVerificationResponse,
)
def verify_explicit_contact_deals_in_bitrix(
    contact_id: int,
    deal_ids: list[int] = Query(...),
) -> BitrixContactDealVerificationResponse:
    client = _build_bitrix_client()
    verification = verify_explicit_bitrix_contact_deals(
        client=client,
        contact_id=contact_id,
        deal_ids=tuple(deal_ids),
    )
    return BitrixContactDealVerificationResponse.model_validate(verification)


@app.post(
    "/api/internal/reconciliation/contacts/{contact_id}/explicit-deals",
    response_model=ExplicitContactDealReconciliationResponse,
)
def reconcile_explicit_contact_deals_endpoint(
    contact_id: int,
    deal_ids: list[int] = Query(...),
) -> ExplicitContactDealReconciliationResponse:
    client = _build_bitrix_client()
    result = reconcile_explicit_contact_deals(
        get_connection(),
        client=client,
        contact_id=contact_id,
        deal_ids=tuple(deal_ids),
    )
    return ExplicitContactDealReconciliationResponse.model_validate(result)


@app.get("/api/bitrix/sync/status", response_model=PipelineStatusResponse)
def bitrix_sync_status() -> PipelineStatusResponse:
    status = get_latest_bitrix_ingestion_status(get_connection())
    if status is None:
        return PipelineStatusResponse(
            run_id=None,
            dataset_name=BITRIX_MANUAL_DATASET_NAME,
            dataset_kind=BITRIX_MANUAL_DATASET_KIND,
            state="not_run",
            message="Manual Bitrix ingestion has not been run.",
            raw_contacts_count=0,
            raw_deals_count=0,
            raw_links_count=0,
            normalized_contacts_count=0,
            normalized_deals_count=0,
            started_at=None,
            finished_at=None,
            snapshot_paths=(),
            is_active=False,
        )

    return PipelineStatusResponse.model_validate(status)


@app.post("/api/bitrix/sync/run", response_model=PipelineStatusResponse)
def run_manual_bitrix_sync() -> PipelineStatusResponse:
    try:
        client = _build_bitrix_client()
    except (BitrixClientError, ValueError) as exc:
        status = store_bitrix_ingestion_error(get_connection(), str(exc))
        return PipelineStatusResponse.model_validate(status)

    status = run_bitrix_manual_ingestion(
        get_connection(),
        client=client,
        contact_type_field=settings.bitrix_contact_type_field,
        data_dir=settings.data_dir,
    )
    return PipelineStatusResponse.model_validate(status)


@app.post("/api/local/refresh-data", response_model=LocalDataRefreshResponse)
def refresh_local_data() -> LocalDataRefreshResponse:
    try:
        client = _build_bitrix_client()
    except (BitrixClientError, ValueError) as exc:
        status = store_bitrix_ingestion_error(get_connection(), str(exc))
        return LocalDataRefreshResponse(
            status=PipelineStatusResponse.model_validate(status),
            message=status.message,
            contact_type_rules_count=0,
            active_contact_type_rules_count=0,
            currency_rate_rows_loaded=0,
            currency_rate_currencies=(),
        )

    result = run_full_bitrix_manual_refresh(
        get_connection(),
        client=client,
        contact_type_field=settings.bitrix_contact_type_field,
        data_dir=settings.data_dir,
        rate_client=NbrbRateClient(),
    )
    return LocalDataRefreshResponse(
        status=PipelineStatusResponse.model_validate(result.status),
        message=result.status.message,
        contact_type_rules_count=result.contact_type_rules_count,
        active_contact_type_rules_count=result.active_contact_type_rules_count,
        currency_rate_rows_loaded=result.currency_rate_rows_loaded,
        currency_rate_currencies=result.currency_rate_currencies,
    )


@app.get("/api/meta/filters", response_model=FilterMetadataResponse)
def meta_filters() -> FilterMetadataResponse:
    filters = get_filter_metadata(get_connection())
    return FilterMetadataResponse.model_validate(filters)


def _build_bitrix_client() -> BitrixClient:
    return BitrixClient(
        settings.bitrix_webhook_url,
        page_size=settings.bitrix_page_size,
    )


@app.get("/api/reports/contacts", response_model=ContactSummaryPageResponse)
def report_contacts(
    limit: int = Query(default=50, gt=0, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = None,
    contact_type: str | None = None,
    region: str | None = None,
    status: str | None = None,
) -> ContactSummaryPageResponse:
    page = list_contact_summaries(
        get_connection(),
        limit=limit,
        offset=offset,
        search=search,
        contact_type=contact_type,
        region=region,
        status=status,
    )
    return ContactSummaryPageResponse.model_validate(page)


@app.get(
    "/api/reports/contacts/analytics",
    response_model=ContactAnalyticsPageResponse,
)
def report_contact_analytics(
    limit: int = Query(default=50, gt=0, le=100),
    offset: int = Query(default=0, ge=0),
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    contact_type: str | None = None,
    region: str | None = None,
    status: str | None = None,
) -> ContactAnalyticsPageResponse:
    page = list_contact_analytics(
        get_connection(),
        limit=limit,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
        search=search,
        contact_type=contact_type,
        region=region,
        status=status,
    )
    return ContactAnalyticsPageResponse.model_validate(page)


@app.get("/api/reports/abc", response_model=tuple[AbcResponse, ...])
def report_abc(analysis_date: date | None = None) -> tuple[AbcResponse, ...]:
    return tuple(
        AbcResponse.model_validate(row)
        for row in get_abc_report(get_connection(), analysis_date=analysis_date)
    )


@app.get("/api/reports/rfm", response_model=tuple[RfmResponse, ...])
def report_rfm(
    date_from: date | None = None,
    date_to: date | None = None,
    analysis_date: date | None = None,
) -> tuple[RfmResponse, ...]:
    return tuple(
        RfmResponse.model_validate(row)
        for row in get_rfm_report(
            get_connection(),
            date_from=date_from,
            date_to=date_to,
            analysis_date=analysis_date,
        )
    )


@app.get("/api/reports/stale-deals", response_model=tuple[StaleDealResponse, ...])
def report_stale_deals(
    analysis_date: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[StaleDealResponse, ...]:
    return tuple(
        StaleDealResponse.model_validate(row)
        for row in list_stale_open_deals(
            get_connection(),
            analysis_date=analysis_date,
            date_from=date_from,
            date_to=date_to,
        )
    )


@app.get("/api/reports/deal-cycle", response_model=DealCycleReportResponse)
def report_deal_cycle(
    date_from: date | None = None,
    date_to: date | None = None,
) -> DealCycleReportResponse:
    return DealCycleReportResponse.model_validate(
        get_deal_cycle_report(
            get_connection(),
            date_from=date_from,
            date_to=date_to,
        )
    )


@app.get("/api/reports/concentration", response_model=ConcentrationReportResponse)
def report_concentration(
    date_from: date | None = None,
    date_to: date | None = None,
) -> ConcentrationReportResponse:
    return ConcentrationReportResponse.model_validate(
        get_concentration_report(
            get_connection(),
            date_from=date_from,
            date_to=date_to,
        )
    )


@app.get("/api/reports/type-region", response_model=TypeRegionAnalyticsReportResponse)
@app.get("/api/reports/types-regions", response_model=TypeRegionAnalyticsReportResponse)
def report_type_region(
    date_from: date | None = None,
    date_to: date | None = None,
) -> TypeRegionAnalyticsReportResponse:
    return TypeRegionAnalyticsReportResponse.model_validate(
        get_type_region_analytics(
            get_connection(),
            date_from=date_from,
            date_to=date_to,
        )
    )
