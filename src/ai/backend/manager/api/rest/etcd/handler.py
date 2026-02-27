"""Etcd configuration handler using the new ApiHandler pattern.

All handlers use typed parameters (``BodyParam``, ``QueryParam``,
``RequestCtx``) that are automatically extracted by ``_wrap_api_handler``,
and responses are returned as ``APIResponse`` objects.
"""

from __future__ import annotations

import collections
import logging
from collections.abc import Mapping
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Final, cast

import sqlalchemy as sa
from aiohttp import web

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
from ai.backend.common.json import load_json
from ai.backend.common.types import AcceleratorMetadata
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.resource import get_container_registries
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.agent import AgentRow, AgentStatus

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

KNOWN_SLOT_METADATA: dict[str, AcceleratorMetadata] = {
    "cpu": {
        "slot_name": "cpu",
        "description": "CPU",
        "human_readable_name": "CPU",
        "display_unit": "Core",
        "number_format": {"binary": False, "round_length": 0},
        "display_icon": "cpu",
    },
    "mem": {
        "slot_name": "ram",
        "description": "Memory",
        "human_readable_name": "RAM",
        "display_unit": "GiB",
        "number_format": {"binary": True, "round_length": 0},
        "display_icon": "cpu",
    },
    "cuda.device": {
        "slot_name": "cuda.device",
        "human_readable_name": "GPU",
        "description": "CUDA-capable GPU",
        "display_unit": "GPU",
        "number_format": {"binary": False, "round_length": 0},
        "display_icon": "gpu1",
    },
    "cuda.shares": {
        "slot_name": "cuda.shares",
        "human_readable_name": "fGPU",
        "description": "CUDA-capable GPU (fractional)",
        "display_unit": "fGPU",
        "number_format": {"binary": False, "round_length": 2},
        "display_icon": "gpu1",
    },
    "rocm.device": {
        "slot_name": "rocm.device",
        "human_readable_name": "GPU",
        "description": "ROCm-capable GPU",
        "display_unit": "GPU",
        "number_format": {"binary": False, "round_length": 0},
        "display_icon": "gpu2",
    },
    "tpu.device": {
        "slot_name": "tpu.device",
        "human_readable_name": "TPU",
        "description": "TPU device",
        "display_unit": "GPU",
        "number_format": {"binary": False, "round_length": 0},
        "display_icon": "tpu",
    },
}


