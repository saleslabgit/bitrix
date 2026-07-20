from datetime import date

import duckdb

from app import main
from app.local_database import reset_connection

from app.main import (
    bitrix_discovery,
    bitrix_sync_status,
    refresh_local_data,
    run_manual_bitrix_sync,
)
from app.pipeline.approved_contact_type_rules import APPROVED_CONTACT_TYPE_RULES
from app.pipeline.currency_rates import NbrbRateClient
from app.pipeline.manual_refresh import run_full_bitrix_manual_refresh
from app.pipeline.synthetic import run_synthetic_pipeline
from app.storage.status import get_active_dataset_run


def test_bitrix_api_surfaces_fail_safely_without_credentials(monkeypatch, tmp_path) -> None:
    reset_connection()
    monkeypatch.setattr(main.settings, "data_dir", tmp_path)
    monkeypatch.setattr(main.settings, "duckdb_path", tmp_path / "api-bitrix.duckdb")
    monkeypatch.setattr(main.settings, "bitrix_webhook_url", None)
    monkeypatch.setattr(main.settings, "bitrix_contact_type_field", None)

    try:
        discovery = bitrix_discovery()
        run_status = run_manual_bitrix_sync()
        refresh_status = refresh_local_data()
        latest_status = bitrix_sync_status()
    finally:
        reset_connection()

    assert discovery.state == "error"
    assert "webhook URL is not configured" in discovery.message
    assert run_status.dataset_kind == "bitrix_manual"
    assert run_status.state == "error"
    assert "webhook URL is not configured" in run_status.message
    assert refresh_status.status.dataset_kind == "bitrix_manual"
    assert refresh_status.status.state == "error"
    assert "webhook URL is not configured" in refresh_status.message
    assert latest_status.state == "error"


def test_full_manual_refresh_runs_bitrix_rules_normalization_and_rates() -> None:
    with duckdb.connect(database=":memory:") as connection:
        result = run_full_bitrix_manual_refresh(
            connection,
            client=RefreshBitrixClient(),
            contact_type_field="UF_CRM_CONTACT_TYPE",
            rate_client=NbrbRateClient(transport=_nbrb_transport),
        )
        normalized_contact = connection.execute(
            """
            SELECT contact_type_normalized, region_normalized
            FROM normalized_contacts
            WHERE contact_id = 10
            """
        ).fetchone()
        rate_count = connection.execute("SELECT COUNT(*) FROM currency_rates").fetchone()[0]

    assert result.status.state == "success"
    assert result.status.is_active is True
    assert result.status.raw_contacts_count == 1
    assert result.status.normalized_deals_count == 1
    assert result.contact_type_rules_count == len(APPROVED_CONTACT_TYPE_RULES)
    assert result.active_contact_type_rules_count == 13
    assert result.currency_rate_rows_loaded == 2
    assert result.currency_rate_currencies == ("USD",)
    assert normalized_contact == ("Дизайнер", "Беларусь")
    assert rate_count == 2


def test_full_manual_refresh_preparation_failure_keeps_previous_active_dataset() -> None:
    with duckdb.connect(database=":memory:") as connection:
        previous_status = run_synthetic_pipeline(connection)

        result = run_full_bitrix_manual_refresh(
            connection,
            client=UnsupportedCurrencyBitrixClient(),
            contact_type_field="UF_CRM_CONTACT_TYPE",
            rate_client=NbrbRateClient(transport=_nbrb_transport),
        )
        active_status = get_active_dataset_run(connection)
        normalized_deal_count = connection.execute(
            "SELECT COUNT(*) FROM normalized_deals"
        ).fetchone()[0]

    assert result.status.state == "error"
    assert "Unsupported currencies" in result.status.message
    assert result.status.is_active is False
    assert active_status.run_id == previous_status.run_id
    assert active_status.dataset_kind == "local_synthetic"
    assert normalized_deal_count == previous_status.normalized_deals_count


def test_full_manual_refresh_empty_currency_rows_returns_safe_error_status() -> None:
    with duckdb.connect(database=":memory:") as connection:
        previous_status = run_synthetic_pipeline(connection)

        result = run_full_bitrix_manual_refresh(
            connection,
            client=NoCommonRateRowsBitrixClient(),
            contact_type_field="UF_CRM_CONTACT_TYPE",
            rate_client=NbrbRateClient(transport=_no_common_rate_transport),
            rate_as_of_date=date(2025, 1, 1),
        )
        active_status = get_active_dataset_run(connection)
        normalized_deal_count = connection.execute(
            "SELECT COUNT(*) FROM normalized_deals"
        ).fetchone()[0]

    assert result.status.state == "error"
    assert "No currency rate rows were loaded" in result.status.message
    assert "executemany" not in result.status.message
    assert result.status.is_active is False
    assert active_status.run_id == previous_status.run_id
    assert normalized_deal_count == previous_status.normalized_deals_count


