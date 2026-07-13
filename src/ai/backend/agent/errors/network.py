"""
Cluster-network exceptions for the agent (BEP-1062).
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class LocalSubnetPoolExhausted(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when every node-local /24 block for session LOCAL bridges is taken."""

    error_type = "https://api.backend.ai/probs/agent/local-subnet-pool-exhausted"
    error_title = "No free node-local subnet is available for the session LOCAL bridge."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class LocalSubnetLayoutChanged(BackendAIError, web.HTTPInternalServerError):
    """The node-local pool was re-cut while sessions still hold blocks from the old one.

    A journalled index names a subnet only against the pool it was cut from, so reading it back
    under a different pool (or block size) would name a subnet the live bridge is not on. The
    operator has to drain the node before changing either.
    """

    error_type = "https://api.backend.ai/probs/agent/local-subnet-layout-changed"
    error_title = "The node-local subnet pool changed while sessions still hold blocks from it."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class OverlayAddressNotAssigned(BackendAIError, web.HTTPInternalServerError):
    """The manager did not assign an overlay IP for a multi-node vxlan endpoint.

    The overlay subnet is stretched across the cluster, so a node cannot pick an address locally
    without colliding with its peers. A missing assignment is a control-plane bug; fail loudly
    rather than attach a colliding address.
    """

    error_type = "https://api.backend.ai/probs/agent/overlay-address-not-assigned"
    error_title = "No manager-assigned overlay address for the cluster-network endpoint."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class SubnetAddressPoolExhausted(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when a host-local subnet has no free address left for a container endpoint."""

    error_type = "https://api.backend.ai/probs/agent/subnet-address-pool-exhausted"
    error_title = "No free address is available in the container subnet."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class PortForwardError(BackendAIError, web.HTTPInternalServerError):
    """Raised when installing or removing a container's host-port DNAT rule fails."""

    error_type = "https://api.backend.ai/probs/agent/port-forward-error"
    error_title = "Failed to publish the container's service port on a host port."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class NetworkStateStoreConflict(BackendAIError, web.HTTPInternalServerError):
    """A network state store on disk disagrees with its owner's in-memory state.

    Each store has exactly one writer per node, so a record the owner believes is free but which
    already exists on disk means a second writer is mutating this node's network — a condition the
    data plane cannot survive anyway (session setup deletes and recreates host devices by name).
    Fail loudly rather than allocate over it.
    """

    error_type = "https://api.backend.ai/probs/agent/network-state-store-conflict"
    error_title = "The on-disk network state store was modified by another writer."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )
