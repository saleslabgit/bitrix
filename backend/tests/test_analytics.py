from datetime import date, datetime, timezone
from decimal import Decimal

import duckdb
import pytest

from app.pipeline.synthetic import run_synthetic_pipeline
from app.reports.analytics import (
    NO_SALES_SEGMENT,
    get_abc_report,
    get_concentration_report,
    get_deal_cycle_report,
    get_rfm_report,
    get_type_region_analytics,
    list_contact_analytics,
    list_currency_conversions,
    list_deal_analytics,
    list_stale_open_deals,
)
from app.storage import initialize_schema


def test_currency_conversion_uses_local_rates_for_usd_eur_and_byn() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        conversions = {
            row.deal_id: row for row in list_currency_conversions(connection)
        }

    assert conversions[1].amount_usd == Decimal("120000.00")
    assert conversions[1].rate_date == date(2023, 1, 1)
    assert conversions[2].amount_usd == Decimal("120000.00")
    assert conversions[4].amount_usd == Decimal("24242.42")
    assert conversions[15].rate_date == date(2025, 1, 1)


def test_contact_analytics_counts_only_won_revenue_and_profit() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        page = list_contact_analytics(connection, limit=20)
        rows = {row.contact_id: row for row in page.items}

    assert page.total == 10
    assert rows[1].total_deals_count == 4
    assert rows[1].won_deals_count == 4
    assert rows[1].budget_usd == Decimal("354242.42")
    assert rows[1].budget_in_work_usd == Decimal("0.00")
    assert rows[1].lost_budget_usd == Decimal("0.00")
    assert rows[1].revenue_usd == Decimal("354242.42")
    assert rows[1].estimated_profit_usd == Decimal("177121.21")
    assert rows[2].open_deals_count == 1
    assert rows[2].budget_usd == Decimal("191454.55")
    assert rows[2].budget_in_work_usd == Decimal("45000.00")
    assert rows[2].lost_budget_usd == Decimal("0.00")
    assert rows[2].revenue_usd == Decimal("146454.55")
    assert rows[2].has_sales is True


def test_contact_analytics_abc_and_rfm_handle_no_sales_contact() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)
        connection.execute(
            """
            INSERT INTO normalized_contacts (
                contact_id,
                contact_name,
                contact_type_raw,
                contact_type_normalized,
                region_normalized
            )
            VALUES (99, 'Synthetic No Sales', NULL, 'Не определено', 'Не определено')
            """
        )

        contact_row = [
            row
            for row in list_contact_analytics(connection, limit=100).items
            if row.contact_id == 99
        ][0]
        abc_row = [
            row for row in get_abc_report(connection) if row.contact_id == 99
        ][0]
        rfm_row = [
            row for row in get_rfm_report(connection) if row.contact_id == 99
        ][0]

    assert contact_row.revenue_usd == Decimal("0.00")
    assert contact_row.has_sales is False
    assert abc_row.abc_full == NO_SALES_SEGMENT
    assert abc_row.abc_12m == NO_SALES_SEGMENT
    assert rfm_row.rfm_code == "000"
    assert rfm_row.segment == NO_SALES_SEGMENT


def test_contact_analytics_budget_breakdown_uses_assigned_deals_usd() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        row = [
            row
            for row in list_contact_analytics(connection, limit=20).items
            if row.contact_id == 7
        ][0]

    assert row.budget_usd == Decimal("40000.00")
    assert row.budget_in_work_usd == Decimal("0.00")
    assert row.lost_budget_usd == Decimal("25000.00")
    assert row.revenue_usd == Decimal("15000.00")
    assert row.estimated_profit_usd == Decimal("7500.00")


def test_contact_analytics_supports_exact_contact_id_filter() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        page = list_contact_analytics(connection, limit=10, contact_id=4)

    assert page.total == 1
    assert page.items[0].contact_id == 4


def test_contact_analytics_contact_id_desc_handles_usd_deals_without_rate_rows() -> None:
    with duckdb.connect(database=":memory:") as connection:
        _load_usd_deal_without_rates_dataset(connection)

        page = list_contact_analytics(
            connection,
            limit=25,
            offset=0,
            sort="contact_id",
            order="desc",
        )

    assert page.total == 1
    assert page.items[0].contact_id == 1
    assert page.items[0].budget_usd == Decimal("100.00")
    assert page.items[0].revenue_usd == Decimal("100.00")
    assert page.items[0].estimated_profit_usd == Decimal("50.00")


