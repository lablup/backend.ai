"""Etcd configuration handler using the new ApiHandler pattern.

All handlers use typed parameters (``BodyParam``, ``QueryParam``,
``RequestCtx``) that are automatically extracted by ``_wrap_api_handler``,
and responses are returned as ``APIResponse`` objects.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, QueryParam
from ai.backend.common.dto.manager.etcd.request import (
    DeleteConfigRequest,
    GetConfigRequest,
    GetResourceMetadataQuery,
    SetConfigRequest,
)
from ai.backend.common.dto.manager.etcd.response import (
    ConfigResultResponse,
    OkResultResponse,
    ResourceMetadataResponse,
    ResourceSlotsResponse,
    VfolderTypesResponse,
)
from ai.backend.common.dto.manager.resource.response import ContainerRegistriesResponse
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.services.container_registry.actions.get_container_registries import (
    GetContainerRegistriesAction,
)
from ai.backend.manager.services.etcd_config import (
    DeleteConfigAction,
    GetConfigAction,
    GetResourceMetadataAction,
    GetResourceSlotsAction,
    GetVfolderTypesAction,
    SetConfigAction,
)
from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class EtcdHandler:
    """Etcd configuration API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
        self._processors = processors

    # ------------------------------------------------------------------
    # GET /config/resource-slots
    # ------------------------------------------------------------------

    async def get_resource_slots(self) -> APIResponse:
        log.info("ETCD.GET_RESOURCE_SLOTS ()")
        action = GetResourceSlotsAction()
        result = await self._processors.etcd_config.get_resource_slots.wait_for_complete(action)
        resp = ResourceSlotsResponse(root=result.slots)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # GET /config/resource-slots/details
    # ------------------------------------------------------------------

    async def get_resource_metadata(
        self,
        query: QueryParam[GetResourceMetadataQuery],
    ) -> APIResponse:
        params = query.parsed
        log.info("ETCD.GET_RESOURCE_METADATA (sg:{})", params.sgroup)
        action = GetResourceMetadataAction(sgroup=params.sgroup)
        result = await self._processors.etcd_config.get_resource_metadata.wait_for_complete(action)
        resp = ResourceMetadataResponse(root=result.metadata)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # GET /config/vfolder-types
    # ------------------------------------------------------------------

    async def get_vfolder_types(self) -> APIResponse:
        log.info("ETCD.GET_VFOLDER_TYPES ()")
        action = GetVfolderTypesAction()
        result = await self._processors.etcd_config.get_vfolder_types.wait_for_complete(action)
        resp = VfolderTypesResponse(root=result.types)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # GET /config/docker-registries  (deprecated)
    # ------------------------------------------------------------------

    async def get_docker_registries(self, ctx: UserContext) -> APIResponse:
        log.info("ETCD.GET_DOCKER_REGISTRIES ()")
        log.warning(
            "ETCD.GET_DOCKER_REGISTRIES has been deprecated because it no longer uses etcd."
            " Use /resource/container-registries API instead."
        )
        result = (
            await self._processors.container_registry.get_container_registries.wait_for_complete(
                GetContainerRegistriesAction()
            )
        )
        return APIResponse.build(HTTPStatus.OK, ContainerRegistriesResponse(root=result.registries))

    # ------------------------------------------------------------------
    # POST /config/get  (superadmin)
    # ------------------------------------------------------------------

    async def get_config(
        self,
        body: BodyParam[GetConfigRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Raw etcd key-value read.

        .. warning::

           When reading with ``prefix=True``, simple string-prefix matching
           is used.  Prefer dedicated CRUD APIs when possible.
        """
        params = body.parsed
        log.info(
            "ETCD.GET_CONFIG (ak:{}, key:{}, prefix:{})",
            ctx.access_key,
            params.key,
            params.prefix,
        )
        action = GetConfigAction(key=params.key, prefix=params.prefix)
        result = await self._processors.etcd_config.get_config.wait_for_complete(action)
        return APIResponse.build(HTTPStatus.OK, ConfigResultResponse(result=result.result))

    # ------------------------------------------------------------------
    # POST /config/set  (superadmin)
    # ------------------------------------------------------------------

    async def set_config(
        self,
        body: BodyParam[SetConfigRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Raw etcd key-value write."""
        params = body.parsed
        log.info(
            "ETCD.SET_CONFIG (ak:{}, key:{}, val:{})",
            ctx.access_key,
            params.key,
            params.value,
        )
        action = SetConfigAction(key=params.key, value=params.value)
        await self._processors.etcd_config.set_config.wait_for_complete(action)
        return APIResponse.build(HTTPStatus.OK, OkResultResponse())

    # ------------------------------------------------------------------
    # POST /config/delete  (superadmin)
    # ------------------------------------------------------------------

    async def delete_config(
        self,
        body: BodyParam[DeleteConfigRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Raw etcd key-value delete.

        .. warning::

           When deleting with ``prefix=True``, simple string-prefix matching
           is used.  This may delete sibling keys unexpectedly.
        """
        params = body.parsed
        log.info(
            "ETCD.DELETE_CONFIG (ak:{}, key:{}, prefix:{})",
            ctx.access_key,
            params.key,
            params.prefix,
        )
        action = DeleteConfigAction(key=params.key, prefix=params.prefix)
        await self._processors.etcd_config.delete_config.wait_for_complete(action)
        return APIResponse.build(HTTPStatus.OK, OkResultResponse())