class EtcdHandler:
    """Etcd configuration API handler.

    Dependencies are resolved at request time via middleware parameters
    because the handler is instantiated inside ``create_app()`` before
    ``RootContext`` is available.  When the server bootstrap is unified
    (future issue), constructor DI can replace the middleware approach.
    """

    # ------------------------------------------------------------------
    # GET /config/resource-slots
    # ------------------------------------------------------------------

    async def get_resource_slots(self, ctx: RequestCtx) -> APIResponse:
        log.info("ETCD.GET_RESOURCE_SLOTS ()")
        root_ctx: RootContext = ctx.request.app["_root.context"]
        known_slots = await root_ctx.config_provider.legacy_etcd_config_loader.get_resource_slots()
        resp = ResourceSlotsResponse(root={str(k): v for k, v in known_slots.items()})
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # GET /config/resource-slots/details
    # ------------------------------------------------------------------

    async def get_resource_metadata(
        self,
        query: QueryParam[GetResourceMetadataQuery],
        ctx: RequestCtx,
    ) -> APIResponse:
        params = query.parsed
        log.info("ETCD.GET_RESOURCE_METADATA (sg:{})", params.sgroup)
        root_ctx: RootContext = ctx.request.app["_root.context"]
        known_slots = await root_ctx.config_provider.legacy_etcd_config_loader.get_resource_slots()

        # Collect plugin-reported accelerator metadata
        computer_metadata = await root_ctx.valkey_stat.get_computer_metadata()
        reported_accelerator_metadata: dict[str, AcceleratorMetadata] = {
            slot_name: cast(AcceleratorMetadata, load_json(metadata_json))
            for slot_name, metadata_json in computer_metadata.items()
        }

        # Merge the reported metadata and preconfigured metadata (for legacy plugins)
        accelerator_metadata: dict[str, AcceleratorMetadata] = {}
        for slot_name, metadata in collections.ChainMap(
            reported_accelerator_metadata,
            KNOWN_SLOT_METADATA,
        ).items():
            if slot_name in known_slots:
                accelerator_metadata[slot_name] = metadata

        # Optionally filter by the slots reported by the given resource group's agents
        if params.sgroup is not None:
            available_slot_keys: set[str] = set()
            async with root_ctx.db.begin_readonly_session() as db_sess:
                result = await db_sess.execute(
                    sa.select(AgentRow).where(
                        (AgentRow.status == AgentStatus.ALIVE)
                        & (AgentRow.scaling_group == params.sgroup)
                        & (AgentRow.schedulable == sa.true())
                    )
                )
                for agent in result.scalars().all():
                    available_slot_keys.update(agent.available_slots.keys())
            accelerator_metadata = {
                str(k): v
                for k, v in accelerator_metadata.items()
                if k in {"cpu", "mem", *available_slot_keys}
            }

        resp = ResourceMetadataResponse(root=accelerator_metadata)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # GET /config/vfolder-types
    # ------------------------------------------------------------------

    async def get_vfolder_types(self, ctx: RequestCtx) -> APIResponse:
        log.info("ETCD.GET_VFOLDER_TYPES ()")
        root_ctx: RootContext = ctx.request.app["_root.context"]
        vfolder_types = await root_ctx.config_provider.legacy_etcd_config_loader.get_vfolder_types()
        resp = VfolderTypesResponse(root=list(vfolder_types))
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # GET /config/docker-registries  (deprecated)
    # ------------------------------------------------------------------

    async def get_docker_registries(self, ctx: RequestCtx) -> web.StreamResponse:
        log.info("ETCD.GET_DOCKER_REGISTRIES ()")
        log.warning(
            "ETCD.GET_DOCKER_REGISTRIES has been deprecated because it no longer uses etcd."
            " Use /resource/container-registries API instead."
        )
        return await get_container_registries(ctx.request)

    # ------------------------------------------------------------------
    # POST /config/get  (superadmin)
    # ------------------------------------------------------------------

    async def get_config(
        self,
        body: BodyParam[GetConfigRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        """Raw etcd key-value read.

        .. warning::

           When reading with ``prefix=True``, simple string-prefix matching
           is used.  Prefer dedicated CRUD APIs when possible.
        """
        params = body.parsed
        root_ctx: RootContext = req.request.app["_root.context"]
        log.info(
            "ETCD.GET_CONFIG (ak:{}, key:{}, prefix:{})",
            ctx.access_key,
            params.key,
            params.prefix,
        )
        if params.prefix:
            tree_value = dict(await root_ctx.etcd.get_prefix_dict(params.key))
            return APIResponse.build(HTTPStatus.OK, ConfigResultResponse(result=tree_value))
        scalar_value = await root_ctx.etcd.get(params.key)
        return APIResponse.build(HTTPStatus.OK, ConfigResultResponse(result=scalar_value))

    # ------------------------------------------------------------------
    # POST /config/set  (superadmin)
    # ------------------------------------------------------------------

    async def set_config(
        self,
        body: BodyParam[SetConfigRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        """Raw etcd key-value write."""
        params = body.parsed
        root_ctx: RootContext = req.request.app["_root.context"]
        log.info(
            "ETCD.SET_CONFIG (ak:{}, key:{}, val:{})",
            ctx.access_key,
            params.key,
            params.value,
        )
        if isinstance(params.value, Mapping):
            updates: dict[str, Any] = {}

            def flatten(prefix: str, o: Mapping[str, Any]) -> None:
                for k, v in o.items():
                    inner_prefix = prefix if k == "" else f"{prefix}/{k}"
                    if isinstance(v, Mapping):
                        flatten(inner_prefix, v)
                    else:
                        updates[inner_prefix] = v

            flatten(params.key, params.value)
            if len(updates) > 16:
                raise InvalidAPIParameters(
                    "Too large update! Split into smaller key-value pair sets."
                )
            await root_ctx.etcd.put_dict(updates)
        else:
            await root_ctx.etcd.put(params.key, params.value)
        return APIResponse.build(HTTPStatus.OK, OkResultResponse())

    # ------------------------------------------------------------------
    # POST /config/delete  (superadmin)
    # ------------------------------------------------------------------

    async def delete_config(
        self,
        body: BodyParam[DeleteConfigRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        """Raw etcd key-value delete.

        .. warning::

           When deleting with ``prefix=True``, simple string-prefix matching
           is used.  This may delete sibling keys unexpectedly.
        """
        params = body.parsed
        root_ctx: RootContext = req.request.app["_root.context"]
        log.info(
            "ETCD.DELETE_CONFIG (ak:{}, key:{}, prefix:{})",
            ctx.access_key,
            params.key,
            params.prefix,
        )
        if params.prefix:
            await root_ctx.etcd.delete_prefix(params.key)
        else:
            await root_ctx.etcd.delete(params.key)
        return APIResponse.build(HTTPStatus.OK, OkResultResponse())