def test_contact_analytics_sorts_before_pagination_by_revenue_and_date() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        revenue_page = list_contact_analytics(
            connection,
            limit=1,
            sort="revenue_usd",
            order="desc",
        )
        date_page = list_contact_analytics(
            connection,
            limit=3,
            sort="last_won_date",
            order="desc",
        )

    assert revenue_page.items[0].contact_id == 1
    assert [row.last_won_date for row in date_page.items] == sorted(
        (row.last_won_date for row in date_page.items),
        reverse=True,
    )


def test_contact_analytics_sorts_before_pagination_by_budget() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        page = list_contact_analytics(
            connection,
            limit=1,
            sort="budget_usd",
            order="desc",
        )

    assert page.items[0].contact_id == 1
    assert page.items[0].budget_usd == Decimal("354242.42")


def test_contact_analytics_filters_by_deal_creation_date_not_closed_date() -> None:
    with duckdb.connect(database=":memory:") as connection:
        _load_creation_date_filter_dataset(connection)

        created_2024 = list_contact_analytics(
            connection,
            limit=10,
            deal_created_from=date(2024, 1, 1),
            deal_created_to=date(2024, 12, 31),
        )
        created_2025 = list_contact_analytics(
            connection,
            limit=10,
            deal_created_from=date(2025, 1, 1),
            deal_created_to=date(2025, 12, 31),
        )

    assert created_2024.total == 1
    assert created_2024.items[0].contact_id == 1
    assert created_2024.items[0].budget_usd == Decimal("100.00")
    assert created_2024.items[0].revenue_usd == Decimal("100.00")
    assert created_2025.total == 1
    assert created_2025.items[0].contact_id == 2
    assert created_2025.items[0].budget_usd == Decimal("50.00")
    assert created_2025.items[0].budget_in_work_usd == Decimal("50.00")


def test_contact_analytics_composes_status_and_deal_creation_filters() -> None:
    with duckdb.connect(database=":memory:") as connection:
        _load_creation_date_filter_dataset(connection)

        page = list_contact_analytics(
            connection,
            limit=10,
            deal_created_from=date(2025, 1, 1),
            deal_created_to=date(2025, 12, 31),
            status="open",
        )

    assert page.total == 1
    assert page.items[0].contact_id == 2
    assert page.items[0].total_deals_count == 1
    assert page.items[0].open_deals_count == 1
    assert page.items[0].budget_usd == Decimal("50.00")
    assert page.items[0].revenue_usd == Decimal("0.00")


def test_contact_analytics_existing_report_date_filter_still_uses_closed_date() -> None:
    with duckdb.connect(database=":memory:") as connection:
        _load_creation_date_filter_dataset(connection)

        page = list_contact_analytics(
            connection,
            limit=10,
            date_from=date(2025, 1, 1),
            date_to=date(2025, 12, 31),
        )

    assert page.total == 2
    assert {row.contact_id for row in page.items} == {1, 2}
    assert page.items[0].revenue_usd == Decimal("100.00")


def test_contact_analytics_sort_tie_breaks_by_contact_id() -> None:
    with duckdb.connect(database=":memory:") as connection:
        _load_equal_revenue_dataset(connection)

        page = list_contact_analytics(
            connection,
            limit=10,
            sort="revenue_usd",
            order="desc",
        )

    assert [row.contact_id for row in page.items] == [1, 2, 3]


def test_contact_analytics_rejects_unsupported_sort_field() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        with pytest.raises(ValueError, match="Unsupported contact analytics sort field"):
            list_contact_analytics(
                connection,
                sort="raw_payload",  # type: ignore[arg-type]
            )


def test_deal_analytics_returns_rows_with_won_only_profit() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        page = list_deal_analytics(connection, limit=40)
        rows = {row.deal_id: row for row in page.items}

    assert page.total == 30
    assert rows[1].deal_name == "Synthetic Deal 001"
    assert rows[1].status_group == "won"
    assert rows[1].budget_usd == Decimal("120000.00")
    assert rows[1].estimated_profit_usd == Decimal("60000.00")
    assert rows[21].status_group == "open"
    assert rows[21].estimated_profit_usd == Decimal("0.00")
    assert rows[26].status_group == "lost"
    assert rows[26].estimated_profit_usd == Decimal("0.00")
    assert rows[21].closed_date is None


