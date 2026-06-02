from pydantic import ConfigDict

from ai.backend.common.types import BackendAISchema


class BaseAgentRequestModel(BackendAISchema):
    """Base class for pydantic request payloads on agent RPC v3 methods.

    Mirrors the role of ``ai.backend.common.api_handlers.BaseRequestModel``
    but scoped to agent-facing RPC wire types. Keeping a separate base lets
    the agent RPC surface version independently from the HTTP API request
    models while sharing a consistent pydantic configuration.

    Subclasses are consumed by ``AgentRPCRegistry`` (see
    ``ai.backend.agent.rpc.routing``): the registry inspects the bound
    handler's signature, treats every parameter annotation as a
    ``BaseAgentRequestModel`` subclass, and validates the incoming wire
    payload (``req`` envelope field) into it via ``model_validate``
    before invoking the handler.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_by_name=True,
    )


class HealthReq(BaseAgentRequestModel):
    """Empty request payload for the ``health_v2`` RPC method."""


class GatherHwinfoReq(BaseAgentRequestModel):
    """Empty request payload for the ``gather_hwinfo_v2`` RPC method."""
