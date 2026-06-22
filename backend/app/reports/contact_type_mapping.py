from __future__ import annotations

import ast
from dataclasses import dataclass

import duckdb


@dataclass(frozen=True)
class RawCombinationCount:
    raw_combination: str
    count: int


@dataclass(frozen=True)
class ContactTypeOptionAggregate:
    option_id: int
    contacts_count: int
    observed_raw_combinations: tuple[RawCombinationCount, ...]


def get_contact_type_option_aggregates(
    connection: duckdb.DuckDBPyConnection,
) -> tuple[ContactTypeOptionAggregate, ...]:
    rows = connection.execute(
        """
        SELECT contact_type_raw, COUNT(*)
        FROM raw_contacts
        WHERE contact_type_raw IS NOT NULL
            AND trim(contact_type_raw) <> ''
            AND lower(trim(contact_type_raw)) <> 'false'
            AND trim(contact_type_raw) <> '[]'
        GROUP BY contact_type_raw
        ORDER BY contact_type_raw
        """
    ).fetchall()

    combinations_by_option: dict[int, list[RawCombinationCount]] = {}
    for raw_value, count in rows:
        option_ids = _parse_raw_option_ids(raw_value)
        if not option_ids:
            continue
        combination = RawCombinationCount(
            raw_combination=str(raw_value),
            count=int(count),
        )
        for option_id in option_ids:
            combinations_by_option.setdefault(option_id, []).append(combination)

    return tuple(
        ContactTypeOptionAggregate(
            option_id=option_id,
            contacts_count=sum(row.count for row in combinations),
            observed_raw_combinations=tuple(
                sorted(combinations, key=lambda row: row.raw_combination)
            ),
        )
        for option_id, combinations in sorted(combinations_by_option.items())
    )


def format_raw_combination_summary(
    combinations: tuple[RawCombinationCount, ...],
) -> str:
    return "; ".join(
        f"{combination.raw_combination} ({combination.count})"
        for combination in combinations
    )


def _parse_raw_option_ids(raw_value: object) -> tuple[int, ...]:
    if raw_value in (None, ""):
        return ()

    try:
        parsed = ast.literal_eval(str(raw_value))
    except (SyntaxError, ValueError):
        return ()

    if isinstance(parsed, int):
        values = [parsed]
    elif isinstance(parsed, (list, tuple)):
        values = parsed
    else:
        return ()

    option_ids: list[int] = []
    for value in values:
        try:
            option_id = int(value)
        except (TypeError, ValueError):
            continue
        if option_id > 0 and option_id not in option_ids:
            option_ids.append(option_id)

    return tuple(option_ids)
