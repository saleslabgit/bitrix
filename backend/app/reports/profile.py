from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import duckdb

from app.pipeline.normalization import UNDEFINED_VALUE
from app.storage.schema import list_expected_tables
from app.storage.status import DatasetRunStatus, get_dataset_storage_status


MISSING_VALUE_LABEL = "Не заполнено"
MISSING_RAW_TYPE_SQL = """
contact_type_raw IS NULL
OR trim(contact_type_raw) = ''
OR lower(trim(contact_type_raw)) = 'false'
OR trim(contact_type_raw) = '[]'
"""


@dataclass(frozen=True)
class TablePresence:
    table_name: str
    exists: bool


@dataclass(frozen=True)
class CountByLabel:
    label: str
    count: int


@dataclass(frozen=True)
class CountByStage:
    category_id: int | None
    stage_id: str
    count: int


@dataclass(frozen=True)
class CountByTypeRegion:
    contact_type_normalized: str
    region_normalized: str
    count: int


@dataclass(frozen=True)
class DateRange:
    min_created_at: datetime | None
    max_created_at: datetime | None
    min_closed_at: datetime | None
    max_closed_at: datetime | None


@dataclass(frozen=True)
class NormalizationProfile:
    normalized_contacts_undefined_type_count: int
    normalized_contacts_undefined_region_count: int
    normalized_deals_undefined_type_count: int
    normalized_deals_undefined_region_count: int
    normalized_contacts_type_mostly_undefined: bool
    normalized_contacts_region_mostly_undefined: bool
    normalized_deals_type_mostly_undefined: bool
    normalized_deals_region_mostly_undefined: bool


@dataclass(frozen=True)
class ContactTypeRulesProfile:
    active_rules_count: int
    raw_values_without_active_rule: tuple[str, ...]


@dataclass(frozen=True)
class LinkIntegrityProfile:
    deals_without_analytical_contact_count: int
    deals_without_local_link_count: int
    links_missing_contact_count: int
    links_missing_deal_count: int


@dataclass(frozen=True)
class DatasetProfile:
    active_dataset: DatasetRunStatus | None
    latest_run: DatasetRunStatus | None
    snapshot_count: int
    expected_tables: tuple[TablePresence, ...]
    contact_type_raw_counts: tuple[CountByLabel, ...]
    distinct_contact_type_raw_values_count: int
    contacts_missing_type_count: int
    link_integrity: LinkIntegrityProfile
    status_group_counts: tuple[CountByLabel, ...]
    currency_counts: tuple[CountByLabel, ...]
    category_stage_counts: tuple[CountByStage, ...]
    deal_date_range: DateRange
    normalization: NormalizationProfile
    contact_type_rules: ContactTypeRulesProfile
    normalized_deal_type_counts: tuple[CountByLabel, ...]
    normalized_deal_region_counts: tuple[CountByLabel, ...]
    normalized_deal_type_region_counts: tuple[CountByTypeRegion, ...]


