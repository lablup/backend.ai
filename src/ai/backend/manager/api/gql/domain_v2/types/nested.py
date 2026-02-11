"""DomainV2 GraphQL nested types for structured field groups."""

from __future__ import annotations

from datetime import datetime

import strawberry

# ============================================================================
# Basic Information
# ============================================================================


@strawberry.type(
    name="DomainV2BasicInfo",
    description=(
        "Added in 26.2.0. Basic domain information. "
        "Contains identity and descriptive fields for the domain."
    ),
)
class DomainV2BasicInfoGQL:
    """Basic domain information."""

    name: str = strawberry.field(description="Domain name (primary key).")
    description: str | None = strawberry.field(description="Optional description of the domain.")
    integration_id: str | None = strawberry.field(
        description="External system integration identifier."
    )


# ============================================================================
# Container Registry Configuration
# ============================================================================


@strawberry.type(
    name="DomainV2RegistryInfo",
    description=(
        "Added in 26.2.0. Domain container registry configuration. "
        "Contains allowed container registry URLs for this domain."
    ),
)
class DomainV2RegistryInfoGQL:
    """Domain container registry configuration."""

    allowed_docker_registries: list[str] = strawberry.field(
        description=(
            "List of allowed container registry URLs. "
            "Empty list means no restrictions on registry access."
        )
    )


# ============================================================================
# Lifecycle Information
# ============================================================================


@strawberry.type(
    name="DomainV2LifecycleInfo",
    description=(
        "Added in 26.2.0. Domain lifecycle information. "
        "Contains activation status and timestamp tracking."
    ),
)
class DomainV2LifecycleInfoGQL:
    """Domain lifecycle information."""

    is_active: bool = strawberry.field(
        description=(
            "Whether the domain is active. "
            "Inactive domains cannot create new projects or perform operations."
        )
    )
    created_at: datetime = strawberry.field(description="Timestamp when the domain was created.")
    modified_at: datetime = strawberry.field(
        description="Timestamp when the domain was last modified."
    )