def test_deal_analytics_supports_exact_deal_id_filter() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        page = list_deal_analytics(connection, limit=10, deal_id=4)

    assert page.total == 1
    assert page.items[0].deal_id == 4


def test_deal_analytics_filters_by_status_type_region_and_created_date() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        page = list_deal_analytics(
            connection,
            limit=10,
            status="open",
            contact_type="Synthetic Partner A",
            region="Synthetic East",
            deal_created_from=date(2025, 10, 1),
            deal_created_to=date(2025, 10, 1),
        )

    assert page.total == 1
    assert page.items[0].deal_id == 22
    assert page.items[0].created_date == date(2025, 10, 1)


def test_deal_analytics_filters_by_client_search_and_returns_filtered_totals() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        page = list_deal_analytics(
            connection,
            limit=1,
            offset=0,
            client_search="contact 2",
            sort="budget_usd",
            order="desc",
        )

    assert page.total == 4
    assert len(page.items) == 1
    assert page.items[0].deal_id == 5
    assert page.filtered_budget_usd == Decimal("191454.55")
    assert page.filtered_estimated_profit_usd == Decimal("73227.28")


def test_deal_analytics_filters_by_exact_client_id_and_totals_before_pagination() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        page = list_deal_analytics(
            connection,
            limit=1,
            offset=0,
            client_id=2,
            sort="budget_usd",
            order="desc",
        )

    assert page.total == 4
    assert len(page.items) == 1
    assert {row.deal_id for row in page.items} == {5}
    assert page.filtered_budget_usd == Decimal("191454.55")
    assert page.filtered_estimated_profit_usd == Decimal("73227.28")


def test_deal_analytics_exact_client_id_composes_with_status() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        page = list_deal_analytics(
            connection,
            limit=10,
            client_id=2,
            status="won",
        )

    assert page.total == 3
    assert {row.deal_id for row in page.items} == {5, 6, 15}
    assert all(row.status_group == "won" for row in page.items)
    assert page.filtered_budget_usd == Decimal("146454.55")
    assert page.filtered_estimated_profit_usd == Decimal("73227.28")


def test_deal_analytics_exact_client_id_takes_precedence_over_client_search() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        page = list_deal_analytics(
            connection,
            limit=10,
            client_id=2,
            client_search="missing client name",
        )

    assert page.total == 4
    assert {row.deal_id for row in page.items} == {5, 6, 15, 21}


def test_deal_analytics_empty_filtered_totals_are_zero() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        page = list_deal_analytics(
            connection,
            limit=10,
            client_search="missing client",
        )

    assert page.total == 0
    assert page.items == ()
    assert page.filtered_budget_usd == Decimal("0.00")
    assert page.filtered_estimated_profit_usd == Decimal("0.00")


def test_deal_analytics_sorts_by_budget_profit_and_date_with_tie_breaker() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        budget_page = list_deal_analytics(
            connection,
            limit=1,
            sort="budget_usd",
            order="desc",
        )
        profit_page = list_deal_analytics(
            connection,
            limit=1,
            sort="estimated_profit_usd",
            order="desc",
        )
        date_page = list_deal_analytics(
            connection,
            limit=3,
            sort="closed_date",
            order="desc",
        )

    assert budget_page.items[0].deal_id == 1
    assert profit_page.items[0].deal_id == 1
    assert [row.closed_date for row in date_page.items] == sorted(
        (row.closed_date for row in date_page.items),
        reverse=True,
    )


def test_deal_analytics_sort_tie_breaks_by_deal_id() -> None:
    with duckdb.connect(database=":memory:") as connection:
        _load_equal_revenue_dataset(connection)

        page = list_deal_analytics(
            connection,
            limit=10,
            sort="estimated_profit_usd",
            order="desc",
        )

    assert [row.deal_id for row in page.items] == [1, 2, 3]


def test_deal_analytics_rejects_unsupported_sort_field() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        with pytest.raises(ValueError, match="Unsupported deal analytics sort field"):
            list_deal_analytics(
                connection,
                sort="raw_payload",  # type: ignore[arg-type]
            )


def test_abc_boundaries_at_80_and_95_percent_are_deterministic() -> None:
    with duckdb.connect(database=":memory:") as connection:
        _load_abc_boundary_dataset(connection)

        rows = {row.contact_id: row for row in get_abc_report(connection)}

    assert rows[1].abc_full == "A"
    assert rows[2].abc_full == "B"
    assert rows[3].abc_full == "C"
    assert rows[4].abc_full == NO_SALES_SEGMENT


