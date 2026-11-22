"""Request DTOs for compute_cluster v2."""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, StringConstraints

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.compute_cluster.types import (
    ComputeClusterOrderField,
    ComputeClusterStatus,
    ComputeClusterStatusFilter,
    OrderDirection,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.common.tristate.unset import UNSET, Unset

__all__ = (
    "ComputeClusterFilter",
    "ComputeClusterOrder",
    "CreateComputeClusterInput",
    "SearchComputeClustersInput",
    "UpdateComputeClusterInput",
)

_ApiServer = Annotated[str, StringConstraints(min_length=1, max_length=2048)]
_NamespacePrefix = Annotated[str, StringConstraints(min_length=1, max_length=32)]
_Description = Annotated[str, StringConstraints(max_length=512)]
_GatewayAddr = Annotated[str, StringConstraints(min_length=1, max_length=256)]
_Kubeconfig = Annotated[str, StringConstraints(min_length=1)]


class CreateComputeClusterInput(BaseRequestModel):
    """Input for registering a compute cluster."""

    name: str = Field(
        min_length=1,
        max_length=64,
        description=f"Added in {NEXT_RELEASE_VERSION}. Unique compute cluster name.",
    )
    description: _Description | None = Field(
        default=None,
        description=f"Added in {NEXT_RELEASE_VERSION}. Optional description.",
    )
    api_server: _ApiServer = Field(
        description=f"Added in {NEXT_RELEASE_VERSION}. URL of the cluster's Kubernetes API server.",
    )
    kubeconfig: _Kubeconfig = Field(
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. Kubeconfig the manager uses to reach the cluster. "
            "Stored encrypted and never returned."
        ),
    )
    namespace_prefix: _NamespacePrefix = Field(
        default="bai-",
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. Prefix of the namespaces created in the cluster."
        ),
    )
    gateway_addr: _GatewayAddr | None = Field(
        default=None,
        description=f"Added in {NEXT_RELEASE_VERSION}. Address of the cluster's network gateway.",
    )
    gateway_public_key: str | None = Field(
        default=None,
        description=f"Added in {NEXT_RELEASE_VERSION}. Public key of the cluster's gateway.",
    )


class UpdateComputeClusterInput(BaseRequestModel):
    """Input for updating a compute cluster.

    Every field defaults to UNSET (no change). The nullable fields accept ``null`` to clear.
    """

    description: _Description | None | Unset = Field(
        default=UNSET,
        description=f"Added in {NEXT_RELEASE_VERSION}. Omit to leave unchanged; null clears.",
    )
    api_server: _ApiServer | None | Unset = Field(
        default=UNSET,
        description=f"Added in {NEXT_RELEASE_VERSION}. Omit to leave unchanged.",
    )
    kubeconfig: _Kubeconfig | None | Unset = Field(
        default=UNSET,
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. Replaces the stored kubeconfig. "
            "Omit to leave unchanged."
        ),
    )
    namespace_prefix: _NamespacePrefix | None | Unset = Field(
        default=UNSET,
        description=f"Added in {NEXT_RELEASE_VERSION}. Omit to leave unchanged.",
    )
    gateway_addr: _GatewayAddr | None | Unset = Field(
        default=UNSET,
        description=f"Added in {NEXT_RELEASE_VERSION}. Omit to leave unchanged; null clears.",
    )
    gateway_public_key: str | None | Unset = Field(
        default=UNSET,
        description=f"Added in {NEXT_RELEASE_VERSION}. Omit to leave unchanged; null clears.",
    )
    status: ComputeClusterStatus | None | Unset = Field(
        default=UNSET,
        description=f"Added in {NEXT_RELEASE_VERSION}. Omit to leave unchanged.",
    )


class ComputeClusterFilter(BaseRequestModel):
    """Filter criteria for compute cluster search."""

    entity_id: UUIDFilter | None = Field(
        default=None,
        description=f"Added in {NEXT_RELEASE_VERSION}. Filter by compute cluster ID.",
    )
    name: StringFilter | None = Field(
        default=None, description=f"Added in {NEXT_RELEASE_VERSION}. Filter by name."
    )
    status: ComputeClusterStatusFilter | None = Field(
        default=None, description=f"Added in {NEXT_RELEASE_VERSION}. Filter by status."
    )
    created_at: DateTimeFilter | None = Field(
        default=None,
        description=f"Added in {NEXT_RELEASE_VERSION}. Filter by creation datetime.",
    )
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


ComputeClusterFilter.model_rebuild()


class ComputeClusterOrder(BaseRequestModel):
    """Single ordering criterion for compute cluster search."""

    field: ComputeClusterOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Sort direction.")


class SearchComputeClustersInput(BaseRequestModel):
    """Input for paginated compute cluster search."""

    filter: ComputeClusterFilter | None = Field(default=None, description="Filter criteria.")
    order: list[ComputeClusterOrder] | None = Field(default=None, description="Ordering criteria.")
    first: int | None = Field(
        default=None, ge=1, description="Cursor-based: number of items after cursor"
    )
    after: str | None = Field(default=None, description="Cursor-based: start cursor (exclusive)")
    last: int | None = Field(
        default=None, ge=1, description="Cursor-based: number of items before cursor"
    )
    before: str | None = Field(default=None, description="Cursor-based: end cursor (exclusive)")
    limit: int | None = Field(
        default=None, ge=1, description="Offset-based: maximum number of results."
    )
    offset: int | None = Field(
        default=None, ge=0, description="Offset-based: number of results to skip."
    )
