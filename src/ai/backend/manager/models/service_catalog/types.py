from __future__ import annotations

from typing import Any, TypedDict

__all__ = ("ServiceCatalogEndpointRowJson",)


class ServiceCatalogEndpointRowJson(TypedDict):
    """One element of ``ServiceCatalogRow.endpoint_rows``: row_to_json's keys and values."""

    id: str
    service_id: str
    role: str
    scope: str
    address: str
    port: int
    protocol: str
    metadata: dict[str, Any] | None
