from __future__ import annotations

from typing import Self

from pydantic import ConfigDict, Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.idle_checker.types import (
    CheckerTypeFilter,
    IdleCheckerInputTypeDTO,
    IdleCheckerOrderField,
)
from ai.backend.common.types import SessionTypes


class SessionLifetimeSpecInputDTO(BaseRequestModel):
    max_lifetime_seconds: int = Field(ge=0)


class IdleCheckerSpecInputDTO(BaseRequestModel):
    model_config = ConfigDict(extra="forbid")

    type: IdleCheckerInputTypeDTO
    session_lifetime: SessionLifetimeSpecInputDTO


class CreateIdleCheckerInput(BaseRequestModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None)
    checker_type: IdleCheckerInputTypeDTO
    target_session_types: list[SessionTypes] = Field(min_length=1)
    initial_grace_period_seconds: int = Field(default=0, ge=0)
    checker_spec: IdleCheckerSpecInputDTO

    @model_validator(mode="after")
    def _validate_spec_type(self) -> Self:
        if self.checker_spec.type != self.checker_type:
            raise ValueError("checker_type must match checker_spec.type")
        return self


class UpdateIdleCheckerInput(BaseRequestModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(
        default=None,
        description="Updated description. Omit or pass null to leave it unchanged.",
    )
    target_session_types: list[SessionTypes] | None = Field(default=None, min_length=1)
    initial_grace_period_seconds: int | None = Field(default=None, ge=0)
    checker_spec: IdleCheckerSpecInputDTO | None = Field(default=None)


class IdleCheckerFilter(BaseRequestModel):
    name: StringFilter | None = Field(default=None)
    checker_type: CheckerTypeFilter | None = Field(default=None)
    created_at: DateTimeFilter | None = Field(default=None)
    updated_at: DateTimeFilter | None = Field(default=None)
    AND: list[Self] | None = Field(default=None)
    OR: list[Self] | None = Field(default=None)
    NOT: list[Self] | None = Field(default=None)


IdleCheckerFilter.model_rebuild()


class IdleCheckerOrder(BaseRequestModel):
    field: IdleCheckerOrderField
    direction: OrderDirection = Field(default=OrderDirection.ASC)


class SearchIdleCheckersInput(BaseRequestModel):
    filter: IdleCheckerFilter | None = Field(default=None)
    order: list[IdleCheckerOrder] | None = Field(default=None)
    first: int | None = Field(default=None, ge=1)
    after: str | None = Field(default=None)
    last: int | None = Field(default=None, ge=1)
    before: str | None = Field(default=None)
    limit: int | None = Field(default=None, ge=1)
    offset: int | None = Field(default=None, ge=0)
