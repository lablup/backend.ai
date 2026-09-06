"""Request DTOs of the entity invitation v2 API."""

from __future__ import annotations

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.entity_invitation.types import (
    EntityInvitationOrderField,
    EntityInvitationStatusDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO, UUIDScope

__all__ = (
    "CreateEntityInvitationInput",
    "EntityInvitationFilter",
    "EntityInvitationOrderBy",
    "EntityInvitationScope",
    "EntityInvitationTargetScope",
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


class EntityInvitationTargetScope(BaseRequestModel):
    """One entity whose invitations are being read.

    Its own pair rather than the shared ``EntityTypeScope``: what an invitation offers
    is an open entity type, which that closed element enum cannot name.
    """

    entity_type: EntityType = Field(description="Type of the entity being offered")
    entity_id: EntityID = Field(description="Id of the entity being offered")


class EntityInvitationScope(BaseRequestModel):
    """Scope for the scoped entity invitation query.

    Each list is OR'd internally and across lists. Raises an error if every field is
    empty. Naming a user reads the invitations they were sent or sent themselves, which
    the permission check on that user's scope is what allows.
    """

    invitee: list[UUIDScope] | None = Field(
        default=None, description="Users the invitations are addressed to"
    )
    inviter: list[UUIDScope] | None = Field(
        default=None, description="Users who sent the invitations"
    )
    target: list[EntityInvitationTargetScope] | None = Field(
        default=None, description="Entities the invitations offer"
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> EntityInvitationScope:
        if not self.invitee and not self.inviter and not self.target:
            raise ValueError(
                "EntityInvitationScope requires a non-empty value for "
                "'invitee', 'inviter' or 'target'"
            )
        return self


class ScopedSearchEntityInvitationsInput(BaseRequestModel):
    scope: EntityInvitationScope = Field(description="Scope (OR across all items)")
    filter: EntityInvitationFilter | None = None
    order: list[EntityInvitationOrderBy] | None = None
    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    limit: int | None = None
    offset: int | None = None
