"""Request DTOs of the entity invitation v2 API."""

from __future__ import annotations

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.entity_share.types import (
    EntityShareOrderField,
    EntityShareStatusDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO, UUIDScope

__all__ = (
    "CreateEntityShareInput",
    "EntityShareFilter",
    "EntityShareOrderBy",
    "EntityShareScope",
    "EntityShareTargetScope",
    "ScopedSearchEntitySharesInput",
)


class CreateEntityShareInput(BaseRequestModel):
    """One offer of one entity to one recipient.

    The recipient is named exactly one of three ways: a project, a person, or an
    address belonging to someone who may have no account. The cap is given as the
    permissions it holds rather than a bitmask; an empty list means no ceiling, so the
    recipient's own permissions stand unclipped.
    """

    target_entity_type: EntityType = Field(description="Type of the entity being offered")
    target_entity_id: EntityID = Field(description="Id of the entity being offered")
    recipient_project_id: EntityID | None = Field(
        default=None, description="Project the offer goes to"
    )
    recipient_user_id: EntityID | None = Field(
        default=None, description="Person the offer goes to; it lands in their own project"
    )
    recipient_email: str | None = Field(default=None, description="Address the offer goes to")
    permissions: list[PermissionBitDTO] = Field(
        default_factory=list,
        description="Permissions the offer caps at; empty for no ceiling",
    )

    @model_validator(mode="after")
    def _exactly_one_recipient(self) -> CreateEntityShareInput:
        named = [
            self.recipient_project_id is not None,
            self.recipient_user_id is not None,
            self.recipient_email is not None,
        ]
        if sum(named) != 1:
            raise ValueError("An offer names exactly one recipient")
        return self


class EntityShareOrderBy(BaseRequestModel):
    field: EntityShareOrderField
    direction: OrderDirection = OrderDirection.DESC


class EntityShareStatusFilter(BaseRequestModel):
    equals: EntityShareStatusDTO | None = None
    in_: list[EntityShareStatusDTO] | None = Field(default=None, alias="in")


class EntityShareFilter(BaseRequestModel):
    status: EntityShareStatusFilter | None = None
    target_entity_id: UUIDFilter | None = None
    recipient_email: StringFilter | None = None


EntityShareFilter.model_rebuild()


class EntityShareTargetScope(BaseRequestModel):
    """One entity whose invitations are being read.

    Its own pair rather than the shared ``EntityTypeScope``: what an invitation offers
    is an open entity type, which that closed element enum cannot name.
    """

    entity_type: EntityType = Field(description="Type of the entity being offered")
    entity_id: EntityID = Field(description="Id of the entity being offered")


class EntityShareScope(BaseRequestModel):
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
    target: list[EntityShareTargetScope] | None = Field(
        default=None, description="Entities the invitations offer"
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> EntityShareScope:
        if not self.invitee and not self.inviter and not self.target:
            raise ValueError(
                "EntityShareScope requires a non-empty value for 'invitee', 'inviter' or 'target'"
            )
        return self


class ScopedSearchEntitySharesInput(BaseRequestModel):
    scope: EntityShareScope = Field(description="Scope (OR across all items)")
    filter: EntityShareFilter | None = None
    order: list[EntityShareOrderBy] | None = None
    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    limit: int | None = None
    offset: int | None = None