class RefreshBitrixClient:
    def list_deal_stage_history(self, deal_ids: list[int]) -> list[dict[str, object]]:
        return [
            {
                "ID": "500",
                "TYPE_ID": "3",
                "OWNER_ID": str(deal_id),
                "CREATED_TIME": "2025-01-02T10:00:00+00:00",
                "CATEGORY_ID": "0",
                "STAGE_ID": "WON",
                "STAGE_SEMANTIC_ID": "S",
            }
            for deal_id in deal_ids
        ]

    def list_deal_categories(self) -> list[dict[str, object]]:
        return [{"ID": "0", "NAME": "Sales", "SORT": "10"}]

    def list_stages(self, *, category_id: int = 0) -> list[dict[str, object]]:
        assert category_id == 0
        return [
            {
                "STATUS_ID": "WON",
                "CATEGORY_ID": "0",
                "SEMANTICS": "S",
                "NAME": "Won",
            }
        ]

    def list_contacts(self, contact_type_field: str | None) -> list[dict[str, object]]:
        assert contact_type_field == "UF_CRM_CONTACT_TYPE"
        return [
            {
                "ID": "10",
                "NAME": "Ada",
                "LAST_NAME": "Lovelace",
                "UF_CRM_CONTACT_TYPE": "61",
            }
        ]

    def list_deal_items(self) -> list[dict[str, object]]:
        return [
            {
                "id": "100",
                "title": "Won deal",
                "opportunity": "150.25",
                "currencyId": "USD",
                "createdTime": "2025-01-01T10:00:00+00:00",
                "closedTime": "2025-01-02T10:00:00+00:00",
                "movedTime": "2025-01-02T10:00:00+00:00",
                "stageId": "WON",
                "categoryId": "0",
                "contactId": "10",
            }
        ]


class UnsupportedCurrencyBitrixClient(RefreshBitrixClient):
    def list_deal_items(self) -> list[dict[str, object]]:
        rows = super().list_deal_items()
        rows[0]["currencyId"] = "JPY"
        return rows


class NoCommonRateRowsBitrixClient(RefreshBitrixClient):
    def list_deal_stage_history(self, deal_ids: list[int]) -> list[dict[str, object]]:
        rows = super().list_deal_stage_history(deal_ids)
        rows[0]["CREATED_TIME"] = "2025-01-01T10:00:00+00:00"
        return rows

    def list_deal_items(self) -> list[dict[str, object]]:
        rows = super().list_deal_items()
        rows[0]["currencyId"] = "EUR"
        rows[0]["closedTime"] = "2025-01-01T10:00:00+00:00"
        return rows


def _nbrb_transport(url: str) -> object:
    if url.endswith("/currencies"):
        return [
            {
                "Cur_ID": 431,
                "Cur_Abbreviation": "USD",
                "Cur_Scale": 1,
                "Cur_DateStart": "2020-01-01T00:00:00",
                "Cur_DateEnd": "2050-01-01T00:00:00",
            }
        ]
    if "rates/dynamics/431" in url:
        return [
            {"Date": "2025-01-01T00:00:00", "Cur_OfficialRate": 3.3},
            {"Date": "2025-01-02T00:00:00", "Cur_OfficialRate": 3.4},
        ]
    raise AssertionError(f"Unexpected URL: {url}")


def _no_common_rate_transport(url: str) -> object:
    if url.endswith("/currencies"):
        return [
            {
                "Cur_ID": 431,
                "Cur_Abbreviation": "USD",
                "Cur_Scale": 1,
                "Cur_DateStart": "2020-01-01T00:00:00",
                "Cur_DateEnd": "2050-01-01T00:00:00",
            },
            {
                "Cur_ID": 451,
                "Cur_Abbreviation": "EUR",
                "Cur_Scale": 1,
                "Cur_DateStart": "2020-01-01T00:00:00",
                "Cur_DateEnd": "2050-01-01T00:00:00",
            },
        ]
    if "rates/dynamics/431" in url:
        return [{"Date": "2025-01-01T00:00:00", "Cur_OfficialRate": 3.3}]
    if "rates/dynamics/451" in url:
        return [{"Date": "2025-01-02T00:00:00", "Cur_OfficialRate": 3.6}]
    raise AssertionError(f"Unexpected URL: {url}")
