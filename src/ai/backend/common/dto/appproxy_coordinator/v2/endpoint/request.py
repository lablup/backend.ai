"""Request DTOs for AppProxy coordinator endpoint APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

from .types import (
    CreateEndpointItem,
    DeleteEndpointItem,
    RegisterRoutesItem,
    UnregisterRoutesItem,
    UpdateRoutesItem,
)


class MintEndpointTokenRequest(BaseRequestModel):
    """Ask the coordinator to mint a per-endpoint JWT.

    The coordinator signs the token with the worker-shared ``jwt_secret``
    and embeds the circuit binding so that the worker's
    ``Authorization: Bearer <jwt>`` check accepts it for this endpoint
    only and rejects it after ``exp``.
    """

    user_uuid: UUID = Field(
        ...,
        description="User who will present the minted token.",
    )
    exp: datetime = Field(
        ...,
        description="Token expiration timestamp.",
    )


class BulkCreateEndpointRequest(BaseRequestModel):
    """Bulk create (or sync) multiple endpoints in one coordinator call.

    Entries are processed in order inside a single coordinator
    transaction, and freshly created circuits are propagated to
    workers in one batch after commit. The response preserves the
    input order.
    """

    endpoints: list[CreateEndpointItem] = Field(
        ...,
        description=(
            "Endpoints to create or sync. Entries are processed in order "
            "and the response returns a matching per-entry result."
        ),
    )


class BulkDeleteEndpointRequest(BaseRequestModel):
    """Bulk remove multiple endpoints in one coordinator call.

    Each entry runs in its own transaction so a single bad id does not
    fail the whole call; the response reports success / failure per
    input in input order. An already-gone endpoint counts as success.
    """

    endpoints: list[DeleteEndpointItem] = Field(
        ...,
        description=(
            "Endpoints to remove. Entries are processed in order and "
            "the response returns a matching per-entry result."
        ),
    )


class BulkUpdateRoutesRequest(BaseRequestModel):
    """Bulk replace the routing table of multiple endpoints in one coordinator call.

    The coordinator processes all entries inside a single connection,
    replaces each circuit's ``route_info`` with the supplied list, and
    propagates the new route set to workers in one batch after commit.
    Per-entry failures (e.g. circuit not registered yet, race against
    delete) are reported in the response without aborting the call.
    """

    endpoints: list[UpdateRoutesItem] = Field(
        ...,
        description=(
            "Endpoints whose routing tables should be replaced. Entries "
            "are processed in order and the response returns a matching "
            "per-entry result."
        ),
    )


class BulkRegisterRoutesRequest(BaseRequestModel):
    """Bulk add new routes to multiple endpoints in one coordinator call.

    Delta semantics: routes are appended to each circuit's existing
    ``route_info`` set. Already-present route ids count as success
    (idempotent re-register). Per-entry failures are reported in the
    response without aborting the call.
    """

    endpoints: list[RegisterRoutesItem] = Field(
        ...,
        description=(
            "Endpoints whose routing tables should receive new routes. "
            "Entries are processed in order and the response returns a "
            "matching per-entry result."
        ),
    )


class BulkUnregisterRoutesRequest(BaseRequestModel):
    """Bulk remove routes from multiple endpoints in one coordinator call.

    Delta semantics: routes whose ``route_id`` is listed are dropped
    from each circuit's existing ``route_info`` set. Already-absent
    route ids count as success (idempotent re-unregister). Per-entry
    failures are reported in the response without aborting the call.
    """

    endpoints: list[UnregisterRoutesItem] = Field(
        ...,
        description=(
            "Endpoints whose routing tables should drop the listed "
            "route ids. Entries are processed in order and the response "
            "returns a matching per-entry result."
        ),
    )
