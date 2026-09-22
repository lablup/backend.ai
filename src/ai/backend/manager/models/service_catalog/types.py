from __future__ import annotations

from typing import Any, TypedDict

__all__ = ("ServiceCatalogEndpointRowJson",)


class ServiceCatalogEndpointRowJson(TypedDict):
    """One service_catalog_endpoint row as row_to_json renders it: keys are column names."""

    id: str
    service_id: str
    role: str
    scope: str
    address: str
    port: int
    protocol: str
    metadata: dict[str, Any] | None
