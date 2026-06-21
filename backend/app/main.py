from datetime import date

from fastapi import FastAPI, Query

from app.api.models import (
    AbcResponse,
    BitrixDiscoveryResponse,
    ConcentrationReportResponse,
    ContactAnalyticsPageResponse,
    ContactSummaryPageResponse,
    DatasetStorageStatusResponse,
    DealCycleReportResponse,
    FilterMetadataResponse,
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
from app.reports.local import get_filter_metadata, list_contact_summaries
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
