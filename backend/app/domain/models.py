from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import AliasChoices, AwareDatetime, BaseModel, ConfigDict, Field


StatusGroup = Literal["won", "open", "lost"]


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ContactSnapshot(DomainModel):
    contact_id: int = Field(gt=0)
    contact_name: str = Field(min_length=1)
    contact_type_raw: str | None = None


class DealSnapshot(DomainModel):
    deal_id: int = Field(gt=0)
    deal_name: str = Field(min_length=1)
    amount_original: Decimal
    currency_original: str = Field(min_length=1)
    created_at: AwareDatetime
    planned_close_at: AwareDatetime | None = None
    actual_closed_at: AwareDatetime | None = Field(
        default=None,
        validation_alias=AliasChoices("actual_closed_at", "closed_at"),
    )
    stage_id: str = Field(min_length=1)
    category_id: int | None = None
    status_group: StatusGroup
    kev_held: bool = False

    @property
    def closed_at(self) -> AwareDatetime | None:
        """Deprecated domain compatibility alias; always factual."""
        return self.actual_closed_at


class DealStageHistorySnapshot(DomainModel):
    history_id: int = Field(gt=0)
    deal_id: int = Field(gt=0)
    type_id: int
    created_at: AwareDatetime
    category_id: int = Field(ge=0)
    stage_id: str = Field(min_length=1)
    stage_semantic_id: Literal["S", "F", "P"]


class DealContactLink(DomainModel):
    deal_id: int = Field(gt=0)
    contact_id: int = Field(gt=0)
    is_primary: bool = False
    sort_order: int | None = None
    role_id: str | None = None


class StageSnapshot(DomainModel):
    stage_id: str = Field(min_length=1)
    category_id: int | None = None
    status_group: StatusGroup


class DealCategorySnapshot(DomainModel):
    category_id: int = Field(ge=0)
    category_name: str = Field(min_length=1)
    sort_order: int | None = None


class ContactTypeRule(DomainModel):
    raw_value: str = Field(min_length=1)
    normalized_type: str = Field(min_length=1)
    priority: int = Field(ge=0)
    region: str = Field(min_length=1)
    is_active: bool = True


class CurrencyRateSnapshot(DomainModel):
    currency: str = Field(min_length=1)
    rate_date: date
    source_rate_byn: Decimal = Field(gt=0)
    usd_rate_byn: Decimal = Field(gt=0)
    rate_source: Literal["NBRB"] = "NBRB"
    rate_fetched_at: AwareDatetime
