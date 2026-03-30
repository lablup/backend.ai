"""DomainV2 GraphQL nested types for structured field groups."""

from __future__ import annotations

from datetime import datetime

from ai.backend.common.dto.manager.v2.domain.response import (
    DomainBasicInfo as DomainBasicInfoDTO,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DomainLifecycleInfo as DomainLifecycleInfoDTO,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DomainRegistryInfo as DomainRegistryInfoDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)

# ============================================================================
# Basic Information
# ============================================================================


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Basic domain information. Contains identity and descriptive fields for the domain."
        ),
    ),
    model=DomainBasicInfoDTO,
    name="DomainBasicInfo",
)
class DomainBasicInfoGQL:
    """Basic domain information."""

    name: str = gql_field(description="Domain name (primary key).")
    description: str | None = gql_field(description="Optional description of the domain.")
    integration_id: str | None = gql_field(description="External system integration identifier.")


# ============================================================================
# Container Registry Configuration
# ============================================================================


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Domain container registry configuration. "
            "Contains allowed container registry URLs for this domain."
        ),
    ),
    model=DomainRegistryInfoDTO,
    name="DomainRegistryInfo",
)
class DomainRegistryInfoGQL:
    """Domain container registry configuration."""

    allowed_docker_registries: list[str] = gql_field(
        description="List of allowed container registry URLs. Empty list means no restrictions on registry access."
    )


# ============================================================================
# Lifecycle Information
# ============================================================================


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Domain lifecycle information. Contains activation status and timestamp tracking."
        ),
    ),
    model=DomainLifecycleInfoDTO,
    name="DomainLifecycleInfo",
)
class DomainLifecycleInfoGQL:
    """Domain lifecycle information."""

    is_active: bool = gql_field(
        description="Whether the domain is active. Inactive domains cannot create new projects or perform operations."
    )
    created_at: datetime = gql_field(description="Timestamp when the domain was created.")
    modified_at: datetime = gql_field(description="Timestamp when the domain was last modified.")
