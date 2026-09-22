from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import ConfigDict

from ai.backend.common.types import BackendAISchema

__all__ = ("ServiceCatalogEndpointRowJson",)


class ServiceCatalogEndpointRowJson(BackendAISchema):
    """One service_catalog_endpoint row as row_to_json renders it: fields are column names."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    service_id: UUID
    role: str
    scope: str
    address: str
    port: int
    protocol: str
    metadata: dict[str, Any] | None
