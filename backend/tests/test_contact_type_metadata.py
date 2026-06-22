import duckdb

from app.bitrix.contact_type_metadata import extract_contact_type_enum_options
from app.reports.contact_type_mapping import (
    format_raw_combination_summary,
    get_contact_type_option_aggregates,
)
from app.storage import initialize_schema


def test_extract_contact_type_enum_options_from_contact_fields_metadata() -> None:
    metadata = {
        "UF_CRM_CONTACT_TYPE": {
            "type": "enumeration",
            "items": [
                {"ID": "59", "VALUE": "Client"},
                {"ID": 65, "VALUE": "Partner"},
                {"ID": "", "VALUE": "Ignored"},
                {"ID": "bad", "VALUE": "Ignored"},
                {"ID": "67", "VALUE": ""},
            ],
        }
    }

    options = extract_contact_type_enum_options(
        metadata,
        contact_type_field="UF_CRM_CONTACT_TYPE",
    )

    assert [(option.option_id, option.label) for option in options] == [
        (59, "Client"),
        (65, "Partner"),
    ]


def test_contact_type_option_aggregates_use_only_raw_type_counts() -> None:
    with duckdb.connect(database=":memory:") as connection:
        initialize_schema(connection)
        connection.executemany(
            """
            INSERT INTO raw_contacts (contact_id, contact_name, contact_type_raw)
            VALUES (?, ?, ?)
            """,
            [
                (1, "Synthetic Contact 1", "[59]"),
                (2, "Synthetic Contact 2", "[59, 65]"),
                (3, "Synthetic Contact 3", "[65, 59]"),
                (4, "Synthetic Contact 4", "[]"),
                (5, "Synthetic Contact 5", "False"),
                (6, "Synthetic Contact 6", None),
            ],
        )

        aggregates = get_contact_type_option_aggregates(connection)

    by_id = {aggregate.option_id: aggregate for aggregate in aggregates}

    assert set(by_id) == {59, 65}
    assert by_id[59].contacts_count == 3
    assert by_id[65].contacts_count == 2
    assert format_raw_combination_summary(by_id[65].observed_raw_combinations) == (
        "[59, 65] (1); [65, 59] (1)"
    )
