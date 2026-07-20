from datetime import date
from http.cookies import SimpleCookie
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Path, Query, Request, Response, status as http_status
from fastapi.responses import JSONResponse

from app.api.models import (
    AbcAnalyticsPageResponse,
    AbcResponse,
    AuthLoginRequest,
    AuthSessionResponse,
    BitrixItemDealContactVerificationResponse,
    BitrixContactDealVerificationResponse,
    BitrixDiscoveryResponse,
    ConcentrationReportResponse,
    ContactDealDiagnosticResponse,
    ContactAnalyticsPageResponse,
    ContactSummaryPageResponse,
    ContactWonRevenueSeriesResponse,
    DatasetStorageStatusResponse,
    DatasetProfileResponse,
    DealAnalyticsPageResponse,
    DealCycleReportResponse,
    ExplicitContactDealDiagnosticResponse,
    ExplicitContactDealReconciliationResponse,
    FilterMetadataResponse,
    LocalDataRefreshResponse,
    KevConversionReportResponse,
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
from app.core.auth import (
    AUTH_COOKIE_NAME,
    build_auth_status,
    create_session_cookie_value,
    validate_credentials,
    validate_session_cookie,
)
from app.local_database import connection_scope
from app.pipeline.currency_rates import NbrbRateClient
from app.pipeline.manual_refresh import run_full_bitrix_manual_refresh
from app.pipeline.synthetic import get_latest_pipeline_status, run_synthetic_pipeline
from app.reports.analytics import (
    AnalyticsDataUnavailableError,
    ContactNotFoundError,
    get_abc_report,
    get_contact_won_revenue_series,
    get_concentration_report,
    get_deal_cycle_report,
    get_rfm_report,
    get_kev_conversion_report,
    get_type_region_analytics,
    list_contact_analytics,
    list_abc_analytics,
    list_deal_analytics,
    list_stale_open_deals,
)
from app.reports.contact_deal_diagnostics import (
    get_contact_deal_diagnostic,
    get_explicit_contact_deal_diagnostic,
    reconcile_explicit_contact_deals,
    verify_bitrix_item_list_contact_links,
    verify_explicit_bitrix_contact_deals,
    verify_bitrix_contact_deals,
)
from app.reports.local import get_filter_metadata, list_contact_summaries
from app.reports.profile import get_dataset_profile
from app.storage.status import get_dataset_storage_status


settings = get_settings()

app = FastAPI(title=settings.name, debug=settings.debug)

ContactAnalyticsSortQuery = Literal[
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
    "last_won_date",
    "latest_deal_date",
]
DealAnalyticsSortQuery = Literal[
    "deal_id",
    "deal_name",
    "status_group",
    "contact_type_normalized",
    "region_normalized",
    "budget_usd",
    "estimated_profit_usd",
    "created_date",
    "closed_date",
]
AbcAnalyticsSortQuery = Literal[
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
SortOrderQuery = Literal["asc", "desc"]


class ApiAuthMiddleware:
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not _path_requires_auth(scope["path"]):
            await self.asgi_app(scope, receive, send)
            return

        cookie_value = _read_cookie(scope.get("headers", []), AUTH_COOKIE_NAME)
        session = validate_session_cookie(settings, cookie_value)
        if session is None:
            response = JSONResponse(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required."},
            )
            await response(scope, receive, send)
            return

        await self.asgi_app(scope, receive, send)


app.add_middleware(ApiAuthMiddleware)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.env}


@app.get("/api/auth/session", response_model=AuthSessionResponse)
async def auth_session(request: Request) -> AuthSessionResponse:
    session = validate_session_cookie(settings, request.cookies.get(AUTH_COOKIE_NAME))
    return AuthSessionResponse.model_validate(build_auth_status(settings, session))


@app.post("/api/auth/login", response_model=AuthSessionResponse)
async def auth_login(
    payload: AuthLoginRequest,
    response: Response,
) -> AuthSessionResponse:
    if not settings.auth_enabled:
        return AuthSessionResponse.model_validate(build_auth_status(settings, None))

    if not validate_credentials(settings, payload.username, payload.password):
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    cookie_value = create_session_cookie_value(settings, payload.username)
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=cookie_value,
        max_age=settings.auth_session_ttl_seconds,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )
    session = validate_session_cookie(settings, cookie_value)
    return AuthSessionResponse.model_validate(build_auth_status(settings, session))


