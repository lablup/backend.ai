"""Response DTOs for Scope Operation DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "ListScopeOperationsPayload",
    "ScopeOperationNode",
)


class ScopeOperationNode(BaseResponseModel):
    """One wired operation that names a scope rather than an entity."""

    action_name: str = Field(description="The name the operation is recorded under")
    entity_type: str = Field(description="The entity type the operation acts on")
    operation: str = Field(description="The operation performed within the scopes")
    scope_types: list[str] = Field(
        description=(
            "The scope types the operation may be targeted at; `global` where the "
            "caller names the scope type, empty where the operation names no scope"
        )
    )


class ListScopeOperationsPayload(BaseResponseModel):
    """Payload for every wired scope operation."""

    items: list[ScopeOperationNode] = Field(description="Scope operation list")
