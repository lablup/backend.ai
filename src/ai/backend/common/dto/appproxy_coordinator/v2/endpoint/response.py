"""Response DTOs for AppProxy coordinator endpoint APIs."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import (
    CreatedEndpointItem,
    DeletedEndpointItem,
    RegisteredRoutesItem,
    UnregisteredRoutesItem,
    UpdatedRoutesItem,
)


class BulkCreateEndpointResponse(BaseResponseModel):
    """Result of a bulk endpoint create / sync call.

    ``endpoints`` follows the same order as the request so callers can
    match each result back to its input entry by index.
    """

    endpoints: list[CreatedEndpointItem] = Field(
        ...,
        description="Per-endpoint results, in the same order as the request.",
    )


class BulkDeleteEndpointResponse(BaseResponseModel):
    """Result of a bulk endpoint remove call.

    ``endpoints`` follows the same order as the request so callers can
    match each result back to its input entry by index. Individual
    entries may fail independently — check ``success`` / ``error`` on
    each.
    """

    endpoints: list[DeletedEndpointItem] = Field(
        ...,
        description="Per-endpoint results, in the same order as the request.",
    )


class BulkUpdateRoutesResponse(BaseResponseModel):
    """Result of a bulk routes-sync call.

    ``endpoints`` follows the same order as the request so callers can
    match each result back to its input entry by index. Individual
    entries may fail independently — check ``success`` / ``error`` on
    each.
    """

    endpoints: list[UpdatedRoutesItem] = Field(
        ...,
        description="Per-endpoint results, in the same order as the request.",
    )


class BulkRegisterRoutesResponse(BaseResponseModel):
    """Result of a bulk routes-register call.

    ``endpoints`` follows the same order as the request so callers can
    match each result back to its input entry by index. Each entry
    splits the supplied routes into ``registered_route_ids`` (newly
    added) and ``already_registered_route_ids`` (idempotent no-op).
    """

    endpoints: list[RegisteredRoutesItem] = Field(
        ...,
        description="Per-endpoint results, in the same order as the request.",
    )


class BulkUnregisterRoutesResponse(BaseResponseModel):
    """Result of a bulk routes-unregister call.

    ``endpoints`` follows the same order as the request so callers can
    match each result back to its input entry by index. Each entry
    splits the requested route ids into ``unregistered_route_ids``
    (dropped) and ``already_absent_route_ids`` (idempotent no-op).
    """

    endpoints: list[UnregisteredRoutesItem] = Field(
        ...,
        description="Per-endpoint results, in the same order as the request.",
    )


class MintEndpointTokenResponse(BaseResponseModel):
    """JWT minted by the coordinator for a single endpoint."""

    token: str = Field(
        ...,
        description="HS256-signed JWT carrying the circuit binding and exp claim.",
    )
