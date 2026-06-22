from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import urlopen

import duckdb

from app.storage import initialize_schema


NBRB_BASE_URL = "https://api.nbrb.by/exrates/"
BYN_CURRENCY = "BYN"
USD_CURRENCY = "USD"
SUPPORTED_NBRB_CURRENCIES = ("EUR", "RUB", "USD")

JsonTransport = Callable[[str], object]


@dataclass(frozen=True)
class CurrencyRateLoadResult:
    currencies: tuple[str, ...]
    start_date: date
    end_date: date
    rows_loaded: int
    rate_source: str = "NBRB"


@dataclass(frozen=True)
class _CurrencyMetadata:
    cur_id: int
    scale: Decimal
    start_date: date
    end_date: date


class NbrbRateClient:
    def __init__(
        self,
        *,
        base_url: str = NBRB_BASE_URL,
        transport: JsonTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/") + "/"
        self._transport = transport or _default_transport
        self._metadata_cache: list[dict[str, object]] | None = None

    def load_daily_rates(
        self,
        *,
        currencies: tuple[str, ...],
        start_date: date,
        end_date: date,
    ) -> dict[str, dict[date, Decimal]]:
        result: dict[str, dict[date, Decimal]] = {}
        for currency in sorted(set(currencies)):
            if currency == BYN_CURRENCY:
                continue
            rates: dict[date, Decimal] = {}
            for metadata in self._load_metadata_periods(
                currency,
                start_date=start_date,
                end_date=end_date,
            ):
                metadata_start = max(start_date, metadata.start_date)
                metadata_end = min(end_date, metadata.end_date)
                for period_start, period_end in _year_periods(
                    metadata_start,
                    metadata_end,
                ):
                    payload = self._transport(
                        self._url(
                            f"rates/dynamics/{metadata.cur_id}",
                            {
                                "startdate": period_start.isoformat(),
                                "enddate": period_end.isoformat(),
                            },
                        )
                    )
                    if not isinstance(payload, list):
                        raise ValueError("NBRB dynamics response is invalid.")
                    for item in payload:
                        if not isinstance(item, dict):
                            continue
                        rate_date = datetime.fromisoformat(
                            str(item["Date"]).replace("Z", "+00:00")
                        ).date()
                        official_rate = Decimal(str(item["Cur_OfficialRate"]))
                        rates[rate_date] = official_rate / metadata.scale
            result[currency] = rates
        return result

    def _load_metadata_periods(
        self,
        currency: str,
        *,
        start_date: date,
        end_date: date,
    ) -> tuple[_CurrencyMetadata, ...]:
        rows = self._load_all_metadata()
        periods = []
        for row in rows:
            if row.get("Cur_Abbreviation") != currency:
                continue
            period_start = datetime.fromisoformat(
                str(row["Cur_DateStart"]).replace("Z", "+00:00")
            ).date()
            period_end = datetime.fromisoformat(
                str(row["Cur_DateEnd"]).replace("Z", "+00:00")
            ).date()
            if period_start > end_date or period_end < start_date:
                continue
            periods.append(
                _CurrencyMetadata(
                    cur_id=int(row["Cur_ID"]),
                    scale=Decimal(str(row["Cur_Scale"])),
                    start_date=period_start,
                    end_date=period_end,
                )
            )
        if not periods:
            raise ValueError(f"NBRB currency metadata for {currency} is missing.")
        return tuple(sorted(periods, key=lambda period: period.start_date))

    def _load_all_metadata(self) -> list[dict[str, object]]:
        if self._metadata_cache is None:
            payload = self._transport(f"{self._base_url}currencies")
            if not isinstance(payload, list) or not all(
                isinstance(item, dict) for item in payload
            ):
                raise ValueError("NBRB currencies metadata response is invalid.")
            self._metadata_cache = payload
        return self._metadata_cache

    def _url(self, path: str, params: dict[str, str]) -> str:
        return f"{self._base_url}{path}?{urlencode(params)}"


def load_currency_rates_for_raw_deals(
    connection: duckdb.DuckDBPyConnection,
    *,
    client: NbrbRateClient | None = None,
    as_of_date: date | None = None,
) -> CurrencyRateLoadResult | None:
    initialize_schema(connection)
    period = _raw_deal_rate_period(connection, as_of_date=as_of_date)
    if period is None:
        return None

    currencies, start_date, end_date = period
    if end_date < start_date:
        return None

    rate_client = client or NbrbRateClient()
    nbrb_currencies = tuple(
        sorted(
            {
                currency
                for currency in currencies
                if currency != BYN_CURRENCY
            }
            | {USD_CURRENCY}
        )
    )
    rates_by_currency = rate_client.load_daily_rates(
        currencies=nbrb_currencies,
        start_date=start_date,
        end_date=end_date,
    )
    usd_rates = rates_by_currency.get(USD_CURRENCY)
    if not usd_rates:
        raise ValueError("NBRB USD rates are required for local USD analytics.")

    rows: list[tuple[object, ...]] = []
    for rate_date, usd_rate in sorted(usd_rates.items()):
        if BYN_CURRENCY in currencies:
            rows.append(
                (
                    BYN_CURRENCY,
                    rate_date,
                    Decimal("1.00000000"),
                    usd_rate,
                    "NBRB",
                    datetime.now(timezone.utc),
                )
            )
        if USD_CURRENCY in currencies:
            rows.append(
                (
                    USD_CURRENCY,
                    rate_date,
                    usd_rate,
                    usd_rate,
                    "NBRB",
                    datetime.now(timezone.utc),
                )
            )

    for currency in sorted(currencies):
        if currency in {BYN_CURRENCY, USD_CURRENCY}:
            continue
        source_rates = rates_by_currency.get(currency)
        if not source_rates:
            raise ValueError(f"NBRB rates for {currency} are missing.")
        common_dates = sorted(set(source_rates) & set(usd_rates))
        for rate_date in common_dates:
            rows.append(
                (
                    currency,
                    rate_date,
                    source_rates[rate_date],
                    usd_rates[rate_date],
                    "NBRB",
                    datetime.now(timezone.utc),
                )
            )

    connection.execute("BEGIN TRANSACTION")
    try:
        connection.execute("DELETE FROM currency_rates")
        connection.executemany(
            """
            INSERT INTO currency_rates (
                currency,
                rate_date,
                source_rate_byn,
                usd_rate_byn,
                rate_source,
                rate_fetched_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise

    return CurrencyRateLoadResult(
        currencies=currencies,
        start_date=start_date,
        end_date=end_date,
        rows_loaded=len(rows),
    )


def _raw_deal_rate_period(
    connection: duckdb.DuckDBPyConnection,
    *,
    as_of_date: date | None,
) -> tuple[tuple[str, ...], date, date] | None:
    row = connection.execute(
        """
        SELECT
            MIN(CAST(COALESCE(closed_at, created_at) AS DATE)),
            MAX(CAST(COALESCE(closed_at, created_at) AS DATE))
        FROM raw_deals
        """
    ).fetchone()
    if row is None or row[0] is None or row[1] is None:
        return None

    currencies = tuple(
        row[0]
        for row in connection.execute(
            """
            SELECT DISTINCT currency_original
            FROM raw_deals
            ORDER BY currency_original
            """
        ).fetchall()
    )
    unsupported = sorted(
        currency
        for currency in currencies
        if currency not in {*SUPPORTED_NBRB_CURRENCIES, BYN_CURRENCY}
    )
    if unsupported:
        raise ValueError(f"Unsupported currencies for NBRB loader: {', '.join(unsupported)}")

    end_date = min(row[1], as_of_date or date.today())
    return currencies, row[0], end_date


def _year_periods(start_date: date, end_date: date) -> tuple[tuple[date, date], ...]:
    periods: list[tuple[date, date]] = []
    current = start_date
    while current <= end_date:
        period_end = min(date(current.year, 12, 31), end_date)
        periods.append((current, period_end))
        current = date(current.year + 1, 1, 1)
    return tuple(periods)


def _default_transport(url: str) -> object:
    with urlopen(url, timeout=30) as response:
        payload = response.read()
    return json.loads(payload.decode("utf-8"))