@app.post("/api/auth/logout", response_model=AuthSessionResponse)
async def auth_logout(response: Response) -> AuthSessionResponse:
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
    )
    return AuthSessionResponse.model_validate(build_auth_status(settings, None))


def _path_requires_auth(path: str) -> bool:
    return settings.auth_enabled and path.startswith("/api/") and not path.startswith("/api/auth/")


def _read_cookie(headers: list[tuple[bytes, bytes]], name: str) -> str | None:
    cookie_header = None
    for header_name, header_value in headers:
        if header_name.lower() == b"cookie":
            cookie_header = header_value.decode("latin-1")
            break

    if not cookie_header:
        return None

    cookies = SimpleCookie()
    cookies.load(cookie_header)
    morsel = cookies.get(name)
    return morsel.value if morsel is not None else None


@app.get("/api/sync/status", response_model=PipelineStatusResponse)
def sync_status() -> PipelineStatusResponse:
    with connection_scope() as connection:
        status = get_latest_pipeline_status(connection)
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
    with connection_scope() as connection:
        status = run_synthetic_pipeline(
            connection,
            data_dir=settings.data_dir,
        )
    return PipelineStatusResponse.model_validate(status)


@app.get("/api/datasets/status", response_model=DatasetStorageStatusResponse)
def dataset_status() -> DatasetStorageStatusResponse:
    with connection_scope() as connection:
        status = get_dataset_storage_status(connection)
    return DatasetStorageStatusResponse.model_validate(status)


@app.get("/api/datasets/profile", response_model=DatasetProfileResponse)
def dataset_profile() -> DatasetProfileResponse:
    with connection_scope() as connection:
        profile = get_dataset_profile(connection)
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
    with connection_scope() as connection:
        diagnostic = get_contact_deal_diagnostic(connection, contact_id)
    return ContactDealDiagnosticResponse.model_validate(diagnostic)


