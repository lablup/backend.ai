from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class ModelCardOrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"


class ProjectModelCardScope(BaseRequestModel):
    """Scope for project-level model card queries."""

    project_id: UUID = Field(description="MODEL_STORE project UUID to scope the query.")