def test_abc_comparison_uses_deterministic_last_12_month_anchor() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        rows = {row.contact_id: row for row in get_abc_report(connection)}

    assert rows[1].abc_full == "A"
    assert rows[1].abc_12m == NO_SALES_SEGMENT
    assert rows[1].abc_change == "A -> Нет продаж"
    assert rows[1].migration_priority == "срочно"


def test_rfm_covers_old_high_value_recent_single_and_reactivation_cases() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        rows = {row.contact_id: row for row in get_rfm_report(connection)}

    assert rows[1].needs_reactivation is True
    assert rows[1].frequency == 4
    assert rows[7].frequency == 1
    assert rows[7].segment in {"Новые", "Одноразовые", "Остальные"}
    assert rows[6].recency_days is not None
    assert rows[6].recency_days < rows[1].recency_days


def test_stale_open_deals_detects_long_open_synthetic_deal() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        rows = list_stale_open_deals(connection)

    assert any(row.deal_id == 21 for row in rows)
    assert all(row.days_over_threshold > 0 for row in rows)


def test_deal_cycle_metrics_calculate_local_durations() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        report = get_deal_cycle_report(connection)

    assert report.overall.deals_count == 25
    assert report.overall.p75_days > 0
    assert any(
        row.group_name == "Synthetic Direct"
        for row in report.by_contact_type
    )
    assert any(row.group_name == "Synthetic North" for row in report.by_region)


def test_concentration_output_is_deterministic() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        report = get_concentration_report(connection)

    assert report.total_revenue_usd > 0
    assert [entry.top_n for entry in report.entries] == [1, 3, 5]
    assert report.entries[0].revenue_usd == Decimal("354242.42")
    assert report.entries[0].share_percent <= report.entries[1].share_percent


def test_type_region_analytics_uses_normalized_values_and_fallback() -> None:
    with duckdb.connect(database=":memory:") as connection:
        run_synthetic_pipeline(connection)

        report = get_type_region_analytics(connection)
        type_rows = {row.group_name: row for row in report.type_rows}
        region_rows = {row.group_name: row for row in report.region_rows}

    assert type_rows["Synthetic Direct"].revenue_usd == Decimal("161424.25")
    assert type_rows["Не определено"].contact_count == 2
    assert type_rows["Не определено"].lost_deals_count >= 1
    assert region_rows["Synthetic North"].won_deals_count == 9


def _load_abc_boundary_dataset(connection: duckdb.DuckDBPyConnection) -> None:
    initialize_schema(connection)
    connection.executemany(
        """
        INSERT INTO normalized_contacts (
            contact_id,
            contact_name,
            contact_type_raw,
            contact_type_normalized,
            region_normalized
        )
        VALUES (?, ?, NULL, 'Synthetic Type', 'Synthetic Region')
        """,
        [
            (1, "Boundary Contact 1"),
            (2, "Boundary Contact 2"),
            (3, "Boundary Contact 3"),
            (4, "Boundary Contact 4"),
        ],
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
        [datetime(2025, 1, 2, tzinfo=timezone.utc)],
    )
    connection.executemany(
        """
        INSERT INTO normalized_deals (
            deal_id,
            deal_name,
            amount_original,
            currency_original,
            created_at,
            closed_at,
            stage_id,
            category_id,
            status_group,
            analytical_contact_id,
            analytical_contact_name,
            contact_type_normalized,
            region_normalized
        )
        VALUES (
            ?,
            ?,
            ?,
            'USD',
            ?,
            ?,
            'SYN:WON',
            1,
            'won',
            ?,
            ?,
            'Synthetic Type',
            'Synthetic Region'
        )
        """,
        [
            (
                1,
                "Boundary Deal 1",
                Decimal("80.00"),
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 2, tzinfo=timezone.utc),
                1,
                "Boundary Contact 1",
            ),
            (
                2,
                "Boundary Deal 2",
                Decimal("15.00"),
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 2, tzinfo=timezone.utc),
                2,
                "Boundary Contact 2",
            ),
            (
                3,
                "Boundary Deal 3",
                Decimal("5.00"),
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 2, tzinfo=timezone.utc),
                3,
                "Boundary Contact 3",
            ),
        ],
    )


