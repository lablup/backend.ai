from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.runtime_variant.types import RuntimeVariantOrderField


class CreateRuntimeVariantInput(BaseRequestModel):
    name: str = Field(
        min_length=1, max_length=128, description="Unique name of the runtime variant."
    )
    description: str | None = Field(default=None, description="Description of the runtime variant.")


class UpdateRuntimeVariantInput(BaseRequestModel):
    id: UUID = Field(description="ID of the runtime variant to update.")
    name: str | None = Field(default=None, min_length=1, max_length=128, description="New name.")
    description: str | None = Field(default=None, description="New description.")


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
