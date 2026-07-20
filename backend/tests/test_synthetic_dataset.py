from datetime import datetime, timezone

from app.domain import (
    ContactSnapshot,
    ContactTypeRule,
    CurrencyRateSnapshot,
    DealContactLink,
    DealSnapshot,
    StageSnapshot,
)
from fixtures.synthetic_dataset import build_synthetic_dataset


ALLOWED_MODEL_FIELDS = {
    ContactSnapshot: {"contact_id", "contact_name", "contact_type_raw"},
    DealSnapshot: {
        "deal_id",
        "deal_name",
        "amount_original",
        "currency_original",
        "created_at",
        "closed_at",
        "stage_id",
        "category_id",
        "status_group",
        "kev_held",
    },
    DealContactLink: {
        "deal_id",
        "contact_id",
        "is_primary",
        "sort_order",
        "role_id",
    },
    StageSnapshot: {"stage_id", "category_id", "status_group"},
    ContactTypeRule: {
        "raw_value",
        "normalized_type",
        "priority",
        "region",
        "is_active",
    },
    CurrencyRateSnapshot: {
        "currency",
        "rate_date",
        "source_rate_byn",
        "usd_rate_byn",
        "rate_source",
        "rate_fetched_at",
    },
}


def test_synthetic_dataset_has_required_shape() -> None:
    dataset = build_synthetic_dataset()

    assert len(dataset.contacts) >= 10
    assert len(dataset.deals) >= 30
    assert {deal.status_group for deal in dataset.deals} == {"won", "open", "lost"}
    assert len({deal.currency_original for deal in dataset.deals}) >= 3

    linked_deal_counts = {
        deal.deal_id: sum(
            link.deal_id == deal.deal_id for link in dataset.deal_contact_links
        )
        for deal in dataset.deals
    }

    assert any(link_count > 1 for link_count in linked_deal_counts.values())
    assert any(link_count == 0 for link_count in linked_deal_counts.values())
    assert any(deal.status_group == "open" for deal in dataset.deals)
    assert any(deal.status_group == "lost" for deal in dataset.deals)


def test_synthetic_dataset_covers_edge_cases_without_analytics() -> None:
    dataset = build_synthetic_dataset()
    won_deals = [deal for deal in dataset.deals if deal.status_group == "won"]

    priorities = [rule.priority for rule in dataset.contact_type_rules]
    assert len(priorities) != len(set(priorities))

    contact_one_won_deals = [
        deal
        for deal in won_deals
        if any(
            link.deal_id == deal.deal_id and link.contact_id == 1
            for link in dataset.deal_contact_links
        )
    ]
    assert len(contact_one_won_deals) >= 3
    assert all(
        deal.closed_at is not None
        and deal.closed_at < datetime(2025, 6, 21, tzinfo=timezone.utc)
        for deal in contact_one_won_deals
    )

    won_deal_counts_by_contact = {
        contact.contact_id: sum(
            any(
                link.deal_id == deal.deal_id and link.contact_id == contact.contact_id
                for link in dataset.deal_contact_links
            )
            for deal in won_deals
        )
        for contact in dataset.contacts
    }
    assert any(won_count == 1 for won_count in won_deal_counts_by_contact.values())

    long_open_deals = [
        deal
        for deal in dataset.deals
        if deal.status_group == "open"
        and deal.closed_at is None
        and deal.created_at < datetime(2025, 6, 21, tzinfo=timezone.utc)
    ]
    assert long_open_deals


def test_synthetic_dataset_uses_only_allowed_domain_fields() -> None:
    dataset = build_synthetic_dataset()

    model_groups = (
        dataset.contacts,
        dataset.deals,
        dataset.deal_contact_links,
        dataset.stages,
        dataset.contact_type_rules,
        dataset.currency_rates,
    )

    for group in model_groups:
        for model in group:
            assert set(type(model).model_fields) == ALLOWED_MODEL_FIELDS[type(model)]
