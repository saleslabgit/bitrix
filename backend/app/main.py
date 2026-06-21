from fastapi import FastAPI, Query

from app.api.models import (
    ContactSummaryPageResponse,
    FilterMetadataResponse,
    PipelineStatusResponse,
)
from app.core.config import get_settings
from app.local_database import get_connection
from app.pipeline.synthetic import get_latest_pipeline_status, run_synthetic_pipeline
from app.reports.local import get_filter_metadata, list_contact_summaries


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
        )

    return PipelineStatusResponse.model_validate(status)


@app.post("/api/sync/run", response_model=PipelineStatusResponse)
def run_local_synthetic_sync() -> PipelineStatusResponse:
    status = run_synthetic_pipeline(get_connection())
    return PipelineStatusResponse.model_validate(status)


@app.get("/api/meta/filters", response_model=FilterMetadataResponse)
def meta_filters() -> FilterMetadataResponse:
    filters = get_filter_metadata(get_connection())
    return FilterMetadataResponse.model_validate(filters)


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
