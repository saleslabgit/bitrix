from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb

from app.bitrix.client import BitrixClient
from app.bitrix.ingestion import run_bitrix_manual_ingestion
from app.pipeline.approved_contact_type_rules import replace_contact_type_rules
from app.pipeline.currency_rates import (
    CurrencyRateLoadResult,
    NbrbRateClient,
    load_currency_rates_for_raw_deals,
)
from app.pipeline.normalization import normalize_local_data
from app.pipeline.synthetic import PipelineStatus


@dataclass(frozen=True)
class ManualDataRefreshResult:
    status: PipelineStatus
    contact_type_rules_count: int = 0
    active_contact_type_rules_count: int = 0
    currency_rate_rows_loaded: int = 0
    currency_rate_currencies: tuple[str, ...] = ()


@dataclass
class _RefreshDetails:
    contact_type_rules_count: int = 0
    active_contact_type_rules_count: int = 0
    currency_rates: CurrencyRateLoadResult | None = None


def run_full_bitrix_manual_refresh(
    connection: duckdb.DuckDBPyConnection,
    *,
    client: BitrixClient,
    contact_type_field: str | None,
    data_dir: Path | None = None,
    rate_client: NbrbRateClient | None = None,
    rate_as_of_date: date | None = None,
) -> ManualDataRefreshResult:
    details = _RefreshDetails()

    def finalize(connection: duckdb.DuckDBPyConnection) -> None:
        details.contact_type_rules_count = replace_contact_type_rules(connection)
        normalize_local_data(connection)
        details.active_contact_type_rules_count = connection.execute(
            "SELECT COUNT(*) FROM contact_type_rules WHERE is_active = true"
        ).fetchone()[0]
        details.currency_rates = load_currency_rates_for_raw_deals(
            connection,
            client=rate_client,
            as_of_date=rate_as_of_date,
            manage_transaction=False,
        )

    status = run_bitrix_manual_ingestion(
        connection,
        client=client,
        contact_type_field=contact_type_field,
        data_dir=data_dir,
        finalize_local_data=finalize,
        success_message="Manual Bitrix refresh completed.",
    )

    if status.state != "success":
        return ManualDataRefreshResult(status=status)

    return ManualDataRefreshResult(
        status=status,
        contact_type_rules_count=details.contact_type_rules_count,
        active_contact_type_rules_count=details.active_contact_type_rules_count,
        currency_rate_rows_loaded=(
            details.currency_rates.rows_loaded if details.currency_rates is not None else 0
        ),
        currency_rate_currencies=(
            details.currency_rates.currencies if details.currency_rates is not None else ()
        ),
    )
