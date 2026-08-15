from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date, datetime
from xml.etree.ElementTree import ParseError, fromstring
from xml.sax.saxutils import escape

import httpx

from domain.verification.types import (
    VehicleVerificationResult,
    VerificationContext,
    VerifiedVehicleAttributes,
)
from ports.storage import ObjectStorage

PROVIDER_NAME = "api_setu"
_RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})
_ERROR_STATUS_VALUES = frozenset({"ERROR", "FAILED", "FAILURE", "N"})
_API_KEY_HEADER = "X-APISETU-APIKEY"
_CLIENT_ID_HEADER = "X-APISETU-CLIENTID"


class ApiSetuParseError(ValueError):
    """Raised when a provider payload cannot be read as VehicleDetails XML."""


@dataclass(frozen=True, slots=True)
class ApiSetuClientConfig:
    base_url: str
    api_key: str
    client_id: str
    timeout_seconds: float = 10.0
    max_attempts: int = 3
    backoff_seconds: float = 0.2


def parse_api_setu_xml(payload: str | bytes) -> dict[str, str]:
    """Extract API Setu XML tags. Adapter-local; not a domain type."""
    document = payload.encode("utf-8") if isinstance(payload, str) else payload
    try:
        root = fromstring(document)
    except ParseError as error:
        raise ApiSetuParseError("response is not valid XML") from error
    fields: dict[str, str] = {}
    for element in root.iter():
        text = (element.text or "").strip()
        if not text:
            continue
        fields[_local_name(element.tag)] = text
    if not fields:
        raise ApiSetuParseError("XML response contained no vehicle fields")
    return fields


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _provider_status(fields: dict[str, str]) -> str:
    return (fields.get("statusMessage") or fields.get("stautsMessage") or "").strip().upper()


def canonical_attributes_from_fields(fields: dict[str, str]) -> VerifiedVehicleAttributes:
    """Map API Setu XML tags to canonical attributes. Not used outside this adapter."""
    return VerifiedVehicleAttributes(
        registration_date=_parse_date(fields.get("rc_regn_dt")),
        manufacturing_month_year=_parse_month_year(fields.get("rc_manu_month_yr")),
        gvw_kg=_parse_int(fields.get("rc_gvw")),
        unladen_weight_kg=_parse_int(fields.get("rc_unld_wt")),
        engine_cc=_parse_int(fields.get("rc_cubic_cap")),
        cylinder_count=_parse_int(fields.get("rc_no_cyl")),
        fuel_type=_normalize_label(fields.get("rc_fuel_desc")),
        body_type=_body_type(fields.get("rc_body_type_desc")),
    )


