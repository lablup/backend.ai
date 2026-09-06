"""Common types for Entity DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = ("EntityTarget",)


class EntityTarget(BaseRequestModel):
    """One entity, named by its type and its id.

    The type is a plain string rather than a closed enum: an entity type is declared
    where its operations are wired, so `entityTypes` is what lists the valid ones.
    """

    entity_type: str = Field(
        min_length=1, description="Type of the entity, as `entityTypes` lists them"
    )
    entity_id: UUID = Field(description="ID of the entity")
