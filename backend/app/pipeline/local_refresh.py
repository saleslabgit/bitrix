from __future__ import annotations

from dataclasses import dataclass

import duckdb

from app.pipeline.approved_contact_type_rules import replace_contact_type_rules
from app.pipeline.normalization import normalize_local_data
from app.storage import initialize_schema
from app.storage.status import count_current_rows


@dataclass(frozen=True)
class LocalRenormalizationResult:
    rules_count: int
    active_rules_count: int
    raw_contacts_count: int
    raw_deals_count: int
    raw_links_count: int
    normalized_contacts_count: int
    normalized_deals_count: int


def apply_approved_rules_and_renormalize(
    connection: duckdb.DuckDBPyConnection,
) -> LocalRenormalizationResult:
    initialize_schema(connection)
    try:
        connection.execute("BEGIN TRANSACTION")
        rules_count = replace_contact_type_rules(connection)
        normalize_local_data(connection)
        counts = count_current_rows(connection)
        active_rules_count = connection.execute(
            "SELECT COUNT(*) FROM contact_type_rules WHERE is_active = true"
        ).fetchone()[0]
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise

    return LocalRenormalizationResult(
        rules_count=rules_count,
        active_rules_count=active_rules_count,
        **counts,
    )
