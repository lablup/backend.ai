"""REST v2 handler for the resource preset domain."""

from __future__ import annotations

import logging
from decimal import Decimal
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.resource_preset.request import (
    AdminSearchResourcePresetsInput,
    CreateResourcePresetInput,
    UpdateResourcePresetInput,
)
from ai.backend.common.dto.manager.v2.resource_preset.response import (
    AdminSearchResourcePresetsPayload,
)
from ai.backend.common.types import ResourceSlot
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import PresetIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.resource_preset import ResourcePresetAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2ResourcePresetHandler:
    """REST v2 handler for resource preset operations."""

    def __init__(self, *, adapter: ResourcePresetAdapter) -> None:
        self._adapter = adapter

    async def search(
        self,
        body: BodyParam[AdminSearchResourcePresetsInput],
    ) -> APIResponse:
        """Search resource presets with filters, orders, and pagination."""
        result = await self._adapter.search(body.parsed)
        payload = AdminSearchResourcePresetsPayload(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

    async def create(
        self,
        body: BodyParam[CreateResourcePresetInput],
    ) -> APIResponse:
        """Create a new resource preset."""
        dto = body.parsed
        resource_slots = ResourceSlot({
            e.resource_type: Decimal(e.quantity) for e in dto.resource_slots
        })
        shared_memory = dto.shared_memory.bytes if dto.shared_memory else None
        result = await self._adapter.create(
            name=dto.name,
            resource_slots=resource_slots,
            shared_memory=shared_memory,
            resource_group_name=dto.resource_group_name,
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def get(
        self,
        path: PathParam[PresetIdPathParam],
    ) -> APIResponse:
        """Retrieve a single resource preset by ID."""
        result = await self._adapter.get(path.parsed.preset_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[PresetIdPathParam],
        body: BodyParam[UpdateResourcePresetInput],
    ) -> APIResponse:
        """Update an existing resource preset."""
        merged_input = body.parsed.model_copy(
            update={"id": path.parsed.preset_id},
        )
        result = await self._adapter.update(merged_input)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(
        self,
        path: PathParam[PresetIdPathParam],
    ) -> APIResponse:
        """Delete a resource preset by ID."""
        result = await self._adapter.delete(path.parsed.preset_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
