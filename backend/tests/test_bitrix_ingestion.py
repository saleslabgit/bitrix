import duckdb
from datetime import datetime, timezone

from app.bitrix.ingestion import run_bitrix_manual_ingestion
from app.bitrix.transform import transform_deal_contact_links_from_deals
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

    def list_deal_items(self) -> list[dict[str, object]]:
        return [
            {
                "id": "100",
                "title": "Won deal",
                "opportunity": "150.25",
                "currencyId": "USD",
                "createdTime": "2025-01-01T10:00:00+00:00",
                "closedTime": "2025-01-05T10:00:00+00:00",
                "stageId": "WON",
                "categoryId": "0",
                "contactId": "10",
                "contactIds": ["10", "20"],
                "COMMENTS": "hidden",
            },
            {
                "id": "200",
                "title": "Open deal",
                "opportunity": "75",
                "currencyId": "USD",
                "createdTime": "2025-02-01T10:00:00+00:00",
                "stageId": "OPEN",
                "categoryId": "0",
                "contactId": "20",
            },
        ]


class DuplicateDealBitrixClient(FakeBitrixClient):
    def list_deal_items(self) -> list[dict[str, object]]:
        rows = super().list_deal_items()
        return [rows[0], rows[0]]


class DesignerSecondaryItemBitrixClient(FakeBitrixClient):
    def list_contacts(self, contact_type_field: str | None) -> list[dict[str, object]]:
        assert contact_type_field == "UF_CRM_CONTACT_TYPE"
        return [
            {
                "ID": "661",
                "NAME": "Designer",
                "UF_CRM_CONTACT_TYPE": "61",
            },
            {
                "ID": "900",
                "NAME": "Dealer",
                "UF_CRM_CONTACT_TYPE": "67",
            },
        ]

    def list_deal_items(self) -> list[dict[str, object]]:
        return [
            {
                "id": "123",
                "title": "Historical deal",
                "opportunity": "100",
                "currencyId": "USD",
                "createdTime": "2025-01-01T10:00:00+00:00",
                "closedTime": "2025-01-02T10:00:00+00:00",
                "stageId": "WON",
                "categoryId": "0",
                "contactId": "900",
                "contactIds": ["900", "661"],
            }
        ]


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
    assert second_status.raw_links_count == 3
    assert second_status.normalized_contacts_count == 2
    assert second_status.normalized_deals_count == 2
    assert raw_contacts == [
        (10, "Ada Lovelace", "partner"),
        (20, "Grace Hopper", "client"),
    ]
    assert raw_deals == [(100, "Won deal", "won"), (200, "Open deal", "open")]
    assert raw_links == [
        (100, 10, True, None, None),
        (100, 20, False, None, None),
        (200, 20, True, None, None),
    ]
    assert normalized_deal == (10, "Partner", "West")


def test_manual_bitrix_ingestion_uses_item_contact_ids_for_secondary_designer() -> None:
    with duckdb.connect(database=":memory:") as connection:
        initialize_schema(connection)
        connection.executemany(
            """
            INSERT INTO contact_type_rules (
                raw_value,
                normalized_type,
                priority,
                region,
                is_active
            )
            VALUES (?, ?, ?, ?, true)
            """,
            [
                ("61", "Дизайнер", 1, "Беларусь"),
                ("67", "Дилер", 3, "Беларусь"),
            ],
        )

        status = run_bitrix_manual_ingestion(
            connection,
            client=DesignerSecondaryItemBitrixClient(),
            contact_type_field="UF_CRM_CONTACT_TYPE",
        )
        connection.execute(
            """
            INSERT INTO currency_rates (
                currency,
                rate_date,
                source_rate_byn,
                usd_rate_byn,
                rate_source,
                rate_fetched_at
            )
            VALUES ('USD', DATE '2025-01-01', 3.30000000, 3.30000000, 'NBRB', ?)
            """,
            [datetime(2025, 1, 1, tzinfo=timezone.utc)],
        )
        raw_links = connection.execute(
            """
            SELECT deal_id, contact_id, is_primary
            FROM raw_deal_contact_links
            ORDER BY deal_id, contact_id
            """
        ).fetchall()
        normalized_deal = connection.execute(
            """
            SELECT analytical_contact_id, contact_type_normalized
            FROM normalized_deals
            WHERE deal_id = 123
            """
        ).fetchone()
        analytics_page = list_contact_analytics(connection, limit=10)
        analytics = {row.contact_id: row for row in analytics_page.items}

    assert status.state == "success"
    assert raw_links == [(123, 661, False), (123, 900, True)]
    assert normalized_deal == (661, "Дизайнер")
    assert analytics[661].total_deals_count == 1


def test_deal_contact_links_are_built_from_downloaded_deal_rows() -> None:
    links = transform_deal_contact_links_from_deals(
        [
            {"ID": "1", "CONTACT_ID": "10", "CONTACT_IDS": ["10", "20", ""]},
            {"ID": "2", "CONTACT_ID": "0", "CONTACT_IDS": "30, 40,0"},
            {"ID": "3", "CONTACT_ID": None, "CONTACT_IDS": []},
            {
                "ID": "4",
                "CONTACT_ID": None,
                "CONTACT_IDS": {
                    "n0": {"CONTACT_ID": "50"},
                    "n1": {"VALUE": "60"},
                },
            },
            {
                "ID": "5",
                "CONTACT_ID": None,
                "CONTACT_IDS": "[70, 80]",
            },
        ]
    )

    rows = [
        (
            link.deal_id,
            link.contact_id,
            link.is_primary,
            link.sort_order,
            link.role_id,
        )
        for link in links
    ]

    assert rows == [
        (1, 10, True, None, None),
        (1, 20, False, None, None),
        (2, 30, False, None, None),
        (2, 40, False, None, None),
        (4, 50, False, None, None),
        (4, 60, False, None, None),
        (5, 70, False, None, None),
        (5, 80, False, None, None),
    ]


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
