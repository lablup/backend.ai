"""Request DTOs of the entity invitation v2 API."""

from __future__ import annotations

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.entity_invitation.types import (
    EntityInvitationOrderField,
    EntityInvitationSideDTO,
    EntityInvitationStatusDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO

__all__ = (
    "CreateEntityInvitationInput",
    "EntityInvitationFilter",
    "EntityInvitationOrderBy",
    "EntityInvitationScopeDTO",
    "EntityInvitationScopeItemDTO",
    "ScopedSearchEntityInvitationsInput",
)


class CreateEntityInvitationInput(BaseRequestModel):
    """One offer of one entity to one address.

    The cap is given as the permissions it holds rather than a bitmask; an empty list
    means no ceiling, so the invitee's own permissions stand unclipped.
    """

    target_entity_type: EntityType = Field(description="Type of the entity being offered")
    target_entity_id: EntityID = Field(description="Id of the entity being offered")
    invitee_email: str = Field(description="Address the offer goes to")
    permissions: list[PermissionBitDTO] = Field(
        default_factory=list,
        description="Permissions the offer caps at; empty for no ceiling",
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


class EntityInvitationScopeItemDTO(BaseRequestModel):
    """One side invitations are read from.

    ``RECEIVED`` and ``SENT`` are answered for by the requester themselves and name
    nothing else; ``TARGET`` names the entity whose invitations are being read.
    """

    side: EntityInvitationSideDTO = Field(description="Which side the read comes in through.")
    target_entity_type: EntityType | None = Field(
        default=None, description="Type of the entity being offered; TARGET only."
    )
    target_entity_id: EntityID | None = Field(
        default=None, description="Id of the entity being offered; TARGET only."
    )

    @model_validator(mode="after")
    def _check_target(self) -> EntityInvitationScopeItemDTO:
        names = (self.target_entity_type, self.target_entity_id)
        if self.side is EntityInvitationSideDTO.TARGET:
            if None in names:
                raise ValueError("A TARGET item names the entity being offered.")
        elif any(name is not None for name in names):
            raise ValueError(f"A {self.side.value.upper()} item names no entity.")
        return self


class EntityInvitationScopeDTO(BaseRequestModel):
    """The sides the read covers, combined with OR."""

    items: list[EntityInvitationScopeItemDTO] = Field(
        min_length=1, description="Sides to read from (OR across all items)."
    )


class ScopedSearchEntityInvitationsInput(BaseRequestModel):
    scope: EntityInvitationScopeDTO = Field(description="Sides to read from.")
    filter: EntityInvitationFilter | None = None
    order: list[EntityInvitationOrderBy] | None = None
    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    limit: int | None = None
    offset: int | None = None
