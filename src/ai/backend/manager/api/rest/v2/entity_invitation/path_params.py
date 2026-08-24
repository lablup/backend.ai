"""Path parameters naming the entity an invitation offers."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = ("EntityTargetPathParam",)


class EntityTargetPathParam(BaseRequestModel):
    target_entity_type: str = Field(description="Type of the entity being offered")
    target_entity_id: UUID = Field(description="Id of the entity being offered")
