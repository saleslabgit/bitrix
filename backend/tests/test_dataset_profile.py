import duckdb

from app.pipeline.normalization import UNDEFINED_VALUE
from app.pipeline.synthetic import run_synthetic_pipeline
from app.reports.profile import MISSING_VALUE_LABEL, get_dataset_profile
from app.storage import initialize_schema


def counts_by_label(rows):
    return {row.label: row.count for row in rows}


def test_dataset_profile_reports_safe_aggregate_counts(tmp_path) -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection, data_dir=tmp_path)

        profile = get_dataset_profile(connection)

    assert profile.active_dataset is not None
    assert profile.active_dataset.dataset_kind == "local_synthetic"
    assert profile.latest_run is not None
    assert profile.snapshot_count == 6
    assert all(table.exists for table in profile.expected_tables)

    raw_type_counts = counts_by_label(profile.contact_type_raw_counts)
    assert raw_type_counts[MISSING_VALUE_LABEL] == 1
    assert raw_type_counts["synthetic-direct"] == 2
    assert profile.distinct_contact_type_raw_values_count == 7
    assert profile.contacts_missing_type_count == 1

    assert profile.contact_type_rules.active_rules_count == 6
    assert profile.contact_type_rules.raw_values_without_active_rule == (
        "synthetic-service",
    )

    assert profile.link_integrity.deals_without_analytical_contact_count == 5
    assert profile.link_integrity.deals_without_local_link_count == 1
    assert profile.link_integrity.links_missing_contact_count == 0
    assert profile.link_integrity.links_missing_deal_count == 0

    assert counts_by_label(profile.status_group_counts) == {
        "lost": 5,
        "open": 5,
        "won": 20,
    }
    assert counts_by_label(profile.currency_counts) == {
        "BYN": 7,
        "EUR": 9,
        "USD": 14,
    }
    assert sum(row.count for row in profile.category_stage_counts) == 30
    assert profile.deal_date_range.min_created_at is not None
    assert profile.deal_date_range.max_closed_at is not None

    assert profile.normalization.normalized_contacts_undefined_type_count == 2
    assert profile.normalization.normalized_contacts_undefined_region_count == 2
    assert profile.normalization.normalized_deals_undefined_type_count == 5
    assert profile.normalization.normalized_deals_undefined_region_count == 5
    assert profile.normalization.normalized_contacts_type_mostly_undefined is False
    assert profile.normalization.normalized_deals_type_mostly_undefined is False

    assert counts_by_label(profile.normalized_deal_type_counts)[UNDEFINED_VALUE] == 5
    assert counts_by_label(profile.normalized_deal_region_counts)[UNDEFINED_VALUE] == 5
    assert sum(row.count for row in profile.normalized_deal_type_region_counts) == 30


def test_dataset_profile_treats_empty_bitrix_type_values_as_missing() -> None:
    with duckdb.connect(database=":memory:") as connection:
        initialize_schema(connection)
        connection.executemany(
            """
            INSERT INTO raw_contacts (contact_id, contact_name, contact_type_raw)
            VALUES (?, ?, ?)
            """,
            [
                (1, "Synthetic Contact 1", None),
                (2, "Synthetic Contact 2", ""),
                (3, "Synthetic Contact 3", "False"),
                (4, "Synthetic Contact 4", "[]"),
                (5, "Synthetic Contact 5", "[59]"),
            ],
        )

        profile = get_dataset_profile(connection)

    assert counts_by_label(profile.contact_type_raw_counts) == {
        MISSING_VALUE_LABEL: 4,
        "[59]": 1,
    }
    assert profile.contacts_missing_type_count == 4
    assert profile.distinct_contact_type_raw_values_count == 1
    assert profile.contact_type_rules.raw_values_without_active_rule == ("[59]",)
