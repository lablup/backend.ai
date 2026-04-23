"""Response DTOs for AppProxy coordinator endpoint APIs."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import CreatedEndpointItem, DeletedEndpointItem


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
