"""
Response DTOs for Domain v2 API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.pagination import PaginationInfo

__all__ = (
    "DeleteDomainPayload",
    "DomainBasicInfo",
    "DomainLifecycleInfo",
    "DomainNode",
    "DomainPayload",
    "DomainRegistryInfo",
    "PurgeDomainPayload",
    "SearchDomainsPayload",
)


class DomainBasicInfo(BaseModel):
    """Basic domain information."""

    name: str = Field(
        description="Domain name (primary key).",
    )
    description: str | None = Field(
        default=None,
        description="Optional description of the domain.",
    )
    integration_id: str | None = Field(
        default=None,
        description="External system integration identifier.",
    )


class DomainRegistryInfo(BaseModel):
    """Domain container registry configuration."""

    allowed_docker_registries: list[str] = Field(
        description=(
            "List of allowed container registry URLs. "
            "Empty list means no restrictions on registry access."
        ),
    )


class DomainLifecycleInfo(BaseModel):
    """Domain lifecycle information."""

    is_active: bool = Field(
        description=(
            "Whether the domain is active. "
            "Inactive domains cannot create new projects or perform operations."
        ),
    )
    created_at: datetime = Field(
        description="Timestamp when the domain was created.",
    )
    modified_at: datetime = Field(
        description="Timestamp when the domain was last modified.",
    )


class DomainNode(BaseResponseModel):
    """Domain entity with structured field groups."""

    id: str = Field(
        description="Domain name (primary key).",
    )
    basic_info: DomainBasicInfo = Field(
        description="Basic domain information including name and description.",
    )
    registry: DomainRegistryInfo = Field(
        description="Container registry configuration.",
    )
    lifecycle: DomainLifecycleInfo = Field(
        description="Lifecycle information including activation status and timestamps.",
    )


class DomainPayload(BaseResponseModel):
    """Payload for single domain mutation responses."""

    domain: DomainNode = Field(
        description="The domain entity.",
    )


class SearchDomainsPayload(BaseResponseModel):
    """Payload for domain search responses."""

    items: list[DomainNode] = Field(
        description="List of domain entities matching the search criteria.",
    )
    pagination: PaginationInfo = Field(
        description="Pagination information for the result set.",
    )


class DeleteDomainPayload(BaseResponseModel):
    """Payload for domain deletion mutation."""

    deleted: bool = Field(
        description="Whether the deletion was successful.",
    )


class PurgeDomainPayload(BaseResponseModel):
    """Payload for domain permanent deletion mutation."""

    purged: bool = Field(
        description="Whether the purge was successful.",
    )
