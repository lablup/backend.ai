from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope


class ModelCardAccessLevel(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"


class ModelCardOrderField(StrEnum):
    ENTITY_ID = "entity_id"
    NAME = "name"
    VFOLDER_ID = "vfolder_id"
    DOMAIN_NAME = "domain_name"
    PROJECT_ID = "project_id"
    CREATOR_ID = "creator_id"
    AUTHOR = "author"
    TITLE = "title"
    MODEL_VERSION = "model_version"
    TASK = "task"
    CATEGORY = "category"
    ARCHITECTURE = "architecture"
    LICENSE = "license"
    ACCESS_LEVEL = "access_level"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class ProjectModelCardScope(BaseRequestModel):
    """Scope for project-level model card queries."""

    project_id: UUID = Field(description="MODEL_STORE project UUID to scope the query.")


class ModelCardAvailablePresetsScope(BaseRequestModel):
    """Scope for querying available presets that satisfy a model card's resource requirements."""

    model_card_id: UUID = Field(
        description="Model card UUID to check resource requirements against."
    )


class ModelCardUsedBy(BaseRequestModel):
    """Entities whose use narrows the model cards read; every id is AND-ed.

    An entity the caller cannot read refuses the request. Model cards the caller cannot
    read are left out even when a listed entity uses them.
    """

    vfolder: list[UUID] | None = Field(
        default=None, description="VFolders the model card is built on"
    )


class ModelCardScope(BaseRequestModel):
    """Scope for the scoped model card query.

    Each list is OR'd internally and across lists. Raises an error if every field is
    empty.
    """

    domain: list[UUIDScope] | None = Field(
        default=None, description="Domains whose model cards are being read"
    )
    project: list[UUIDScope] | None = Field(
        default=None, description="Projects whose model cards are being read"
    )
    user: list[UUIDScope] | None = Field(
        default=None, description="Users whose model cards are being read"
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> ModelCardScope:
        if not self.domain and not self.project and not self.user:
            raise ValueError(
                "ModelCardScope requires a non-empty value for 'domain', 'project' or 'user'"
            )
        return self