def get_dataset_profile(connection: duckdb.DuckDBPyConnection) -> DatasetProfile:
    storage_status = get_dataset_storage_status(connection)
    expected_tables = _expected_table_presence(connection)
    active_or_latest = storage_status.active_dataset or storage_status.latest_run
    snapshot_count = len(active_or_latest.snapshot_paths) if active_or_latest else 0

    return DatasetProfile(
        active_dataset=storage_status.active_dataset,
        latest_run=storage_status.latest_run,
        snapshot_count=snapshot_count,
        expected_tables=expected_tables,
        contact_type_raw_counts=_contact_type_raw_counts(connection),
        distinct_contact_type_raw_values_count=_distinct_contact_type_raw_count(
            connection
        ),
        contacts_missing_type_count=_scalar(
            connection,
            f"""
            SELECT COUNT(*)
            FROM raw_contacts
            WHERE {MISSING_RAW_TYPE_SQL}
            """,
        ),
        link_integrity=LinkIntegrityProfile(
            deals_without_analytical_contact_count=_scalar(
                connection,
                """
                SELECT COUNT(*)
                FROM normalized_deals
                WHERE analytical_contact_id IS NULL
                """,
            ),
            deals_without_local_link_count=_scalar(
                connection,
                """
                SELECT COUNT(*)
                FROM raw_deals deals
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM raw_deal_contact_links links
                    WHERE links.deal_id = deals.deal_id
                )
                """,
            ),
            links_missing_contact_count=_scalar(
                connection,
                """
                SELECT COUNT(*)
                FROM raw_deal_contact_links links
                LEFT JOIN raw_contacts contacts
                    ON contacts.contact_id = links.contact_id
                WHERE contacts.contact_id IS NULL
                """,
            ),
            links_missing_deal_count=_scalar(
                connection,
                """
                SELECT COUNT(*)
                FROM raw_deal_contact_links links
                LEFT JOIN raw_deals deals
                    ON deals.deal_id = links.deal_id
                WHERE deals.deal_id IS NULL
                """,
            ),
        ),
        status_group_counts=_count_by_label(
            connection,
            """
            SELECT status_group, COUNT(*)
            FROM raw_deals
            GROUP BY status_group
            ORDER BY status_group
            """,
        ),
        currency_counts=_count_by_label(
            connection,
            """
            SELECT currency_original, COUNT(*)
            FROM raw_deals
            GROUP BY currency_original
            ORDER BY currency_original
            """,
        ),
        category_stage_counts=_category_stage_counts(connection),
        deal_date_range=_deal_date_range(connection),
        normalization=_normalization_profile(connection),
        contact_type_rules=ContactTypeRulesProfile(
            active_rules_count=_scalar(
                connection,
                "SELECT COUNT(*) FROM contact_type_rules WHERE is_active = true",
            ),
            raw_values_without_active_rule=_raw_values_without_active_rule(connection),
        ),
        normalized_deal_type_counts=_count_by_label(
            connection,
            """
            SELECT contact_type_normalized, COUNT(*)
            FROM normalized_deals
            GROUP BY contact_type_normalized
            ORDER BY contact_type_normalized
            """,
        ),
        normalized_deal_region_counts=_count_by_label(
            connection,
            """
            SELECT region_normalized, COUNT(*)
            FROM normalized_deals
            GROUP BY region_normalized
            ORDER BY region_normalized
            """,
        ),
        normalized_deal_type_region_counts=_type_region_counts(connection),
    )


