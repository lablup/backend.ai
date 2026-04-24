"""Parameter extraction for agent RPC v3 handlers.

Parallel to ``ai.backend.common.api_handlers.extract_param_value`` in the
REST layer: the RPC dispatcher builds handler kwargs by inspecting each
parameter's annotation and mapping it to a slice of the parsed request
body. Only ``BaseAgentRequestModel`` subclasses are supported — RPC has a
single structured input (the ``req`` envelope field), so a wrapper type
like ``BodyParam`` buys nothing and is deliberately omitted.
"""

from __future__ import annotations

from typing import Any

from ai.backend.common.dto.agent.request import BaseAgentRequestModel


async def extract_rpc_param_value(
    raw_req: Any,
    annotation: Any,
) -> Any:
    """Extract a handler parameter's value from the ``req`` envelope field.

    ``raw_req`` is the raw dict the manager client sent as the ``req``
    entry of the RPC body envelope (see ``_parse_request_body`` in
    ``registry.py``). The annotation alone dictates the target type;
    currently only ``BaseAgentRequestModel`` subclasses are accepted,
    parsed via ``model_validate``.
    """
    if isinstance(annotation, type) and issubclass(annotation, BaseAgentRequestModel):
        return annotation.model_validate(raw_req)

    raise TypeError(
        f"Unsupported RPC handler parameter annotation: {annotation!r}. "
        f"Expected a BaseAgentRequestModel subclass."
    )
