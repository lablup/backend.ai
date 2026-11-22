"""Request DTOs for compute_cluster v2."""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, StringConstraints, field_validator, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.compute_cluster.kubeconfig import parse_kubeconfig
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
NAMESPACE_PREFIX_MAX_LENGTH = 26
"""The prefix plus a 36-character project id stays within a 63-character namespace name."""
_NamespacePrefix = Annotated[
    str,
    StringConstraints(
        min_length=1, max_length=NAMESPACE_PREFIX_MAX_LENGTH, pattern=r"^[a-z0-9]([-a-z0-9]*)?$"
    ),
]
_Description = Annotated[str, StringConstraints(max_length=512)]
_GatewayAddr = Annotated[str, StringConstraints(min_length=1, max_length=256)]
_Kubeconfig = Annotated[str, StringConstraints(min_length=1)]
_KUBECONFIG_DESCRIPTION = (
    "Kubeconfig the manager uses to reach the cluster. Stored encrypted and never returned."
    " Only inline credentials are accepted: `certificate-authority-data`,"
    " `client-certificate-data`, `client-key-data` and `token`; `exec`, `auth-provider` and"
    " file paths are rejected."
)
_API_SERVER_DESCRIPTION = (
    "URL of the cluster's Kubernetes API server. Read from the kubeconfig's current context;"
    " a different value is rejected."
)


def _validated_kubeconfig(value: str | None | Unset) -> str | None | Unset:
    if isinstance(value, str):
        parse_kubeconfig(value)
    return value


def _check_api_server(api_server: str | None | Unset, kubeconfig: str | None | Unset) -> None:
    if not isinstance(api_server, str):
        return
    if not isinstance(kubeconfig, str):
        raise ValueError("api_server is read from the kubeconfig; send the kubeconfig instead")
    server = parse_kubeconfig(kubeconfig).server
    if api_server.rstrip("/") != server.rstrip("/"):
        raise ValueError(
            f"api_server {api_server!r} differs from the kubeconfig's server {server!r}"
        )


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
    api_server: _ApiServer | None = Field(
        default=None,
        description=f"Added in {NEXT_RELEASE_VERSION}. {_API_SERVER_DESCRIPTION}",
    )
    kubeconfig: _Kubeconfig = Field(
        description=f"Added in {NEXT_RELEASE_VERSION}. {_KUBECONFIG_DESCRIPTION}",
    )
    namespace_prefix: _NamespacePrefix = Field(
        default="bai-",
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. Prefix of the namespaces created in the cluster:"
            " lowercase alphanumerics and '-', at most 26 characters."
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

    @field_validator("kubeconfig")
    @classmethod
    def _check_kubeconfig(cls, value: str) -> str:
        parse_kubeconfig(value)
        return value

    @model_validator(mode="after")
    def _check_api_server_matches(self) -> Self:
        _check_api_server(self.api_server, self.kubeconfig)
        return self


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
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. {_API_SERVER_DESCRIPTION}"
            " Only accepted together with `kubeconfig`."
        ),
    )
    kubeconfig: _Kubeconfig | None | Unset = Field(
        default=UNSET,
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. {_KUBECONFIG_DESCRIPTION}"
            " Replaces the stored kubeconfig. Omit to leave unchanged."
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

    @field_validator("kubeconfig")
    @classmethod
    def _check_kubeconfig(cls, value: str | None | Unset) -> str | None | Unset:
        return _validated_kubeconfig(value)

    @model_validator(mode="after")
    def _check_api_server_matches(self) -> Self:
        _check_api_server(self.api_server, self.kubeconfig)
        return self


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
