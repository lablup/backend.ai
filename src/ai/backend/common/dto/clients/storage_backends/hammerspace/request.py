from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from ai.backend.common.types import BackendAISchema


class HammerspaceLoginRequest(BackendAISchema):
    username: str
    password: str


class HammerspaceCreateShareRequest(BackendAISchema):
    name: str
    path: str
    shareSizeLimit: int | None = None


class HammerspaceCreateShareQuery(BackendAISchema):
    model_config = ConfigDict(validate_by_name=True)

    create_path: Literal["true", "false"] = Field(alias="create-path")
    validate_only: Literal["true", "false"] = Field(alias="validate-only")


class HammerspaceGetShareQuery(BackendAISchema):
    spec: str


class HammerspaceGetObjectiveQuery(BackendAISchema):
    spec: str


class HammerspaceClusterMetricQuery(BackendAISchema):
    precedingDuration: str
    intervalDuration: str
