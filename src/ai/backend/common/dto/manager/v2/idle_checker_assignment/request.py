from __future__ import annotations

from typing import Self

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import (
    DateTimeFilter,
    UUIDFilter,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import (
    IdleCheckerAssignmentOrderField,
    IdleCheckerScopeTypeDTO,
    ScopeTypeFilter,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerAssignmentID, IdleCheckerID


class IdleCheckerScopeRefDTO(BaseRequestModel):
    """A typed (scope_type, scope_id) pair referencing one scope."""

    scope_type: IdleCheckerScopeTypeDTO = Field(description="Kind of the scope.")
    scope_id: str = Field(
        min_length=1,
        description="Scope identifier, interpreted according to the scope type.",
    )


class IdleCheckerAssignmentScopeDTO(BaseRequestModel):
    """Scope for the scoped idle checker assignment query.

    All items are OR'd. Raises an error if the item list is empty.
    """

    items: list[IdleCheckerScopeRefDTO] = Field(
        min_length=1, description="Scope-tagged items (OR across all items)."
    )


class CreateIdleCheckerAssignmentInput(BaseRequestModel):
    scope: IdleCheckerScopeRefDTO = Field(description="Scope the checker is bound to.")
    idle_checker_id: IdleCheckerID = Field(description="Idle checker to bind.")
    enabled: bool = Field(
        default=True,
        description="Whether the assignment participates in idle checking.",
    )


class UpdateIdleCheckerAssignmentInput(BaseRequestModel):
    id: IdleCheckerAssignmentID = Field(description="Idle checker assignment ID to update.")
    enabled: bool = Field(description="New enabled state.")


class PurgeIdleCheckerAssignmentInput(BaseRequestModel):
    id: IdleCheckerAssignmentID = Field(description="Idle checker assignment ID to purge.")


class IdleCheckerAssignmentFilter(BaseRequestModel):
    scope_type: ScopeTypeFilter | None = Field(default=None)
    scope_id: UUIDFilter | None = Field(default=None)
    idle_checker_id: UUIDFilter | None = Field(default=None)
    enabled: bool | None = Field(default=None)
    created_at: DateTimeFilter | None = Field(default=None)
    updated_at: DateTimeFilter | None = Field(default=None)
    AND: list[Self] | None = Field(default=None)
    OR: list[Self] | None = Field(default=None)
    NOT: list[Self] | None = Field(default=None)


IdleCheckerAssignmentFilter.model_rebuild()


class IdleCheckerAssignmentOrder(BaseRequestModel):
    field: IdleCheckerAssignmentOrderField
    direction: OrderDirection = Field(default=OrderDirection.ASC)


class SearchIdleCheckerAssignmentsInput(BaseRequestModel):
    filter: IdleCheckerAssignmentFilter | None = Field(default=None)
    order: list[IdleCheckerAssignmentOrder] | None = Field(default=None)
    first: int | None = Field(default=None, ge=1)
    after: str | None = Field(default=None)
    last: int | None = Field(default=None, ge=1)
    before: str | None = Field(default=None)
    limit: int | None = Field(default=None, ge=1)
    offset: int | None = Field(default=None, ge=0)


class ScopedSearchIdleCheckerAssignmentsInput(BaseRequestModel):
    scope: IdleCheckerAssignmentScopeDTO = Field(description="Scope (OR across all items).")
    filter: IdleCheckerAssignmentFilter | None = Field(default=None)
    order: list[IdleCheckerAssignmentOrder] | None = Field(default=None)
    first: int | None = Field(default=None, ge=1)
    after: str | None = Field(default=None)
    last: int | None = Field(default=None, ge=1)
    before: str | None = Field(default=None)
    limit: int | None = Field(default=None, ge=1)
    offset: int | None = Field(default=None, ge=0)
