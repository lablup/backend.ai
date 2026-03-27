"""REST v2 handler for the HuggingFace registry domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    AdminSearchHuggingFaceRegistriesInput,
    CreateHuggingFaceRegistryInput,
    DeleteHuggingFaceRegistryInput,
    UpdateHuggingFaceRegistryInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import RegistryIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.huggingface_registry import HuggingFaceRegistryAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2HuggingFaceRegistryHandler:
    """REST v2 handler for HuggingFace registry operations."""

    def __init__(self, *, adapter: HuggingFaceRegistryAdapter) -> None:
        self._adapter = adapter

    async def create(
        self,
        body: BodyParam[CreateHuggingFaceRegistryInput],
    ) -> APIResponse:
        """Create a new HuggingFace registry."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def search(
        self,
        body: BodyParam[AdminSearchHuggingFaceRegistriesInput],
    ) -> APIResponse:
        """Search HuggingFace registries with pagination."""
        result = await self._adapter.search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get(
        self,
        path: PathParam[RegistryIdPathParam],
    ) -> APIResponse:
        """Get a single HuggingFace registry by ID."""
        result = await self._adapter.get(path.parsed.registry_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        body: BodyParam[UpdateHuggingFaceRegistryInput],
    ) -> APIResponse:
        """Update an existing HuggingFace registry."""
        result = await self._adapter.update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(
        self,
        body: BodyParam[DeleteHuggingFaceRegistryInput],
    ) -> APIResponse:
        """Delete a HuggingFace registry."""
        result = await self._adapter.delete(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
