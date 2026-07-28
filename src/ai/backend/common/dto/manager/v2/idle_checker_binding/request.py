from __future__ import annotations

from typing import Self

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import (
    DateTimeFilter,
    StringFilter,
    UUIDFilter,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.idle_checker_binding.types import (
    IdleCheckerBindingOrderField,
    IdleCheckerScopeTypeDTO,
    ScopeTypeFilter,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerBindingID, IdleCheckerID


class IdleCheckerScopeRefDTO(BaseRequestModel):
    """A typed (scope_type, scope_id) pair referencing one scope."""

    scope_type: IdleCheckerScopeTypeDTO = Field(description="Kind of the scope.")
    scope_id: str = Field(
        min_length=1,
        description="Scope identifier, interpreted according to the scope type.",
    )


class IdleCheckerBindingScopeDTO(BaseRequestModel):
    """Scope for the scoped idle checker binding query.

    All items are OR'd. Raises an error if the item list is empty.
    """

    items: list[IdleCheckerScopeRefDTO] = Field(
        min_length=1, description="Scope-tagged items (OR across all items)."
    )


class CreateIdleCheckerBindingInput(BaseRequestModel):
    scope: IdleCheckerScopeRefDTO = Field(description="Scope the checker is bound to.")
    idle_checker_id: IdleCheckerID = Field(description="Idle checker to bind.")
    enabled: bool = Field(
        default=True,
        description="Whether the binding participates in idle checking.",
    )


class UpdateIdleCheckerBindingInput(BaseRequestModel):
    id: IdleCheckerBindingID = Field(description="Idle checker binding ID to update.")
    enabled: bool = Field(description="New enabled state.")


class PurgeIdleCheckerBindingInput(BaseRequestModel):
    id: IdleCheckerBindingID = Field(description="Idle checker binding ID to purge.")


class IdleCheckerBindingFilter(BaseRequestModel):
    scope_type: ScopeTypeFilter | None = Field(default=None)
    scope_id: StringFilter | None = Field(default=None)
    idle_checker_id: UUIDFilter | None = Field(default=None)
    enabled: bool | None = Field(default=None)
    created_at: DateTimeFilter | None = Field(default=None)
    updated_at: DateTimeFilter | None = Field(default=None)
    AND: list[Self] | None = Field(default=None)
    OR: list[Self] | None = Field(default=None)
    NOT: list[Self] | None = Field(default=None)


IdleCheckerBindingFilter.model_rebuild()


class IdleCheckerBindingOrder(BaseRequestModel):
    field: IdleCheckerBindingOrderField
    direction: OrderDirection = Field(default=OrderDirection.ASC)


class SearchIdleCheckerBindingsInput(BaseRequestModel):
    filter: IdleCheckerBindingFilter | None = Field(default=None)
    order: list[IdleCheckerBindingOrder] | None = Field(default=None)
    first: int | None = Field(default=None, ge=1)
    after: str | None = Field(default=None)
    last: int | None = Field(default=None, ge=1)
    before: str | None = Field(default=None)
    limit: int | None = Field(default=None, ge=1)
    offset: int | None = Field(default=None, ge=0)


class ScopedSearchIdleCheckerBindingsInput(BaseRequestModel):
    scope: IdleCheckerBindingScopeDTO = Field(description="Scope (OR across all items).")
    filter: IdleCheckerBindingFilter | None = Field(default=None)
    order: list[IdleCheckerBindingOrder] | None = Field(default=None)
    first: int | None = Field(default=None, ge=1)
    after: str | None = Field(default=None)
    last: int | None = Field(default=None, ge=1)
    before: str | None = Field(default=None)
    limit: int | None = Field(default=None, ge=1)
    offset: int | None = Field(default=None, ge=0)