def _expected_table_presence(
    connection: duckdb.DuckDBPyConnection,
) -> tuple[TablePresence, ...]:
    rows = connection.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        """
    ).fetchall()
    existing_tables = {row[0] for row in rows}
    return tuple(
        TablePresence(table_name=table_name, exists=table_name in existing_tables)
        for table_name in list_expected_tables()
    )


def _contact_type_raw_counts(
    connection: duckdb.DuckDBPyConnection,
) -> tuple[CountByLabel, ...]:
    return _count_by_label(
        connection,
        f"""
        SELECT
            CASE
                WHEN {MISSING_RAW_TYPE_SQL}
                THEN '{MISSING_VALUE_LABEL}'
                ELSE contact_type_raw
            END,
            COUNT(*)
        FROM raw_contacts
        GROUP BY 1
        ORDER BY 1
        """,
    )


def _distinct_contact_type_raw_count(connection: duckdb.DuckDBPyConnection) -> int:
    return _scalar(
        connection,
        """
        SELECT COUNT(DISTINCT contact_type_raw)
        FROM raw_contacts
        WHERE NOT (
            contact_type_raw IS NULL
            OR trim(contact_type_raw) = ''
            OR lower(trim(contact_type_raw)) = 'false'
            OR trim(contact_type_raw) = '[]'
        )
        """,
    )


def _category_stage_counts(
    connection: duckdb.DuckDBPyConnection,
) -> tuple[CountByStage, ...]:
    rows = connection.execute(
        """
        SELECT category_id, stage_id, COUNT(*)
        FROM raw_deals
        GROUP BY category_id, stage_id
        ORDER BY category_id NULLS FIRST, stage_id
        """
    ).fetchall()
    return tuple(
        CountByStage(category_id=row[0], stage_id=row[1], count=row[2])
        for row in rows
    )


def _deal_date_range(connection: duckdb.DuckDBPyConnection) -> DateRange:
    row = connection.execute(
        """
        SELECT
            MIN(created_at),
            MAX(created_at),
            MIN(closed_at),
            MAX(closed_at)
        FROM raw_deals
        """
    ).fetchone()
    return DateRange(
        min_created_at=row[0],
        max_created_at=row[1],
        min_closed_at=row[2],
        max_closed_at=row[3],
    )


def _normalization_profile(
    connection: duckdb.DuckDBPyConnection,
) -> NormalizationProfile:
    contacts_count = _scalar(connection, "SELECT COUNT(*) FROM normalized_contacts")
    deals_count = _scalar(connection, "SELECT COUNT(*) FROM normalized_deals")
    contacts_undefined_type = _scalar(
        connection,
        """
        SELECT COUNT(*)
        FROM normalized_contacts
        WHERE contact_type_normalized = ?
        """,
        [UNDEFINED_VALUE],
    )
    contacts_undefined_region = _scalar(
        connection,
        """
        SELECT COUNT(*)
        FROM normalized_contacts
        WHERE region_normalized = ?
        """,
        [UNDEFINED_VALUE],
    )
    deals_undefined_type = _scalar(
        connection,
        """
        SELECT COUNT(*)
        FROM normalized_deals
        WHERE contact_type_normalized = ?
        """,
        [UNDEFINED_VALUE],
    )
    deals_undefined_region = _scalar(
        connection,
        """
        SELECT COUNT(*)
        FROM normalized_deals
        WHERE region_normalized = ?
        """,
        [UNDEFINED_VALUE],
    )
    return NormalizationProfile(
        normalized_contacts_undefined_type_count=contacts_undefined_type,
        normalized_contacts_undefined_region_count=contacts_undefined_region,
        normalized_deals_undefined_type_count=deals_undefined_type,
        normalized_deals_undefined_region_count=deals_undefined_region,
        normalized_contacts_type_mostly_undefined=_is_mostly(
            contacts_undefined_type, contacts_count
        ),
        normalized_contacts_region_mostly_undefined=_is_mostly(
            contacts_undefined_region, contacts_count
        ),
        normalized_deals_type_mostly_undefined=_is_mostly(
            deals_undefined_type, deals_count
        ),
        normalized_deals_region_mostly_undefined=_is_mostly(
            deals_undefined_region, deals_count
        ),
    )


def _raw_values_without_active_rule(
    connection: duckdb.DuckDBPyConnection,
) -> tuple[str, ...]:
    rows = connection.execute(
        """
        SELECT DISTINCT contacts.contact_type_raw
        FROM raw_contacts contacts
        LEFT JOIN contact_type_rules rules
            ON rules.raw_value = contacts.contact_type_raw
            AND rules.is_active = true
        WHERE contacts.contact_type_raw IS NOT NULL
            AND trim(contacts.contact_type_raw) <> ''
            AND lower(trim(contacts.contact_type_raw)) <> 'false'
            AND trim(contacts.contact_type_raw) <> '[]'
            AND rules.raw_value IS NULL
        ORDER BY contacts.contact_type_raw
        """
    ).fetchall()
    return tuple(row[0] for row in rows)


def _type_region_counts(
    connection: duckdb.DuckDBPyConnection,
) -> tuple[CountByTypeRegion, ...]:
    rows = connection.execute(
        """
        SELECT contact_type_normalized, region_normalized, COUNT(*)
        FROM normalized_deals
        GROUP BY contact_type_normalized, region_normalized
        ORDER BY contact_type_normalized, region_normalized
        """
    ).fetchall()
    return tuple(
        CountByTypeRegion(
            contact_type_normalized=row[0],
            region_normalized=row[1],
            count=row[2],
        )
        for row in rows
    )


def _count_by_label(
    connection: duckdb.DuckDBPyConnection,
    query: str,
) -> tuple[CountByLabel, ...]:
    return tuple(
        CountByLabel(label=row[0], count=row[1])
        for row in connection.execute(query).fetchall()
    )


def _scalar(
    connection: duckdb.DuckDBPyConnection,
    query: str,
    params: list[object] | None = None,
) -> int:
    value = connection.execute(query, params or []).fetchone()[0]
    return int(value or 0)


def _is_mostly(part: int, total: int) -> bool:
    if total == 0:
        return False
    return part * 2 > total
