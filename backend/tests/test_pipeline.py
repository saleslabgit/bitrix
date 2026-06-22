from datetime import datetime, timezone
from decimal import Decimal

import duckdb

from app.domain import DealSnapshot, StageSnapshot
from app.pipeline.normalization import NO_CONTACT_NAME, UNDEFINED_VALUE, normalize_local_data
from app.pipeline.synthetic import run_synthetic_pipeline
from app.storage import initialize_schema
from app.storage.loaders import load_bitrix_raw_data
from app.storage.snapshots import RAW_SNAPSHOT_COLUMNS
from app.storage.status import get_active_dataset_run


def test_synthetic_pipeline_loads_and_normalizes_expected_counts() -> None:
    with duckdb.connect(database=":memory:") as connection:
        status = run_synthetic_pipeline(connection)
        second_status = run_synthetic_pipeline(connection)

        assert status.state == "success"
        assert second_status.state == "success"
        assert second_status.raw_contacts_count == 10
        assert second_status.raw_deals_count == 30
        assert second_status.raw_links_count == 30
        assert second_status.normalized_contacts_count == 10
        assert second_status.normalized_deals_count == 30


def test_synthetic_pipeline_writes_allowed_raw_parquet_snapshots(tmp_path) -> None:
    with duckdb.connect(database=":memory:") as connection:
        status = run_synthetic_pipeline(connection, data_dir=tmp_path)

        assert status.is_active is True
        assert status.snapshot_paths
        assert all(not path.startswith("/") for path in status.snapshot_paths)
        assert get_active_dataset_run(connection).run_id == status.run_id

        for snapshot_path in status.snapshot_paths:
            table_name = snapshot_path.rsplit("/", maxsplit=1)[-1].removesuffix(
                ".parquet"
            )
            full_path = tmp_path / snapshot_path
            columns = connection.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{full_path}')"
            ).fetchall()
            assert full_path.exists()
            assert tuple(row[0] for row in columns) == RAW_SNAPSHOT_COLUMNS[table_name]


def test_normalized_contacts_include_type_region_and_fallbacks() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        rows = connection.execute(
            """
            SELECT
                contact_id,
                contact_type_normalized,
                region_normalized
            FROM normalized_contacts
            WHERE contact_id IN (1, 8, 10)
            ORDER BY contact_id
            """
        ).fetchall()

    assert rows == [
        (1, "Synthetic Key", "Synthetic North"),
        (8, UNDEFINED_VALUE, UNDEFINED_VALUE),
        (10, UNDEFINED_VALUE, UNDEFINED_VALUE),
    ]


def test_normalized_deals_have_one_row_per_deal_and_expected_contacts() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        count, distinct_count = connection.execute(
            "SELECT COUNT(*), COUNT(DISTINCT deal_id) FROM normalized_deals"
        ).fetchone()
        multi_contact_deal = connection.execute(
            """
            SELECT
                analytical_contact_id,
                analytical_contact_name,
                contact_type_normalized,
                region_normalized
            FROM normalized_deals
            WHERE deal_id = 7
            """
        ).fetchone()
        no_contact_deal = connection.execute(
            """
            SELECT
                analytical_contact_id,
                analytical_contact_name,
                contact_type_normalized,
                region_normalized
            FROM normalized_deals
            WHERE deal_id = 30
            """
        ).fetchone()

    assert count == 30
    assert distinct_count == 30
    assert multi_contact_deal == (
        4,
        "Synthetic Contact 4",
        "Synthetic Partner B",
        "Synthetic West",
    )
    assert no_contact_deal == (
        None,
        NO_CONTACT_NAME,
        UNDEFINED_VALUE,
        UNDEFINED_VALUE,
    )


def test_normalize_local_data_with_empty_raw_tables_leaves_normalized_tables_empty() -> None:
    with duckdb.connect(database=":memory:") as connection:
        initialize_schema(connection)

        normalize_local_data(connection)

        counts = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM normalized_contacts),
                (SELECT COUNT(*) FROM normalized_deals)
            """
        ).fetchone()

    assert counts == (0, 0)


def test_normalize_local_data_keeps_deals_without_links() -> None:
    with duckdb.connect(database=":memory:") as connection:
        initialize_schema(connection)
        load_bitrix_raw_data(
            connection,
            contacts=[],
            deals=[
                DealSnapshot(
                    deal_id=1,
                    deal_name="No link deal",
                    amount_original=Decimal("10.00"),
                    currency_original="USD",
                    created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
                    stage_id="WON",
                    status_group="won",
                )
            ],
            links=[],
            stages=[StageSnapshot(stage_id="WON", status_group="won")],
        )

        normalize_local_data(connection)
        row = connection.execute(
            """
            SELECT analytical_contact_id, analytical_contact_name, contact_type_normalized, region_normalized
            FROM normalized_deals
            WHERE deal_id = 1
            """
        ).fetchone()

    assert row == (None, NO_CONTACT_NAME, UNDEFINED_VALUE, UNDEFINED_VALUE)


def test_normalized_deals_represent_stage_statuses() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        rows = connection.execute(
            """
            SELECT status_group, COUNT(*)
            FROM normalized_deals
            GROUP BY status_group
            ORDER BY status_group
            """
        ).fetchall()

    assert rows == [("lost", 5), ("open", 5), ("won", 20)]