@app.post(
    "/api/internal/diagnostics/contacts/{contact_id}/verify-bitrix-deals",
    response_model=BitrixContactDealVerificationResponse,
)
def verify_contact_deals_in_bitrix(
    contact_id: int,
) -> BitrixContactDealVerificationResponse:
    client = _build_bitrix_client()
    with connection_scope() as connection:
        verification = verify_bitrix_contact_deals(
            connection,
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
    with connection_scope() as connection:
        diagnostic = get_explicit_contact_deal_diagnostic(
            connection,
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
    "/api/internal/diagnostics/contacts/{contact_id}/verify-bitrix-item-deals",
    response_model=BitrixItemDealContactVerificationResponse,
)
def verify_contact_deals_in_bitrix_items(
    contact_id: int,
    deal_ids: list[int] = Query(...),
) -> BitrixItemDealContactVerificationResponse:
    client = _build_bitrix_client()
    verification = verify_bitrix_item_list_contact_links(
        client=client,
        contact_id=contact_id,
        deal_ids=tuple(deal_ids),
    )
    return BitrixItemDealContactVerificationResponse.model_validate(verification)


@app.post(
    "/api/internal/reconciliation/contacts/{contact_id}/explicit-deals",
    response_model=ExplicitContactDealReconciliationResponse,
)
def reconcile_explicit_contact_deals_endpoint(
    contact_id: int,
    deal_ids: list[int] = Query(...),
) -> ExplicitContactDealReconciliationResponse:
    client = _build_bitrix_client()
    with connection_scope() as connection:
        result = reconcile_explicit_contact_deals(
            connection,
            client=client,
            contact_id=contact_id,
            deal_ids=tuple(deal_ids),
        )
    return ExplicitContactDealReconciliationResponse.model_validate(result)


@app.get("/api/bitrix/sync/status", response_model=PipelineStatusResponse)
def bitrix_sync_status() -> PipelineStatusResponse:
    with connection_scope() as connection:
        status = get_latest_bitrix_ingestion_status(connection)
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
        with connection_scope() as connection:
            status = store_bitrix_ingestion_error(connection, str(exc))
        return PipelineStatusResponse.model_validate(status)

    with connection_scope() as connection:
        status = run_bitrix_manual_ingestion(
            connection,
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
        with connection_scope() as connection:
            status = store_bitrix_ingestion_error(connection, str(exc))
        return LocalDataRefreshResponse(
            status=PipelineStatusResponse.model_validate(status),
            message=status.message,
            contact_type_rules_count=0,
            active_contact_type_rules_count=0,
            currency_rate_rows_loaded=0,
            currency_rate_currencies=(),
        )

    with connection_scope() as connection:
        result = run_full_bitrix_manual_refresh(
            connection,
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
    with connection_scope() as connection:
        filters = get_filter_metadata(connection)
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
    with connection_scope() as connection:
        page = list_contact_summaries(
            connection,
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
    deal_created_from: date | None = None,
    deal_created_to: date | None = None,
    search: str | None = None,
    contact_type: str | None = None,
    region: str | None = None,
    status: str | None = None,
    contact_id: Annotated[int | None, Query(gt=0)] = None,
    sort: ContactAnalyticsSortQuery = "contact_id",
    order: SortOrderQuery = "asc",
) -> ContactAnalyticsPageResponse:
    try:
        with connection_scope() as connection:
            page = list_contact_analytics(
                connection,
                limit=limit,
                offset=offset,
                date_from=date_from,
                date_to=date_to,
                deal_created_from=deal_created_from,
                deal_created_to=deal_created_to,
                search=search,
                contact_type=contact_type,
                region=region,
                status=status,
                contact_id=contact_id,
                sort=sort,
                order=order,
            )
    except AnalyticsDataUnavailableError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return ContactAnalyticsPageResponse.model_validate(page)


@app.get(
    "/api/reports/contacts/{contact_id}/won-revenue-series",
    response_model=ContactWonRevenueSeriesResponse,
)
def report_contact_won_revenue_series(
    contact_id: Annotated[int, Path(gt=0)],
    date_from: date | None = None,
    date_to: date | None = None,
) -> ContactWonRevenueSeriesResponse:
    try:
        with connection_scope() as connection:
            series = get_contact_won_revenue_series(
                connection,
                contact_id=contact_id,
                date_from=date_from,
                date_to=date_to,
            )
    except ContactNotFoundError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AnalyticsDataUnavailableError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return ContactWonRevenueSeriesResponse.model_validate(series)


@app.get(
    "/api/reports/deals/analytics",
    response_model=DealAnalyticsPageResponse,
)
def report_deal_analytics(
    limit: int = Query(default=50, gt=0, le=100),
    offset: int = Query(default=0, ge=0),
    deal_id: Annotated[int | None, Query(gt=0)] = None,
    client_id: Annotated[int | None, Query(gt=0)] = None,
    status: str | None = None,
    contact_type: str | None = None,
    region: str | None = None,
    client_search: str | None = None,
    deal_created_from: date | None = None,
    deal_created_to: date | None = None,
    kev_held: bool | None = None,
    sort: DealAnalyticsSortQuery = "deal_id",
    order: SortOrderQuery = "asc",
) -> DealAnalyticsPageResponse:
    try:
        with connection_scope() as connection:
            page = list_deal_analytics(
                connection,
                limit=limit,
                offset=offset,
                deal_id=deal_id,
                client_id=client_id,
                status=status,
                contact_type=contact_type,
                region=region,
                client_search=client_search,
                deal_created_from=deal_created_from,
                deal_created_to=deal_created_to,
                kev_held=kev_held,
                sort=sort,
                order=order,
            )
    except AnalyticsDataUnavailableError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return DealAnalyticsPageResponse.model_validate(page)


@app.get(
    "/api/reports/kev-conversion/analytics",
    response_model=KevConversionReportResponse,
)
def report_kev_conversion_analytics(
    date_from: date | None = None,
    date_to: date | None = None,
    contact_type: str | None = None,
) -> KevConversionReportResponse:
    with connection_scope() as connection:
        report = get_kev_conversion_report(
            connection,
            date_from=date_from,
            date_to=date_to,
            contact_type=contact_type,
        )
    return KevConversionReportResponse.model_validate(report)


@app.get(
    "/api/reports/abc/analytics",
    response_model=AbcAnalyticsPageResponse,
)
def report_abc_analytics(
    limit: int = Query(default=50, gt=0, le=100),
    offset: int = Query(default=0, ge=0),
    contact_id: Annotated[int | None, Query(gt=0)] = None,
    search: str | None = None,
    contact_type: str | None = None,
    segment: str | None = None,
    migration_priority: str | None = None,
    changed_only: bool = False,
    date_from: date | None = None,
    date_to: date | None = None,
    compare_date_from: date | None = None,
    compare_date_to: date | None = None,
    sort: AbcAnalyticsSortQuery = "base_revenue_usd",
    order: SortOrderQuery = "desc",
) -> AbcAnalyticsPageResponse:
    try:
        with connection_scope() as connection:
            page = list_abc_analytics(
                connection,
                limit=limit,
                offset=offset,
                contact_id=contact_id,
                search=search,
                contact_type=contact_type,
                segment=segment,
                migration_priority=migration_priority,
                changed_only=changed_only,
                date_from=date_from,
                date_to=date_to,
                compare_date_from=compare_date_from,
                compare_date_to=compare_date_to,
                sort=sort,
                order=order,
            )
    except AnalyticsDataUnavailableError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return AbcAnalyticsPageResponse.model_validate(page)


@app.get("/api/reports/abc", response_model=tuple[AbcResponse, ...])
def report_abc(analysis_date: date | None = None) -> tuple[AbcResponse, ...]:
    with connection_scope() as connection:
        return tuple(
            AbcResponse.model_validate(row)
            for row in get_abc_report(connection, analysis_date=analysis_date)
        )


@app.get("/api/reports/rfm", response_model=tuple[RfmResponse, ...])
def report_rfm(
    date_from: date | None = None,
    date_to: date | None = None,
    analysis_date: date | None = None,
) -> tuple[RfmResponse, ...]:
    with connection_scope() as connection:
        return tuple(
            RfmResponse.model_validate(row)
            for row in get_rfm_report(
                connection,
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
    with connection_scope() as connection:
        return tuple(
            StaleDealResponse.model_validate(row)
            for row in list_stale_open_deals(
                connection,
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
    with connection_scope() as connection:
        return DealCycleReportResponse.model_validate(
            get_deal_cycle_report(
                connection,
                date_from=date_from,
                date_to=date_to,
            )
        )


@app.get("/api/reports/concentration", response_model=ConcentrationReportResponse)
def report_concentration(
    date_from: date | None = None,
    date_to: date | None = None,
) -> ConcentrationReportResponse:
    with connection_scope() as connection:
        return ConcentrationReportResponse.model_validate(
            get_concentration_report(
                connection,
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
    with connection_scope() as connection:
        return TypeRegionAnalyticsReportResponse.model_validate(
            get_type_region_analytics(
                connection,
                date_from=date_from,
                date_to=date_to,
            )
        )
