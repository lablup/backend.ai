"""Request DTOs of the entity invitation v2 API."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.permission.types import OperationType
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.entity_invitation.types import (
    EntityInvitationOrderField,
    EntityInvitationStatusDTO,
)

__all__ = (
    "CreateEntityInvitationInput",
    "EntityInvitationFilter",
    "EntityInvitationOrderBy",
    "SearchEntityInvitationsInput",
)


class CreateEntityInvitationInput(BaseRequestModel):
    """One offer of one entity to one address.

    The cap is given as the operations it allows rather than a bitmask; an empty list
    means no ceiling, so the invitee's own permissions stand unclipped.
    """

    target_entity_type: str = Field(description="Type of the entity being offered")
    target_entity_id: UUID = Field(description="Id of the entity being offered")
    invitee_email: str = Field(description="Address the offer goes to")
    operations: list[OperationType] = Field(
        default_factory=list,
        description="Operations the offer allows; empty for no ceiling",
    )


class EntityInvitationOrderBy(BaseRequestModel):
    field: EntityInvitationOrderField
    direction: OrderDirection = OrderDirection.DESC


class EntityInvitationStatusFilter(BaseRequestModel):
    equals: EntityInvitationStatusDTO | None = None
    in_: list[EntityInvitationStatusDTO] | None = Field(default=None, alias="in")


class EntityInvitationFilter(BaseRequestModel):
    status: EntityInvitationStatusFilter | None = None
    target_entity_id: UUIDFilter | None = None
    invitee_email: StringFilter | None = None


EntityInvitationFilter.model_rebuild()


class SearchEntityInvitationsInput(BaseRequestModel):
    filter: EntityInvitationFilter | None = None
    order: list[EntityInvitationOrderBy] | None = None
    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    limit: int | None = None
    offset: int | None = None
