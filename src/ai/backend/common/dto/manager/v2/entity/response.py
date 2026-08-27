"""Response DTOs for Entity DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "EntityTypeNode",
    "ListEntityTypesPayload",
)


class EntityTypeNode(BaseResponseModel):
    """One entity type the manager has operations wired for."""

    name: str = Field(description="The entity type, as a request names it")
    scope_types: list[str] = Field(
        description=(
            "The scope types an operation on this entity type may be targeted at; "
            "`global` where the caller names the scope type, empty where no operation "
            "on it names a scope"
        )
    )


class ListEntityTypesPayload(BaseResponseModel):
    """Payload for every entity type a request may name."""

    items: list[EntityTypeNode] = Field(description="Entity type list")
