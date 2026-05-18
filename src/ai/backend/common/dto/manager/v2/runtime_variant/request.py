from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.deployment.request import ModelDefinitionInput
from ai.backend.common.dto.manager.v2.runtime_variant.types import RuntimeVariantOrderField


class CreateRuntimeVariantInput(BaseRequestModel):
    name: str = Field(
        min_length=1, max_length=128, description="Unique name of the runtime variant."
    )
    description: str | None = Field(default=None, description="Description of the runtime variant.")
    reads_vfolder_config_files: bool = Field(
        default=False,
        description=(
            "Whether the runtime engine reads service configuration from files inside the "
            "mounted vfolder (e.g., ``model-definition.yaml``). Defaults to ``False``."
        ),
    )
    default_model_definition: ModelDefinitionInput | None = Field(
        default=None,
        description=(
            "Per-variant baseline ``ModelDefinitionDraft``. Omit (or pass an empty object) "
            "to register a variant whose definition is fully sourced from the vfolder."
        ),
    )


class UpdateRuntimeVariantInput(BaseRequestModel):
    id: UUID = Field(description="ID of the runtime variant to update.")
    name: str | None = Field(default=None, min_length=1, max_length=128, description="New name.")
    description: str | None = Field(default=None, description="New description.")
    reads_vfolder_config_files: bool | None = Field(
        default=None,
        description="New value for ``reads_vfolder_config_files``. ``None`` keeps the existing value.",
    )
    default_model_definition: ModelDefinitionInput | None = Field(
        default=None,
        description=(
            "New baseline draft. ``None`` keeps the existing value; pass an empty object "
            "(``{}``) to clear models back to an empty draft."
        ),
    )


class DeleteRuntimeVariantsInput(BaseRequestModel):
    """Input for deleting multiple runtime variants."""

    ids: list[UUID] = Field(description="List of runtime variant UUIDs to delete.")


class RuntimeVariantFilter(BaseRequestModel):
    name: StringFilter | None = Field(default=None)
    AND: list[RuntimeVariantFilter] | None = Field(default=None)
    OR: list[RuntimeVariantFilter] | None = Field(default=None)
    NOT: list[RuntimeVariantFilter] | None = Field(default=None)


RuntimeVariantFilter.model_rebuild()


class RuntimeVariantOrder(BaseRequestModel):
    field: RuntimeVariantOrderField
    direction: OrderDirection = OrderDirection.ASC


class SearchRuntimeVariantsInput(BaseRequestModel):
    filter: RuntimeVariantFilter | None = Field(default=None)
    order: list[RuntimeVariantOrder] | None = Field(default=None)
    first: int | None = Field(default=None, ge=1)
    after: str | None = Field(default=None)
    last: int | None = Field(default=None, ge=1)
    before: str | None = Field(default=None)
    limit: int | None = Field(default=None, ge=1)
    offset: int | None = Field(default=None, ge=0)
