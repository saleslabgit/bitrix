from datetime import datetime
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
