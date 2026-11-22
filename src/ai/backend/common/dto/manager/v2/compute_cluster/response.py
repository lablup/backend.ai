"""Response DTOs for compute_cluster v2.

The kubeconfig is write-only: no response carries it.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.compute_cluster.types import ComputeClusterStatus
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION

__all__ = (
    "ComputeClusterNode",
    "CreateComputeClusterPayload",
    "PurgeComputeClusterPayload",
    "SearchComputeClustersPayload",
    "UpdateComputeClusterPayload",
)


class ComputeClusterNode(BaseResponseModel):
    """Node model representing a compute cluster entity."""

    id: UUID = Field(description=f"Added in {NEXT_RELEASE_VERSION}. Compute cluster UUID.")
    entity_id: UUID = Field(
        description=f"Added in {NEXT_RELEASE_VERSION}. UUID of the compute cluster."
    )
    name: str = Field(description=f"Added in {NEXT_RELEASE_VERSION}. Unique compute cluster name.")
    description: str | None = Field(
        description=f"Added in {NEXT_RELEASE_VERSION}. Optional description."
    )
    api_server: str = Field(
        description=f"Added in {NEXT_RELEASE_VERSION}. URL of the cluster's Kubernetes API server."
    )
    namespace_prefix: str = Field(
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. Prefix of the namespaces created in the cluster."
        )
    )
    gateway_addr: str | None = Field(
        description=f"Added in {NEXT_RELEASE_VERSION}. Address of the cluster's network gateway."
    )
    gateway_public_key: str | None = Field(
        description=f"Added in {NEXT_RELEASE_VERSION}. Public key of the cluster's gateway."
    )
    status: ComputeClusterStatus = Field(
        description=f"Added in {NEXT_RELEASE_VERSION}. Whether the API server is reachable."
    )
    status_changed_at: datetime | None = Field(
        description=f"Added in {NEXT_RELEASE_VERSION}. When the status last changed."
    )
    created_at: datetime = Field(
        description=f"Added in {NEXT_RELEASE_VERSION}. Creation timestamp (UTC)."
    )
    updated_at: datetime = Field(
        description=f"Added in {NEXT_RELEASE_VERSION}. Last modification timestamp (UTC)."
    )


class CreateComputeClusterPayload(BaseResponseModel):
    """Payload for compute cluster creation."""

    compute_cluster: ComputeClusterNode = Field(description="Created compute cluster.")


class UpdateComputeClusterPayload(BaseResponseModel):
    """Payload for compute cluster update."""

    compute_cluster: ComputeClusterNode = Field(description="Updated compute cluster.")


class PurgeComputeClusterPayload(BaseResponseModel):
    """Payload for compute cluster purge."""

    entity_id: UUID = Field(
        description=f"Added in {NEXT_RELEASE_VERSION}. UUID of the purged compute cluster."
    )


class SearchComputeClustersPayload(BaseResponseModel):
    """Payload for paginated compute cluster search results."""

    items: list[ComputeClusterNode] = Field(description="Compute cluster nodes.")
    total_count: int = Field(description="Total count matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
