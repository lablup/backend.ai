"""REST v2 handlers for the storage namespace domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import (
    APIResponse,
    BaseRootResponseModel,
    BodyParam,
    PathParam,
)
from ai.backend.common.dto.manager.v2.storage_namespace.request import (
    AdminSearchStorageNamespacesInput,
    RegisterStorageNamespaceInput,
    UnregisterStorageNamespaceInput,
)
from ai.backend.common.dto.manager.v2.storage_namespace.response import StorageNamespaceNode
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import StorageIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.storage_namespace import StorageNamespaceAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ListStorageNamespacesPayload(BaseRootResponseModel[list[StorageNamespaceNode]]):
    """Root response model wrapping a list of storage namespace nodes."""

    pass


class V2StorageNamespaceHandler:
    """REST v2 handler for storage namespace endpoints."""

    def __init__(self, *, adapter: StorageNamespaceAdapter) -> None:
        self._adapter = adapter

    async def register(
        self,
        body: BodyParam[RegisterStorageNamespaceInput],
    ) -> APIResponse:
        """Register a new namespace within a storage."""
        result = await self._adapter.register(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def unregister(
        self,
        body: BodyParam[UnregisterStorageNamespaceInput],
    ) -> APIResponse:
        """Unregister a namespace from a storage."""
        result = await self._adapter.unregister(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search(
        self,
        body: BodyParam[AdminSearchStorageNamespacesInput],
    ) -> APIResponse:
        """Search storage namespaces with pagination."""
        result = await self._adapter.search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get_by_storage(
        self,
        path: PathParam[StorageIdPathParam],
    ) -> APIResponse:
        """Get all namespaces for a given storage."""
        items = await self._adapter.get_namespaces(path.parsed.storage_id)
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=ListStorageNamespacesPayload(items),
        )
