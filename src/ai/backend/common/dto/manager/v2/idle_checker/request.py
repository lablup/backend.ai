from __future__ import annotations

from decimal import Decimal
from typing import Self

from pydantic import ConfigDict, Field, model_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.idle_checker.types import (
    CheckerTypeFilter,
    IdleCheckerInputTypeDTO,
    IdleCheckerOrderField,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.identifier.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.types import SessionTypes


class SessionLifetimeSpecInputDTO(BaseRequestModel):
    max_lifetime_seconds: int = Field(ge=1)


class NetworkTimeoutSpecInputDTO(BaseRequestModel):
    max_network_inactivity_seconds: int = Field(ge=1)


class UtilizationThresholdInputDTO(BaseRequestModel):
    preset_id: PrometheusQueryPresetID
    threshold: Decimal


class UtilizationSpecInputDTO(BaseRequestModel):
    max_underutilized_duration_seconds: int = Field(ge=1)
    threshold: UtilizationThresholdInputDTO


class IdleCheckerSpecInputDTO(BaseRequestModel):
    model_config = ConfigDict(extra="forbid")

    session_lifetime: SessionLifetimeSpecInputDTO | None = Field(default=None)
    network: NetworkTimeoutSpecInputDTO | None = Field(default=None)
    utilization: UtilizationSpecInputDTO | None = Field(default=None)

    @model_validator(mode="after")
    def _validate_exactly_one_spec(self) -> Self:
        spec_count = sum(
            spec is not None for spec in (self.session_lifetime, self.network, self.utilization)
        )
        if spec_count != 1:
            raise ValueError("Exactly one idle checker specification must be provided")
        return self


class CreateIdleCheckerInput(BaseRequestModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, description="Idle checker description.")
    checker_type: IdleCheckerInputTypeDTO
    target_session_types: list[SessionTypes] = Field(min_length=1)
    initial_grace_period_seconds: int = Field(default=0, ge=0)
    checker_spec: IdleCheckerSpecInputDTO

    @model_validator(mode="after")
    def _validate_checker_type_matches_spec(self) -> Self:
        matches = {
            IdleCheckerInputTypeDTO.SESSION_LIFETIME: self.checker_spec.session_lifetime,
            IdleCheckerInputTypeDTO.NETWORK_TIMEOUT: self.checker_spec.network,
            IdleCheckerInputTypeDTO.UTILIZATION: self.checker_spec.utilization,
        }
        if matches[self.checker_type] is None:
            raise ValueError("checker_type must match the provided idle checker specification")
        return self


class UpdateIdleCheckerInput(BaseRequestModel):
    id: IdleCheckerID = Field(description="Idle checker ID to update.")
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated description. Omit to leave unchanged or pass null to clear.",
    )
    target_session_types: list[SessionTypes] | None = Field(default=None, min_length=1)
    initial_grace_period_seconds: int | None = Field(default=None, ge=0)
    checker_spec: IdleCheckerSpecInputDTO | None = Field(default=None)


class PurgeIdleCheckerInput(BaseRequestModel):
    id: IdleCheckerID = Field(description="Idle checker ID to purge.")


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
