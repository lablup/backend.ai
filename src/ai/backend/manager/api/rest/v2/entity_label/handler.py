"""REST v2 handler for the label domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import APIResponse, BaseRequestModel, BodyParam, PathParam
from ai.backend.common.data.entity.entity_label import EntityLabelID
from ai.backend.common.dto.manager.v2.entity_label.request import (
    PartialBulkPurgeEntityLabelInput,
    PartialBulkUpsertEntityLabelInput,
    SearchEntityLabelsInput,
    UpsertEntityLabelInput,
)
from ai.backend.logging.structured import StructuredLogger

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.entity_label.adapter import EntityLabelAdapter

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


class EntityLabelIdPathParam(BaseRequestModel):
    label_id: UUID = Field(description="Label ID.")


class V2EntityLabelHandler:
    """REST v2 handler for label operations."""

    def __init__(self, *, adapter: EntityLabelAdapter) -> None:
        self._adapter = adapter

    async def upsert_label(
        self,
        body: BodyParam[UpsertEntityLabelInput],
    ) -> APIResponse:
        """Set one key on an entity, replacing the value it carries."""
        result = await self._adapter.upsert(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_upsert_labels(
        self,
        body: BodyParam[PartialBulkUpsertEntityLabelInput],
    ) -> APIResponse:
        """Set keys on several entities in one call, answering per entity."""
        result = await self._adapter.partial_bulk_upsert(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def bulk_upsert_labels(
        self,
        body: BodyParam[PartialBulkUpsertEntityLabelInput],
    ) -> APIResponse:
        """Deprecated. Use `POST /v2/entity-labels/partial-bulk-upsert`."""
        result = await self._adapter.partial_bulk_upsert(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge_label(
        self,
        path: PathParam[EntityLabelIdPathParam],
    ) -> APIResponse:
        """Take one label off, named by its own id."""
        result = await self._adapter.purge(EntityLabelID(path.parsed.label_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_purge_labels(
        self,
        body: BodyParam[PartialBulkPurgeEntityLabelInput],
    ) -> APIResponse:
        """Take several labels off in one call, answering per label."""
        result = await self._adapter.partial_bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def bulk_purge_labels(
        self,
        body: BodyParam[PartialBulkPurgeEntityLabelInput],
    ) -> APIResponse:
        """Deprecated. Use `POST /v2/entity-labels/partial-bulk-purge`."""
        result = await self._adapter.partial_bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search_labels(
        self,
        body: BodyParam[SearchEntityLabelsInput],
    ) -> APIResponse:
        """Read the labels on the entities named."""
        result = await self._adapter.search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
