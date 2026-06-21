import duckdb

from app.pipeline.normalization import NO_CONTACT_NAME, UNDEFINED_VALUE
from app.pipeline.synthetic import run_synthetic_pipeline
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