def _load_equal_revenue_dataset(connection: duckdb.DuckDBPyConnection) -> None:
    initialize_schema(connection)
    connection.executemany(
        """
        INSERT INTO normalized_contacts (
            contact_id,
            contact_name,
            contact_type_raw,
            contact_type_normalized,
            region_normalized
        )
        VALUES (?, ?, NULL, 'Synthetic Type', 'Synthetic Region')
        """,
        [
            (3, "Tie Contact 3"),
            (1, "Tie Contact 1"),
            (2, "Tie Contact 2"),
        ],
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
        [datetime(2025, 1, 2, tzinfo=timezone.utc)],
    )
    connection.executemany(
        """
        INSERT INTO normalized_deals (
            deal_id,
            deal_name,
            amount_original,
            currency_original,
            created_at,
            closed_at,
            stage_id,
            category_id,
            status_group,
            analytical_contact_id,
            analytical_contact_name,
            contact_type_normalized,
            region_normalized
        )
        VALUES (?, ?, 10.00, 'USD', ?, ?, 'SYN:WON', 1, 'won', ?, ?, 'Synthetic Type', 'Synthetic Region')
        """,
        [
            (
                1,
                "Tie Deal 1",
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 2, tzinfo=timezone.utc),
                3,
                "Tie Contact 3",
            ),
            (
                2,
                "Tie Deal 2",
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 2, tzinfo=timezone.utc),
                1,
                "Tie Contact 1",
            ),
            (
                3,
                "Tie Deal 3",
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 2, tzinfo=timezone.utc),
                2,
                "Tie Contact 2",
            ),
        ],
    )


def _load_usd_deal_without_rates_dataset(connection: duckdb.DuckDBPyConnection) -> None:
    initialize_schema(connection)
    connection.execute(
        """
        INSERT INTO normalized_contacts (
            contact_id,
            contact_name,
            contact_type_raw,
            contact_type_normalized,
            region_normalized
        )
        VALUES (1, 'USD Contact', NULL, 'Synthetic Type', 'Synthetic Region')
        """
    )
    connection.execute(
        """
        INSERT INTO normalized_deals (
            deal_id,
            deal_name,
            amount_original,
            currency_original,
            created_at,
            closed_at,
            stage_id,
            category_id,
            status_group,
            analytical_contact_id,
            analytical_contact_name,
            contact_type_normalized,
            region_normalized
        )
        VALUES (
            1,
            'USD Deal Without Local Rate',
            100.00,
            'USD',
            ?,
            ?,
            'SYN:WON',
            1,
            'won',
            1,
            'USD Contact',
            'Synthetic Type',
            'Synthetic Region'
        )
        """,
        [
            datetime(2025, 1, 1, tzinfo=timezone.utc),
            datetime(2025, 1, 2, tzinfo=timezone.utc),
        ],
    )


def _load_creation_date_filter_dataset(connection: duckdb.DuckDBPyConnection) -> None:
    initialize_schema(connection)
    connection.executemany(
        """
        INSERT INTO normalized_contacts (
            contact_id,
            contact_name,
            contact_type_raw,
            contact_type_normalized,
            region_normalized
        )
        VALUES (?, ?, NULL, 'Synthetic Type', 'Synthetic Region')
        """,
        [
            (1, "Created Contact 1"),
            (2, "Created Contact 2"),
        ],
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
        VALUES ('USD', DATE '2024-01-01', 3.30000000, 3.30000000, 'NBRB', ?)
        """,
        [datetime(2025, 1, 2, tzinfo=timezone.utc)],
    )
    connection.executemany(
        """
        INSERT INTO normalized_deals (
            deal_id,
            deal_name,
            amount_original,
            currency_original,
            created_at,
            closed_at,
            stage_id,
            category_id,
            status_group,
            analytical_contact_id,
            analytical_contact_name,
            contact_type_normalized,
            region_normalized
        )
        VALUES (?, ?, ?, 'USD', ?, ?, ?, 1, ?, ?, ?, 'Synthetic Type', 'Synthetic Region')
        """,
        [
            (
                1,
                "Created In 2024 Closed In 2025",
                Decimal("100.00"),
                datetime(2024, 6, 1, tzinfo=timezone.utc),
                datetime(2025, 2, 1, tzinfo=timezone.utc),
                "SYN:WON",
                "won",
                1,
                "Created Contact 1",
            ),
            (
                2,
                "Created In 2025 Open",
                Decimal("50.00"),
                datetime(2025, 3, 1, tzinfo=timezone.utc),
                None,
                "SYN:OPEN",
                "open",
                2,
                "Created Contact 2",
            ),
        ],
    )
