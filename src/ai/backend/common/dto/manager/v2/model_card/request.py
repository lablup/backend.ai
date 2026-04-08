from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.deployment.request import DeploymentStrategyInput
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
    model_store_project_id: UUID = Field(
        description="MODEL_STORE project UUID where the model card belongs."
    )
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
    storage_host: StringFilter | None = Field(
        default=None,
        description=(
            "Filter by the storage host backing the model card's VFolder. "
            "Evaluated as an EXISTS subquery joining the model VFolder's host column."
        ),
    )
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
    # Optional deployment-level overrides. When set, these values win over
    # whatever the revision preset specifies. When left as ``None``, the
    # preset's default is used (falling back to system defaults if the preset
    # does not specify the value either).
    open_to_public: bool | None = Field(
        default=None,
        description="Override for the deployment's open_to_public setting. "
        "If omitted, the preset default is used; otherwise falls back to False.",
    )
    replica_count: int | None = Field(
        default=None,
        ge=0,
        description="Override for the deployment's replica_count. "
        "If omitted, the preset default is used; otherwise falls back to "
        "desired_replica_count or 1.",
    )
    revision_history_limit: int | None = Field(
        default=None,
        ge=0,
        description="Override for the deployment's revision_history_limit. "
        "If omitted, the preset default is used; otherwise falls back to 10.",
    )
    deployment_strategy: DeploymentStrategyInput | None = Field(
        default=None,
        description="Override for the deployment strategy (rolling or blue-green). "
        "If omitted, the preset default is used; otherwise no policy is attached.",
    )
