from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from app.bitrix.allowlist import BITRIX_STAGE_ENTITY_ID, build_contact_select, build_deal_select


BitrixTransport = Callable[[str, dict[str, Any]], dict[str, Any]]

READ_ONLY_METHODS = frozenset(
    {
        "crm.contact.fields",
        "crm.deal.fields",
        "crm.contact.list",
        "crm.deal.list",
        "crm.deal.contact.items.get",
        "crm.status.list",
    }
)


class BitrixClientError(RuntimeError):
    pass


class BitrixConfigurationError(BitrixClientError):
    pass


class BitrixHttpError(BitrixClientError):
    pass


class BitrixApiError(BitrixClientError):
    pass


class BitrixUnexpectedResponseError(BitrixClientError):
    pass


class BitrixClient:
    def __init__(
        self,
        webhook_url: str | None,
        *,
        page_size: int = 50,
        transport: BitrixTransport | None = None,
    ) -> None:
        if not webhook_url or not webhook_url.strip():
            raise BitrixConfigurationError("Bitrix webhook URL is not configured.")
        if page_size < 1 or page_size > 50:
            raise BitrixConfigurationError("Bitrix page size must be between 1 and 50.")

        self._webhook_url = webhook_url.rstrip("/") + "/"
        self._page_size = page_size
        self._transport = transport or self._http_transport

    def get_contact_fields(self) -> dict[str, Any]:
        result = self._call("crm.contact.fields", {})
        if not isinstance(result, dict):
            raise BitrixUnexpectedResponseError("Bitrix contact fields response is invalid.")
        return result

    def get_deal_fields(self) -> dict[str, Any]:
        result = self._call("crm.deal.fields", {})
        if not isinstance(result, dict):
            raise BitrixUnexpectedResponseError("Bitrix deal fields response is invalid.")
        return result

    def list_contacts(self, contact_type_field: str | None = None) -> list[dict[str, Any]]:
        return list(
            self._list_method(
                "crm.contact.list",
                {
                    "select": list(build_contact_select(contact_type_field)),
                    "order": {"ID": "ASC"},
                },
            )
        )

    def list_deals(self) -> list[dict[str, Any]]:
        return list(
            self._list_method(
                "crm.deal.list",
                {
                    "select": list(build_deal_select()),
                    "order": {"ID": "ASC"},
                },
            )
        )

    def list_deals_for_contact(self, contact_id: int) -> list[dict[str, Any]]:
        return list(
            self._list_method(
                "crm.deal.list",
                {
                    "filter": {"CONTACT_ID": contact_id},
                    "select": list(build_deal_select()),
                    "order": {"ID": "ASC"},
                },
            )
        )

    def get_deal_contact_links(self, deal_id: int) -> list[dict[str, Any]]:
        result = self._call("crm.deal.contact.items.get", {"id": deal_id})
        if isinstance(result, list):
            return _dict_items(result, "deal-contact links")
        if isinstance(result, dict) and isinstance(result.get("items"), list):
            return _dict_items(result["items"], "deal-contact links")
        raise BitrixUnexpectedResponseError("Bitrix deal-contact links response is invalid.")

    def list_stages(self) -> list[dict[str, Any]]:
        return list(
            self._list_method(
                "crm.status.list",
                {
                    "filter": {"ENTITY_ID": BITRIX_STAGE_ENTITY_ID},
                    "order": {"SORT": "ASC"},
                },
            )
        )

    def _list_method(
        self,
        method: str,
        params: dict[str, Any],
    ) -> Iterable[dict[str, Any]]:
        start: int | None = 0
        while start is not None:
            page_params = dict(params)
            page_params["start"] = start
            page_params["limit"] = self._page_size
            response = self._call_full(method, page_params)
            result = response.get("result")
            rows = _extract_list_result(result, method)
            yield from rows
            start = _extract_next(response)

    def _call(self, method: str, params: dict[str, Any]) -> Any:
        return self._call_full(method, params)["result"]

    def _call_full(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method not in READ_ONLY_METHODS:
            raise BitrixConfigurationError("Bitrix method is not allowed for this read-only client.")

        response = self._transport(method, params)
        if not isinstance(response, dict):
            raise BitrixUnexpectedResponseError("Bitrix response is not an object.")
        if "error" in response:
            error_code = str(response.get("error") or "unknown_error")
            raise BitrixApiError(f"Bitrix API error: {error_code}.")
        if "result" not in response:
            raise BitrixUnexpectedResponseError("Bitrix response does not contain result.")
        return response

    def _http_transport(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        url = self._build_method_url(method)
        body = json.dumps(params).encode("utf-8")
        request = Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                payload = response.read()
        except HTTPError as exc:
            raise BitrixHttpError(f"Bitrix HTTP error: {exc.code}.") from exc
        except URLError as exc:
            raise BitrixHttpError("Bitrix HTTP request failed.") from exc

        try:
            decoded = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise BitrixUnexpectedResponseError("Bitrix response is not valid JSON.") from exc

        if not isinstance(decoded, dict):
            raise BitrixUnexpectedResponseError("Bitrix response is not an object.")
        return decoded

    def _build_method_url(self, method: str) -> str:
        return urljoin(self._webhook_url, f"{method}.json")


def _extract_list_result(result: Any, method: str) -> list[dict[str, Any]]:
    if isinstance(result, list):
        return _dict_items(result, method)
    if isinstance(result, dict) and isinstance(result.get("items"), list):
        return _dict_items(result["items"], method)
    raise BitrixUnexpectedResponseError(f"Bitrix {method} result is not a list.")


def _dict_items(items: list[Any], label: str) -> list[dict[str, Any]]:
    if not all(isinstance(item, dict) for item in items):
        raise BitrixUnexpectedResponseError(f"Bitrix {label} contains invalid rows.")
    return items


def _extract_next(response: dict[str, Any]) -> int | None:
    next_value = response.get("next")
    if next_value is None:
        return None
    try:
        return int(next_value)
    except (TypeError, ValueError) as exc:
        raise BitrixUnexpectedResponseError("Bitrix pagination marker is invalid.") from exc
