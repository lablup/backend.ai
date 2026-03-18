"""DomainV2 GraphQL nested types for structured field groups."""

from __future__ import annotations

import strawberry

from ai.backend.common.dto.manager.v2.domain.response import (
    DomainBasicInfo as DomainBasicInfoDTO,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DomainLifecycleInfo as DomainLifecycleInfoDTO,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DomainRegistryInfo as DomainRegistryInfoDTO,
)

# ============================================================================
# Basic Information
# ============================================================================


@strawberry.experimental.pydantic.type(
    model=DomainBasicInfoDTO,
    name="DomainBasicInfo",
    description=(
        "Added in 26.2.0. Basic domain information. "
        "Contains identity and descriptive fields for the domain."
    ),
    all_fields=True,
)
class DomainBasicInfoGQL:
    """Basic domain information."""


# ============================================================================
# Container Registry Configuration
# ============================================================================


@strawberry.experimental.pydantic.type(
    model=DomainRegistryInfoDTO,
    name="DomainRegistryInfo",
    description=(
        "Added in 26.2.0. Domain container registry configuration. "
        "Contains allowed container registry URLs for this domain."
    ),
    all_fields=True,
)
class DomainRegistryInfoGQL:
    """Domain container registry configuration."""


# ============================================================================
# Lifecycle Information
# ============================================================================


@strawberry.experimental.pydantic.type(
    model=DomainLifecycleInfoDTO,
    name="DomainLifecycleInfo",
    description=(
        "Added in 26.2.0. Domain lifecycle information. "
        "Contains activation status and timestamp tracking."
    ),
    all_fields=True,
)
class DomainLifecycleInfoGQL:
    """Domain lifecycle information."""
