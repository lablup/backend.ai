"""Request DTOs for AppProxy coordinator endpoint APIs."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

from .types import CreateEndpointItem, DeleteEndpointItem


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
