"""Maricopa County Assessor API connector (AZ-only enrichment).

This connector is intentionally conservative:
- It is disabled by default and must be enabled via config.
- It returns None on failures (rate limits, auth, parsing issues) instead of raising.
- It only extracts a small set of high-signal fields and stores raw response in mls_data
  for debugging.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

from config import settings
from mls_connector import MLSConnector
from models import Property, PropertyStatus, PropertyType

logger = logging.getLogger(__name__)


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _safe_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(float(str(value).replace(",", "").strip()))
    except Exception:
        return None


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(str(value).replace(",", "").strip())
    except Exception:
        return None


def _find_first_key(data: Any, keys: list[str]) -> Any:
    """Try to find the first matching key in a dict-like object."""
    if not isinstance(data, dict):
        return None
    for k in keys:
        if k in data and data[k] not in (None, "", [], {}):
            return data[k]
    return None


def _unwrap_first_record(payload: Any) -> Any:
    """Assessor APIs sometimes return {results:[...]}, {data:[...]}, or a list directly."""
    if payload is None:
        return None
    if isinstance(payload, list):
        return payload[0] if payload else None
    if isinstance(payload, dict):
        for key in ("result", "results", "data", "items", "records", "properties"):
            value = payload.get(key)
            if isinstance(value, list) and value:
                return value[0]
        return payload
    return payload


def _deep_find_first(data: Any, keys: list[str]) -> Any:
    """Deep search nested dict/list for the first matching key."""
    if data is None:
        return None
    if isinstance(data, dict):
        for k in keys:
            if k in data and data[k] not in (None, "", [], {}):
                return data[k]
        for v in data.values():
            found = _deep_find_first(v, keys)
            if found not in (None, "", [], {}):
                return found
        return None
    if isinstance(data, list):
        for item in data:
            found = _deep_find_first(item, keys)
            if found not in (None, "", [], {}):
                return found
        return None
    return None


class MaricopaAssessorConnector(MLSConnector):
    """Connector for a Maricopa County Assessor API (exact endpoints vary by vendor).

    This connector supports a simple address-based query that can be configured via:
    - MARICOPA_ASSESSOR_BASE_URL
    - MARICOPA_ASSESSOR_SEARCH_PATH (default: /property)
    - MARICOPA_ASSESSOR_ADDRESS_PARAM (default: address)

    Authentication can be provided via:
    - MARICOPA_ASSESSOR_API_KEY + MARICOPA_ASSESSOR_API_KEY_HEADER (header auth), or
    - MARICOPA_ASSESSOR_API_KEY + MARICOPA_ASSESSOR_API_KEY_QUERY_PARAM (query auth).
    """

    def __init__(self) -> None:
        super().__init__()
        self.base_url = (settings.maricopa_assessor_base_url or "").rstrip("/")
        self.api_key = settings.maricopa_assessor_api_key or ""
        # Official docs use AUTHORIZATION header
        self.api_key_header = settings.maricopa_assessor_api_key_header or "AUTHORIZATION"
        self.api_key_query_param = settings.maricopa_assessor_api_key_query_param or ""
        self.search_path = settings.maricopa_assessor_search_path or "/search/property/"
        self.address_param = settings.maricopa_assessor_address_param or "q"
        self.timeout_seconds = int(settings.maricopa_assessor_timeout_seconds or 30)

        self.last_status_code: Optional[int] = None
        self.last_error: Optional[str] = None
        self.last_endpoint: Optional[str] = None

    def connect(self) -> bool:
        """Mark connector ready if enabled and base URL is configured."""
        if not settings.maricopa_assessor_enabled:
            self.connected = False
            self.last_error = "disabled"
            return False
        if not self.base_url:
            self.connected = False
            self.last_error = "missing_base_url"
            return False
        self.connected = True
        self.last_error = None
        return True

    def disconnect(self) -> None:
        self.connected = False

    def search_properties(self, *args: Any, **kwargs: Any) -> list[Property]:
        """Not implemented: this connector is designed for single property enrichment."""
        return []

    def get_property_by_mls(self, mls_number: str) -> Optional[Property]:
        """Maricopa assessor data is typically keyed by parcel/APN, not MLS number."""
        return None

    def get_property_by_address(
        self, address: str, city: str, state: str, zip_code: str
    ) -> Optional[Property]:
        if not self.connected:
            raise ConnectionError("Not connected to Maricopa Assessor API")

        if not state or str(state).strip().upper() != "AZ":
            return None

        full_address = ", ".join(
            [p for p in [address, city, f"{state} {zip_code}".strip()] if p]
        ).strip()
        if not full_address:
            return None

        url = f"{self.base_url}{self.search_path}"
        self.last_endpoint = url

        # Per official docs: include custom AUTHORIZATION header and user-agent = null.
        headers: Dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "null",
        }
        params: Dict[str, Any] = {self.address_param: full_address}

        if self.api_key and self.api_key_query_param:
            params[self.api_key_query_param] = self.api_key
        elif self.api_key:
            headers[self.api_key_header] = self.api_key

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=self.timeout_seconds)
            self.last_status_code = resp.status_code

            if resp.status_code in (401, 403):
                self.last_error = f"auth_failed: HTTP {resp.status_code}"
                logger.warning(
                    f"Maricopa Assessor auth failed (HTTP {resp.status_code}). Check API key/header settings."
                )
                return None
            if resp.status_code == 429:
                self.last_error = "rate_limited: HTTP 429"
                logger.warning("Maricopa Assessor rate limited (HTTP 429).")
                return None

            resp.raise_for_status()
            payload = resp.json()

            # First call returns search result set; extract APN then hydrate parcel endpoints.
            apn = _safe_str(_deep_find_first(payload, ["apn", "APN", "parcel", "parcelNumber", "parcel_number"]))
            record = _unwrap_first_record(payload)
            if not record and not apn:
                self.last_error = "no_results"
                return None

            # If search result doesn't contain APN directly, try extracting from first record.
            if not apn and record:
                apn = _safe_str(_deep_find_first(record, ["apn", "APN", "parcel", "parcelNumber", "parcel_number"]))

            parcel_payload: Dict[str, Any] = {}
            if apn:
                parcel_payload = self._fetch_parcel_details(apn) or {}

            prop = self._parse_combined(
                search_record=record if isinstance(record, dict) else {},
                parcel_payload=parcel_payload,
                apn=apn,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
            )
            if prop:
                self.last_error = None
            return prop

        except requests.exceptions.Timeout:
            self.last_error = "timeout"
            logger.warning(f"Maricopa Assessor request timed out for {full_address}")
            return None
        except requests.exceptions.RequestException as e:
            self.last_error = f"request_failed: {e}"
            logger.warning(f"Maricopa Assessor request failed for {full_address}: {e}")
            return None
        except Exception as e:
            self.last_error = f"unexpected_error: {e}"
            logger.warning(f"Maricopa Assessor unexpected error for {full_address}: {e}")
            return None

    def _fetch_parcel_details(self, apn: str) -> Optional[Dict[str, Any]]:
        """Hydrate additional parcel endpoints once we have an APN."""
        if not apn:
            return None

        def _get(path: str) -> Optional[Any]:
            url = f"{self.base_url}{path}"
            headers: Dict[str, str] = {
                "Accept": "application/json",
                "User-Agent": "null",
            }
            params: Dict[str, Any] = {}
            if self.api_key and self.api_key_query_param:
                params[self.api_key_query_param] = self.api_key
            elif self.api_key:
                headers[self.api_key_header] = self.api_key

            try:
                r = requests.get(url, headers=headers, params=params, timeout=self.timeout_seconds)
                self.last_status_code = r.status_code
                if r.status_code in (401, 403):
                    self.last_error = f"auth_failed: HTTP {r.status_code}"
                    return None
                if r.status_code == 429:
                    self.last_error = "rate_limited: HTTP 429"
                    return None
                r.raise_for_status()
                return r.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Maricopa Assessor parcel request failed for {path}: {e}")
                return None

        # Pull a small, high-signal set of endpoints.
        payload: Dict[str, Any] = {"apn": apn}
        payload["parcel"] = _get(f"/parcel/{apn}")  # full parcel data
        payload["propertyinfo"] = _get(f"/parcel/{apn}/propertyinfo")
        payload["address"] = _get(f"/parcel/{apn}/address")
        payload["valuations"] = _get(f"/parcel/{apn}/valuations")
        payload["residential_details"] = _get(f"/parcel/{apn}/residential-details")
        payload["owner_details"] = _get(f"/parcel/{apn}/owner-details")
        return payload

    def _parse_combined(
        self,
        search_record: Dict[str, Any],
        parcel_payload: Dict[str, Any],
        apn: Optional[str],
        address: str,
        city: str,
        state: str,
        zip_code: str,
    ) -> Optional[Property]:
        """Best-effort parsing across search + parcel payloads (schema varies)."""
        combined: Dict[str, Any] = {
            "search": search_record,
            "parcel_payload": parcel_payload,
        }

        apn_val = apn or _safe_str(
            _deep_find_first(combined, ["apn", "APN", "parcelNumber", "parcel_number"])
        )
        year_built = _safe_int(
            _deep_find_first(combined, ["yearBuilt", "YearBuilt", "builtYear", "BuiltYear", "yr_blt", "YR_BLT"])
        )
        lot_size_sqft = _safe_float(
            _deep_find_first(
                combined,
                [
                    "lotSizeSqFt",
                    "LotSizeSqFt",
                    "lot_size_sqft",
                    "LotSqFt",
                    "lotSqFt",
                    "lot_sq_ft",
                    "LotAreaSqFt",
                ],
            )
        )
        square_feet = _safe_int(
            _deep_find_first(
                combined,
                [
                    "squareFeet",
                    "SquareFeet",
                    "sqft",
                    "SqFt",
                    "buildingSqFt",
                    "livingAreaSqFt",
                    "LivingArea",
                ],
            )
        )

        # Valuations often come as arrays; we store raw in mls_data and pull best-effort value fields.
        assessed_value = _safe_float(
            _deep_find_first(
                combined,
                ["assessedValue", "AssessedValue", "totalAssessedValue", "TotalAssessedValue"],
            )
        )
        market_value = _safe_float(
            _deep_find_first(combined, ["marketValue", "MarketValue", "fullCashValue", "FullCashValue"])
        )

        situs_address = _safe_str(
            _deep_find_first(
                combined,
                ["situsAddress", "SitusAddress", "propertyAddress", "PropertyAddress", "Address"],
            )
        )

        # Always return a Property instance so bot can merge missing fields.
        prop_id = apn_val or f"maricopa:{(situs_address or address).strip()}"
        status = PropertyStatus.ACTIVE

        mls_data: Dict[str, Any] = {
            "source": "maricopa_assessor",
            "apn": apn_val,
            "assessed_value": assessed_value,
            "market_value": market_value,
            "raw": combined,
        }

        try:
            return Property(
                mls_number=prop_id,
                address=situs_address or address,
                city=city,
                state=state,
                zip_code=zip_code,
                property_type=PropertyType.RESIDENTIAL,
                status=status,
                square_feet=square_feet,
                lot_size_sqft=lot_size_sqft,
                year_built=year_built,
                mls_data=mls_data,
            )
        except Exception as e:
            logger.warning(f"Maricopa Assessor parse failed: {e}")
            return None