def _normalize_label(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped.upper() if stripped else None


def _body_type(value: str | None) -> str | None:
    label = _normalize_label(value)
    if label is None:
        return None
    if "OPEN" in label:
        return "OPEN"
    if "CLOSED" in label or "CONTAINER" in label or "BOX" in label:
        return "CLOSED"
    if "TANKER" in label:
        return "TANKER"
    if "TIPPER" in label:
        return "TIPPER"
    return label


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_month_year(value: str | None) -> date | None:
    if not value:
        return None
    try:
        month_text, year_text = value.split("/", maxsplit=1)
        return date(int(year_text), int(month_text), 1)
    except ValueError:
        return None


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


class ApiSetuVehicleVerificationProvider:
    """HTTP adapter for API Setu/VAHAN RC lookup.

    XML request/response shapes stay in this module. Domain and application
    layers only see VehicleVerificationResult.
    """

    def __init__(
        self,
        *,
        config: ApiSetuClientConfig,
        storage: ObjectStorage,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not config.base_url:
            raise ValueError("API Setu base URL is required")
        if not config.api_key:
            raise ValueError("API Setu API key is required")
        self._config = config
        self._storage = storage
        self._client = client

    async def verify_registration(
        self,
        registration_number: str,
        context: VerificationContext,
    ) -> VehicleVerificationResult:
        try:
            response = await self._request_with_retry(registration_number, context)
        except httpx.TimeoutException:
            return self._result(context, success=False, error_code="API_SETU_TIMEOUT")
        except httpx.TransportError:
            return self._result(context, success=False, error_code="API_SETU_UNAVAILABLE")

        raw_object_key = await self._store_raw(response.content, context)
        if response.status_code in {401, 403}:
            return self._result(
                context,
                success=False,
                error_code="API_SETU_UNAUTHORIZED",
                raw_object_key=raw_object_key,
            )
        if response.status_code == 404:
            return self._result(
                context,
                success=False,
                error_code="API_SETU_NOT_FOUND",
                raw_object_key=raw_object_key,
            )
        if response.status_code == 429:
            return self._result(
                context,
                success=False,
                error_code="API_SETU_RATE_LIMITED",
                raw_object_key=raw_object_key,
            )
        if response.status_code >= 400:
            return self._result(
                context,
                success=False,
                error_code="API_SETU_UNAVAILABLE",
                raw_object_key=raw_object_key,
            )
        return self._result_from_xml(response.text, context, raw_object_key)

    async def _request_with_retry(
        self,
        registration_number: str,
        context: VerificationContext,
    ) -> httpx.Response:
        attempts = max(1, self._config.max_attempts)
        last_response: httpx.Response | None = None
        for attempt in range(1, attempts + 1):
            try:
                response = await self._send(registration_number, context)
            except (httpx.TimeoutException, httpx.TransportError):
                if attempt >= attempts:
                    raise
                await self._backoff(attempt)
                continue
            last_response = response
            if response.status_code in _RETRYABLE_STATUS_CODES and attempt < attempts:
                await self._backoff(attempt)
                continue
            return response
        assert last_response is not None
        return last_response

    async def _send(self, registration_number: str, context: VerificationContext) -> httpx.Response:
        headers = {
            "Accept": "application/xml",
            "Content-Type": "application/xml",
            _API_KEY_HEADER: self._config.api_key,
            _CLIENT_ID_HEADER: self._config.client_id,
            "X-Correlation-ID": context.correlation_id,
        }
        body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<VehicleDetailsRequest>"
            f"<rc_regn_no>{escape(registration_number)}</rc_regn_no>"
            "</VehicleDetailsRequest>"
        )
        client = self._client or httpx.AsyncClient()
        close_client = self._client is None
        try:
            return await client.post(
                self._config.base_url,
                content=body.encode("utf-8"),
                headers=headers,
                timeout=self._config.timeout_seconds,
            )
        finally:
            if close_client:
                await client.aclose()

    async def _backoff(self, attempt: int) -> None:
        delay = self._config.backoff_seconds * (2 ** (attempt - 1))
        await asyncio.sleep(delay)

    async def _store_raw(self, payload: bytes, context: VerificationContext) -> str:
        key = (
            f"tenants/{context.tenant_id}/vehicles/{context.vehicle_id}"
            f"/verification/{context.correlation_id}.xml"
        )
        return await self._storage.put_bytes(key, payload, "application/xml")

    def _result_from_xml(
        self,
        payload: str,
        context: VerificationContext,
        raw_object_key: str,
    ) -> VehicleVerificationResult:
        try:
            fields = parse_api_setu_xml(payload)
        except ApiSetuParseError:
            return self._result(
                context,
                success=False,
                error_code="API_SETU_INVALID_RESPONSE",
                raw_object_key=raw_object_key,
            )
        status = _provider_status(fields)
        if status in _ERROR_STATUS_VALUES:
            return self._result(
                context,
                success=False,
                error_code="API_SETU_PROVIDER_ERROR",
                raw_object_key=raw_object_key,
            )
        if not fields.get("rc_regn_no"):
            return self._result(
                context,
                success=False,
                error_code="API_SETU_INCOMPLETE_RESPONSE",
                raw_object_key=raw_object_key,
            )
        return self._result(
            context,
            success=True,
            raw_object_key=raw_object_key,
            attributes=canonical_attributes_from_fields(fields),
        )

    @staticmethod
    def _result(
        context: VerificationContext,
        *,
        success: bool,
        error_code: str | None = None,
        raw_object_key: str | None = None,
        attributes: VerifiedVehicleAttributes | None = None,
    ) -> VehicleVerificationResult:
        return VehicleVerificationResult(
            success=success,
            provider=PROVIDER_NAME,
            correlation_id=context.correlation_id,
            raw_object_key=raw_object_key,
            error_code=error_code,
            attributes=attributes,
        )
