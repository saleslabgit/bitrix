from __future__ import annotations

import duckdb

from app.domain import ContactTypeRule, MISSING_CONTACT_TYPE_RULE_RAW_VALUE


APPROVED_CONTACT_TYPE_RULES: tuple[ContactTypeRule, ...] = (
    ContactTypeRule(
        raw_value="59",
        normalized_type="Подрядчик",
        region="Беларусь",
        priority=3,
        is_active=True,
    ),
    ContactTypeRule(
        raw_value="61",
        normalized_type="Дизайнер",
        region="Беларусь",
        priority=1,
        is_active=True,
    ),
    ContactTypeRule(
        raw_value="65",
        normalized_type="Конечный клиент",
        region="Без региона",
        priority=4,
        is_active=True,
    ),
    ContactTypeRule(
        raw_value="67",
        normalized_type="Поставщик",
        region="Без региона",
        priority=99,
        is_active=False,
    ),
    ContactTypeRule(
        raw_value="151",
        normalized_type="Дилер",
        region="Беларусь",
        priority=2,
        is_active=True,
    ),
    ContactTypeRule(
        raw_value="245",
        normalized_type="Другое",
        region="Без региона",
        priority=99,
        is_active=False,
    ),
    ContactTypeRule(
        raw_value="247",
        normalized_type="Проектировщик",
        region="Беларусь",
        priority=3,
        is_active=True,
    ),
    ContactTypeRule(
        raw_value="249",
        normalized_type="Другое",
        region="Без региона",
        priority=99,
        is_active=False,
    ),
    ContactTypeRule(
        raw_value="251",
        normalized_type="Дилер",
        region="Беларусь",
        priority=2,
        is_active=True,
    ),
    ContactTypeRule(
        raw_value="253",
        normalized_type="Другое",
        region="Без региона",
        priority=99,
        is_active=False,
    ),
    ContactTypeRule(
        raw_value="255",
        normalized_type="Дизайнер",
        region="Россия",
        priority=1,
        is_active=True,
    ),
    ContactTypeRule(
        raw_value="469",
        normalized_type="Другое",
        region="Без региона",
        priority=99,
        is_active=False,
    ),
    ContactTypeRule(
        raw_value="1943",
        normalized_type="Партнер",
        region="Без региона",
        priority=99,
        is_active=False,
    ),
    ContactTypeRule(
        raw_value="1945",
        normalized_type="Другое",
        region="Без региона",
        priority=99,
        is_active=False,
    ),
    ContactTypeRule(
        raw_value="2341",
        normalized_type="Дилер",
        region="Россия",
        priority=2,
        is_active=True,
    ),
    ContactTypeRule(
        raw_value="2343",
        normalized_type="Подрядчик",
        region="Россия",
        priority=3,
        is_active=True,
    ),
    ContactTypeRule(
        raw_value="2345",
        normalized_type="Подрядчик",
        region="Россия",
        priority=3,
        is_active=True,
    ),
    ContactTypeRule(
        raw_value="2785",
        normalized_type="Подрядчик",
        region="Россия",
        priority=3,
        is_active=True,
    ),
    ContactTypeRule(
        raw_value="2829",
        normalized_type="Подрядчик",
        region="Беларусь",
        priority=3,
        is_active=True,
    ),
    ContactTypeRule(
        raw_value=MISSING_CONTACT_TYPE_RULE_RAW_VALUE,
        normalized_type="Конечный клиент",
        region="Без региона",
        priority=4,
        is_active=True,
    ),
)


def replace_contact_type_rules(
    connection: duckdb.DuckDBPyConnection,
    rules: tuple[ContactTypeRule, ...] = APPROVED_CONTACT_TYPE_RULES,
) -> int:
    connection.execute("DELETE FROM contact_type_rules")
    connection.executemany(
        """
        INSERT INTO contact_type_rules (
            raw_value,
            normalized_type,
            priority,
            region,
            is_active
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                rule.raw_value,
                rule.normalized_type,
                rule.priority,
                rule.region,
                rule.is_active,
            )
            for rule in rules
        ],
    )
    return len(rules)
