from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from app.domain import (
    ContactSnapshot,
    ContactTypeRule,
    CurrencyRateSnapshot,
    DealContactLink,
    DealSnapshot,
    StageSnapshot,
)


def utc_datetime(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


@dataclass(frozen=True)
class SyntheticDataset:
    contacts: tuple[ContactSnapshot, ...]
    deals: tuple[DealSnapshot, ...]
    deal_contact_links: tuple[DealContactLink, ...]
    stages: tuple[StageSnapshot, ...]
    contact_type_rules: tuple[ContactTypeRule, ...]
    currency_rates: tuple[CurrencyRateSnapshot, ...]


def build_synthetic_dataset() -> SyntheticDataset:
    contacts = tuple(
        ContactSnapshot(
            contact_id=contact_id,
            contact_name=f"Synthetic Contact {contact_id}",
            contact_type_raw=contact_type_raw,
        )
        for contact_id, contact_type_raw in (
            (1, "synthetic-key"),
            (2, "synthetic-direct"),
            (3, "synthetic-partner-a"),
            (4, "synthetic-partner-b"),
            (5, "synthetic-retail"),
            (6, "synthetic-retail"),
            (7, "synthetic-distributor"),
            (8, "synthetic-service"),
            (9, "synthetic-direct"),
            (10, None),
        )
    )

    stages = (
        StageSnapshot(stage_id="SYN:WON", category_id=1, status_group="won"),
        StageSnapshot(stage_id="SYN:OPEN", category_id=1, status_group="open"),
        StageSnapshot(stage_id="SYN:LOST", category_id=1, status_group="lost"),
    )

    contact_type_rules = (
        ContactTypeRule(
            raw_value="synthetic-key",
            normalized_type="Synthetic Key",
            priority=10,
            region="Synthetic North",
        ),
        ContactTypeRule(
            raw_value="synthetic-direct",
            normalized_type="Synthetic Direct",
            priority=20,
            region="Synthetic North",
        ),
        ContactTypeRule(
            raw_value="synthetic-partner-a",
            normalized_type="Synthetic Partner A",
            priority=30,
            region="Synthetic East",
        ),
        ContactTypeRule(
            raw_value="synthetic-partner-b",
            normalized_type="Synthetic Partner B",
            priority=30,
            region="Synthetic West",
        ),
        ContactTypeRule(
            raw_value="synthetic-retail",
            normalized_type="Synthetic Retail",
            priority=40,
            region="Synthetic South",
        ),
        ContactTypeRule(
            raw_value="synthetic-distributor",
            normalized_type="Synthetic Distributor",
            priority=50,
            region="Synthetic Central",
        ),
        ContactTypeRule(
            raw_value="synthetic-service",
            normalized_type="Synthetic Service",
            priority=60,
            region="Synthetic Central",
            is_active=False,
        ),
    )

    currency_rates = tuple(
        CurrencyRateSnapshot(
            currency=currency,
            rate_date=rate_date,
            source_rate_byn=source_rate_byn,
            usd_rate_byn=Decimal("3.30000000"),
            rate_fetched_at=utc_datetime(rate_date.year, rate_date.month, rate_date.day + 1),
        )
        for rate_date in (date(2023, 1, 1), date(2025, 1, 1))
        for currency, source_rate_byn in (
            ("USD", Decimal("3.30000000")),
            ("EUR", Decimal("3.60000000")),
            ("BYN", Decimal("1.00000000")),
        )
    )

    deal_specs = (
        (1, "Synthetic Deal 001", "120000.00", "USD", utc_datetime(2023, 1, 10), utc_datetime(2023, 2, 10), "SYN:WON", "won"),
        (2, "Synthetic Deal 002", "110000.00", "EUR", utc_datetime(2023, 3, 11), utc_datetime(2023, 4, 11), "SYN:WON", "won"),
        (3, "Synthetic Deal 003", "90000.00", "USD", utc_datetime(2023, 5, 12), utc_datetime(2023, 6, 12), "SYN:WON", "won"),
        (4, "Synthetic Deal 004", "80000.00", "BYN", utc_datetime(2023, 7, 13), utc_datetime(2023, 8, 13), "SYN:WON", "won"),
        (5, "Synthetic Deal 005", "70000.00", "USD", utc_datetime(2024, 1, 5), utc_datetime(2024, 2, 5), "SYN:WON", "won"),
        (6, "Synthetic Deal 006", "60000.00", "EUR", utc_datetime(2024, 3, 6), utc_datetime(2024, 4, 6), "SYN:WON", "won"),
        (7, "Synthetic Deal 007", "50000.00", "USD", utc_datetime(2024, 5, 7), utc_datetime(2024, 6, 7), "SYN:WON", "won"),
        (8, "Synthetic Deal 008", "40000.00", "BYN", utc_datetime(2024, 7, 8), utc_datetime(2024, 8, 8), "SYN:WON", "won"),
        (9, "Synthetic Deal 009", "30000.00", "USD", utc_datetime(2025, 1, 9), utc_datetime(2025, 2, 9), "SYN:WON", "won"),
        (10, "Synthetic Deal 010", "20000.00", "EUR", utc_datetime(2025, 3, 10), utc_datetime(2025, 4, 10), "SYN:WON", "won"),
        (11, "Synthetic Deal 011", "15000.00", "USD", utc_datetime(2025, 5, 11), utc_datetime(2025, 6, 11), "SYN:WON", "won"),
        (12, "Synthetic Deal 012", "14000.00", "BYN", utc_datetime(2025, 7, 12), utc_datetime(2025, 8, 12), "SYN:WON", "won"),
        (13, "Synthetic Deal 013", "13000.00", "USD", utc_datetime(2025, 9, 13), utc_datetime(2025, 10, 13), "SYN:WON", "won"),
        (14, "Synthetic Deal 014", "12000.00", "EUR", utc_datetime(2025, 11, 14), utc_datetime(2025, 12, 14), "SYN:WON", "won"),
        (15, "Synthetic Deal 015", "11000.00", "USD", utc_datetime(2026, 1, 15), utc_datetime(2026, 2, 15), "SYN:WON", "won"),
        (16, "Synthetic Deal 016", "10000.00", "BYN", utc_datetime(2026, 2, 16), utc_datetime(2026, 3, 16), "SYN:WON", "won"),
        (17, "Synthetic Deal 017", "9000.00", "USD", utc_datetime(2026, 3, 17), utc_datetime(2026, 4, 17), "SYN:WON", "won"),
        (18, "Synthetic Deal 018", "8000.00", "EUR", utc_datetime(2026, 4, 18), utc_datetime(2026, 5, 18), "SYN:WON", "won"),
        (19, "Synthetic Deal 019", "7000.00", "USD", utc_datetime(2026, 5, 19), utc_datetime(2026, 6, 1), "SYN:WON", "won"),
        (20, "Synthetic Deal 020", "6500.00", "BYN", utc_datetime(2026, 6, 1), utc_datetime(2026, 6, 10), "SYN:WON", "won"),
        (21, "Synthetic Deal 021", "45000.00", "USD", utc_datetime(2024, 1, 1), None, "SYN:OPEN", "open"),
        (22, "Synthetic Deal 022", "32000.00", "EUR", utc_datetime(2025, 10, 1), None, "SYN:OPEN", "open"),
        (23, "Synthetic Deal 023", "28000.00", "BYN", utc_datetime(2026, 1, 20), None, "SYN:OPEN", "open"),
        (24, "Synthetic Deal 024", "17000.00", "USD", utc_datetime(2026, 3, 22), None, "SYN:OPEN", "open"),
        (25, "Synthetic Deal 025", "9000.00", "EUR", utc_datetime(2026, 6, 5), None, "SYN:OPEN", "open"),
        (26, "Synthetic Deal 026", "25000.00", "USD", utc_datetime(2024, 2, 1), utc_datetime(2024, 3, 1), "SYN:LOST", "lost"),
        (27, "Synthetic Deal 027", "22000.00", "EUR", utc_datetime(2024, 6, 1), utc_datetime(2024, 7, 1), "SYN:LOST", "lost"),
        (28, "Synthetic Deal 028", "18000.00", "BYN", utc_datetime(2025, 2, 1), utc_datetime(2025, 3, 1), "SYN:LOST", "lost"),
        (29, "Synthetic Deal 029", "14000.00", "USD", utc_datetime(2025, 8, 1), utc_datetime(2025, 9, 1), "SYN:LOST", "lost"),
        (30, "Synthetic Deal 030", "10000.00", "EUR", utc_datetime(2026, 5, 1), utc_datetime(2026, 5, 20), "SYN:LOST", "lost"),
    )

    deals = tuple(
        DealSnapshot(
            deal_id=deal_id,
            deal_name=name,
            amount_original=Decimal(amount),
            currency_original=currency,
            created_at=created_at,
            closed_at=closed_at,
            stage_id=stage_id,
            category_id=1,
            status_group=status_group,
        )
        for deal_id, name, amount, currency, created_at, closed_at, stage_id, status_group in deal_specs
    )

    deal_contact_links = (
        DealContactLink(deal_id=1, contact_id=1, is_primary=True),
        DealContactLink(deal_id=2, contact_id=1, is_primary=True),
        DealContactLink(deal_id=3, contact_id=1, is_primary=True),
        DealContactLink(deal_id=4, contact_id=1, is_primary=True),
        DealContactLink(deal_id=5, contact_id=2, is_primary=True),
        DealContactLink(deal_id=6, contact_id=2, is_primary=True),
        DealContactLink(deal_id=7, contact_id=3),
        DealContactLink(deal_id=7, contact_id=4, is_primary=True),
        DealContactLink(deal_id=8, contact_id=3, is_primary=True),
        DealContactLink(deal_id=9, contact_id=5, is_primary=True),
        DealContactLink(deal_id=10, contact_id=6, is_primary=True),
        DealContactLink(deal_id=11, contact_id=7, is_primary=True),
        DealContactLink(deal_id=12, contact_id=8, is_primary=True),
        DealContactLink(deal_id=13, contact_id=9, is_primary=True),
        DealContactLink(deal_id=14, contact_id=10, is_primary=True),
        DealContactLink(deal_id=15, contact_id=2, is_primary=True),
        DealContactLink(deal_id=16, contact_id=3, is_primary=True),
        DealContactLink(deal_id=17, contact_id=4, is_primary=True),
        DealContactLink(deal_id=18, contact_id=5, is_primary=True),
        DealContactLink(deal_id=19, contact_id=6, is_primary=True),
        DealContactLink(deal_id=20, contact_id=9, is_primary=True),
        DealContactLink(deal_id=21, contact_id=2, is_primary=True),
        DealContactLink(deal_id=22, contact_id=3, is_primary=True),
        DealContactLink(deal_id=23, contact_id=4, is_primary=True),
        DealContactLink(deal_id=24, contact_id=5, is_primary=True),
        DealContactLink(deal_id=25, contact_id=6, is_primary=True),
        DealContactLink(deal_id=26, contact_id=7, is_primary=True),
        DealContactLink(deal_id=27, contact_id=8, is_primary=True),
        DealContactLink(deal_id=28, contact_id=9, is_primary=True),
        DealContactLink(deal_id=29, contact_id=10, is_primary=True),
    )

    return SyntheticDataset(
        contacts=contacts,
        deals=deals,
        deal_contact_links=deal_contact_links,
        stages=stages,
        contact_type_rules=contact_type_rules,
        currency_rates=currency_rates,
    )
