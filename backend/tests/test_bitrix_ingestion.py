import duckdb

from app.bitrix.ingestion import run_bitrix_manual_ingestion
from app.pipeline.synthetic import run_synthetic_pipeline
from app.reports.analytics import list_contact_analytics
from app.storage import initialize_schema
from app.storage.status import get_active_dataset_run, get_dataset_storage_status


class FakeBitrixClient:
    def list_stages(self) -> list[dict[str, object]]:
        return [
            {
                "STATUS_ID": "WON",
                "CATEGORY_ID": "0",
                "SEMANTICS": "S",
                "NAME": "Won",
            },
            {
                "STATUS_ID": "OPEN",
                "CATEGORY_ID": "0",
                "SEMANTICS": "P",
                "NAME": "Open",
            },
        ]

    def list_contacts(self, contact_type_field: str | None) -> list[dict[str, object]]:
        assert contact_type_field == "UF_CRM_CONTACT_TYPE"
        return [
            {
                "ID": "10",
                "NAME": "Ada",
                "LAST_NAME": "Lovelace",
                "UF_CRM_CONTACT_TYPE": "partner",
                "PHONE": [{"VALUE": "+000"}],
                "EMAIL": [{"VALUE": "hidden@example.com"}],
            },
            {
                "ID": "20",
                "NAME": "Grace",
                "LAST_NAME": "Hopper",
                "UF_CRM_CONTACT_TYPE": "client",
                "ADDRESS": "hidden",
            },
        ]

    def list_deals(self) -> list[dict[str, object]]:
        return [
            {
                "ID": "100",
                "TITLE": "Won deal",
                "OPPORTUNITY": "150.25",
                "CURRENCY_ID": "USD",
                "DATE_CREATE": "2025-01-01T10:00:00+00:00",
                "CLOSEDATE": "2025-01-05T10:00:00+00:00",
                "STAGE_ID": "WON",
                "CATEGORY_ID": "0",
                "COMMENTS": "hidden",
            },
            {
                "ID": "200",
                "TITLE": "Open deal",
                "OPPORTUNITY": "75",
                "CURRENCY_ID": "USD",
                "DATE_CREATE": "2025-02-01T10:00:00+00:00",
                "STAGE_ID": "OPEN",
                "CATEGORY_ID": "0",
            },
        ]

    def get_deal_contact_links(self, deal_id: int) -> list[dict[str, object]]:
        if deal_id == 100:
            return [
                {
                    "DEAL_ID": "100",
                    "CONTACT_ID": "10",
                    "IS_PRIMARY": "Y",
                    "SORT": "10",
                    "ROLE_ID": "decision-maker",
                    "PHONE": "hidden",
                }
            ]
        return [{"DEAL_ID": "200", "CONTACT_ID": "20", "IS_PRIMARY": "N"}]


class DuplicateDealBitrixClient(FakeBitrixClient):
    def list_deals(self) -> list[dict[str, object]]:
        rows = super().list_deals()
        return [rows[0], rows[0]]


def test_manual_bitrix_ingestion_loads_allowed_raw_data_and_normalizes(tmp_path) -> None:
    with duckdb.connect(database=":memory:") as connection:
        initialize_schema(connection)
        connection.execute(
            """
            INSERT INTO contact_type_rules (
                raw_value,
                normalized_type,
                priority,
                region,
                is_active
            )
            VALUES ('partner', 'Partner', 10, 'West', true)
            """
        )

        status = run_bitrix_manual_ingestion(
            connection,
            client=FakeBitrixClient(),
            contact_type_field="UF_CRM_CONTACT_TYPE",
            data_dir=tmp_path,
        )
        second_status = run_bitrix_manual_ingestion(
            connection,
            client=FakeBitrixClient(),
            contact_type_field="UF_CRM_CONTACT_TYPE",
            data_dir=tmp_path,
        )

        raw_contacts = connection.execute(
            """
            SELECT contact_id, contact_name, contact_type_raw
            FROM raw_contacts
            ORDER BY contact_id
            """
        ).fetchall()
        raw_deals = connection.execute(
            """
            SELECT deal_id, deal_name, status_group
            FROM raw_deals
            ORDER BY deal_id
            """
        ).fetchall()
        raw_links = connection.execute(
            """
            SELECT deal_id, contact_id, is_primary, sort_order, role_id
            FROM raw_deal_contact_links
            ORDER BY deal_id, contact_id
            """
        ).fetchall()
        normalized_deal = connection.execute(
            """
            SELECT analytical_contact_id, contact_type_normalized, region_normalized
            FROM normalized_deals
            WHERE deal_id = 100
            """
        ).fetchone()

    assert status.state == "success"
    assert status.is_active is True
    assert status.snapshot_paths
    assert second_status.raw_contacts_count == 2
    assert second_status.raw_deals_count == 2
    assert second_status.raw_links_count == 2
    assert second_status.normalized_contacts_count == 2
    assert second_status.normalized_deals_count == 2
    assert raw_contacts == [
        (10, "Ada Lovelace", "partner"),
        (20, "Grace Hopper", "client"),
    ]
    assert raw_deals == [(100, "Won deal", "won"), (200, "Open deal", "open")]
    assert raw_links == [(100, 10, True, 10, "decision-maker"), (200, 20, False, None, None)]
    assert normalized_deal == (10, "Partner", "West")


def test_failed_manual_bitrix_ingestion_keeps_previous_active_dataset(tmp_path) -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection, data_dir=tmp_path)
        successful_status = run_bitrix_manual_ingestion(
            connection,
            client=FakeBitrixClient(),
            contact_type_field="UF_CRM_CONTACT_TYPE",
            data_dir=tmp_path,
        )

        failed_status = run_bitrix_manual_ingestion(
            connection,
            client=DuplicateDealBitrixClient(),
            contact_type_field="UF_CRM_CONTACT_TYPE",
            data_dir=tmp_path,
        )
        active_status = get_active_dataset_run(connection)
        storage_status = get_dataset_storage_status(connection)
        analytics_page = list_contact_analytics(connection, limit=10)
        normalized_deal_count = connection.execute(
            "SELECT COUNT(*) FROM normalized_deals"
        ).fetchone()[0]

    assert successful_status.state == "success"
    assert failed_status.state == "error"
    assert failed_status.is_active is False
    assert active_status.run_id == successful_status.run_id
    assert storage_status.latest_run.run_id == failed_status.run_id
    assert storage_status.active_dataset.run_id == successful_status.run_id
    assert normalized_deal_count == 2
    assert analytics_page.total == 2


def test_manual_bitrix_ingestion_stores_safe_error_status() -> None:
    class BrokenClient:
        def list_stages(self) -> list[dict[str, object]]:
            raise ValueError("Required stage data is missing.")

    with duckdb.connect(database=":memory:") as connection:
        status = run_bitrix_manual_ingestion(
            connection,
            client=BrokenClient(),
            contact_type_field=None,
        )

    assert status.state == "error"
    assert status.message == "Required stage data is missing."
