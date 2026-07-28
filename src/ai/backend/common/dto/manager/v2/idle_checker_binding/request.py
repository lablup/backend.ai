from __future__ import annotations

from typing import Self

from pydantic import ConfigDict, Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import (
    DateTimeFilter,
    UUIDFilter,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.idle_checker_binding.types import (
    IdleCheckerBindingOrderField,
    ScopeTypeFilter,
)
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.idle_checker import IdleCheckerBindingID, IdleCheckerID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupID


class IdleCheckerBindingScopeDTO(BaseRequestModel):
    model_config = ConfigDict(extra="forbid")

    domain: DomainID | None = Field(default=None, description="Domain ID.")
    project: ProjectID | None = Field(default=None, description="Project ID.")
    resource_group: ResourceGroupID | None = Field(default=None, description="Resource group ID.")

    @model_validator(mode="after")
    def _validate_exactly_one_scope(self) -> Self:
        provided = 0
        for value in (self.domain, self.project, self.resource_group):
            if value is None:
                continue
            provided += 1
        if provided != 1:
            raise ValueError("Exactly one scope must be provided")
        return self


class IdleCheckerBindingOptionsInputDTO(BaseRequestModel):
    enabled: bool | None = Field(
        default=None,
        description=(
            "Whether the binding participates in idle checking. "
            "Omit to use the default (true) on create or to keep the current value on update."
        ),
    )


class CreateIdleCheckerBindingInput(BaseRequestModel):
    scope: IdleCheckerBindingScopeDTO = Field(description="Scope the checker is bound to.")
    idle_checker_id: IdleCheckerID = Field(description="Idle checker to bind.")
    options: IdleCheckerBindingOptionsInputDTO | None = Field(
        default=None, description="Binding options; omit to use the defaults."
    )


class UpdateIdleCheckerBindingInput(BaseRequestModel):
    id: IdleCheckerBindingID = Field(description="Idle checker binding ID to update.")
    options: IdleCheckerBindingOptionsInputDTO = Field(description="New binding options.")


class PurgeIdleCheckerBindingInput(BaseRequestModel):
    id: IdleCheckerBindingID = Field(description="Idle checker binding ID to purge.")


class IdleCheckerBindingFilter(BaseRequestModel):
    scope_type: ScopeTypeFilter | None = Field(default=None)
    scope_id: UUIDFilter | None = Field(default=None)
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
    scope: IdleCheckerBindingScopeDTO = Field(description="Scope to search bindings in.")
    filter: IdleCheckerBindingFilter | None = Field(default=None)
    order: list[IdleCheckerBindingOrder] | None = Field(default=None)
    first: int | None = Field(default=None, ge=1)
    after: str | None = Field(default=None)
    last: int | None = Field(default=None, ge=1)
    before: str | None = Field(default=None)
    limit: int | None = Field(default=None, ge=1)
    offset: int | None = Field(default=None, ge=0)
