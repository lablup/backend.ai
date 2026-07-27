from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class IdleCheckerTypeDTO(StrEnum):
    SESSION_LIFETIME = "session_lifetime"


class IdleCheckerInputTypeDTO(StrEnum):
    SESSION_LIFETIME = "session_lifetime"


class CheckerTypeFilter(BaseRequestModel):
    equals: IdleCheckerTypeDTO | None = Field(default=None)
    in_: list[IdleCheckerTypeDTO] | None = Field(default=None, alias="in")


class IdleCheckerOrderField(StrEnum):
    NAME = "name"
    CHECKER_TYPE = "checker_type"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
