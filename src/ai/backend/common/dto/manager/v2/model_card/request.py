from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.model_card.types import (
    ModelCardAccessLevel,
    ModelCardOrderField,
)


class ResourceSlotEntryInput(BaseRequestModel):
    resource_type: str = Field(description="Resource type name (e.g. cpu, mem).")
    quantity: str = Field(description="Resource quantity as string.")


class CreateModelCardInput(BaseRequestModel):
    name: str = Field(min_length=1, max_length=512, description="Model card name.")
    vfolder_id: UUID = Field(description="VFolder ID containing the model.")
    project_id: UUID = Field(description="Project ID (must be MODEL_STORE type).")
    domain_name: str | None = Field(
        default=None,
        max_length=64,
        description="Domain name. If omitted, uses the requester's domain.",
    )
    author: str | None = Field(default=None, max_length=256)
    title: str | None = Field(default=None, max_length=512)
    model_version: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None)
    task: str | None = Field(default=None, max_length=128)
    category: str | None = Field(default=None, max_length=128)
    architecture: str | None = Field(default=None, max_length=128)
    framework: list[str] = Field(default_factory=list)
    label: list[str] = Field(default_factory=list)
    license: str | None = Field(default=None, max_length=128)
    min_resource: list[ResourceSlotEntryInput] | None = Field(default=None)
    readme: str | None = Field(default=None)
    access_level: ModelCardAccessLevel = Field(
        default=ModelCardAccessLevel.INTERNAL, description="Access level."
    )


class UpdateModelCardInput(BaseRequestModel):
    id: UUID = Field(description="Model card ID.")
    name: str | None = Field(default=None, min_length=1, max_length=512)
    author: str | Sentinel | None = Field(default=SENTINEL)
    title: str | Sentinel | None = Field(default=SENTINEL)
    model_version: str | Sentinel | None = Field(default=SENTINEL)
    description: str | Sentinel | None = Field(default=SENTINEL)
    task: str | Sentinel | None = Field(default=SENTINEL)
    category: str | Sentinel | None = Field(default=SENTINEL)
    architecture: str | Sentinel | None = Field(default=SENTINEL)
    framework: list[str] | None = Field(default=None)
    label: list[str] | None = Field(default=None)
    license: str | Sentinel | None = Field(default=SENTINEL)
    min_resource: list[ResourceSlotEntryInput] | Sentinel | None = Field(default=SENTINEL)
    readme: str | Sentinel | None = Field(default=SENTINEL)
    access_level: ModelCardAccessLevel | Sentinel | None = Field(default=SENTINEL)


class ModelCardFilter(BaseRequestModel):
    name: StringFilter | None = Field(default=None)
    domain_name: str | None = Field(default=None)
    project_id: UUID | None = Field(default=None)
    AND: list[ModelCardFilter] | None = Field(default=None)
    OR: list[ModelCardFilter] | None = Field(default=None)
    NOT: list[ModelCardFilter] | None = Field(default=None)


ModelCardFilter.model_rebuild()


class ModelCardOrder(BaseRequestModel):
    field: ModelCardOrderField
    direction: OrderDirection = OrderDirection.ASC


class SearchModelCardsInput(BaseRequestModel):
    filter: ModelCardFilter | None = Field(default=None)
    order: list[ModelCardOrder] | None = Field(default=None)
    first: int | None = Field(default=None, ge=1)
    after: str | None = Field(default=None)
    last: int | None = Field(default=None, ge=1)
    before: str | None = Field(default=None)
    limit: int | None = Field(default=None, ge=1)
    offset: int | None = Field(default=None, ge=0)


class DeleteModelCardsInput(BaseRequestModel):
    """Input for deleting multiple model cards."""

    ids: list[UUID] = Field(description="List of model card UUIDs to delete.")


class DeployModelCardInput(BaseRequestModel):
    """Input for creating a deployment from a model card."""

    project_id: UUID = Field(
        description="Target project UUID where the deployment will be created. "
        "Must be a general project, not MODEL_STORE.",
    )
    revision_preset_id: UUID = Field(
        description="Deployment revision preset UUID that provides image, "
        "runtime variant, resource slots, environ, and startup command.",
    )
    resource_group: str = Field(
        description="Resource group (scaling group) name for scheduling.",
    )
    desired_replica_count: int = Field(
        default=1,
        ge=1,
        description="Number of replicas to deploy.",
    )
