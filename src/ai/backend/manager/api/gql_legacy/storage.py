from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional

import aiohttp
import graphene

from ai.backend.common.types import HardwareMetadata
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import (
    AUTH_TOKEN_HDR,
    VolumeInfo,
)

from .base import Item, PaginatedList

if TYPE_CHECKING:
    from .schema import GraphQueryContext


__all__ = (
    "StorageVolume",
    "StorageVolumeList",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class StorageVolume(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    # id: {proxy_name}:{name}
    backend = graphene.String()
    fsprefix = graphene.String()
    path = graphene.String()
    capabilities = graphene.List(graphene.String)
    hardware_metadata = graphene.JSONString()
    performance_metric = graphene.JSONString()
    usage = graphene.JSONString()
    proxy = graphene.String(
        description="Added in 24.03.0. Name of the proxy which this volume belongs to."
    )
    name = graphene.String(description="Added in 24.03.0. Name of the storage.")

    async def resolve_hardware_metadata(self, info: graphene.ResolveInfo) -> HardwareMetadata:
        ctx: GraphQueryContext = info.context
        return await ctx.registry.gather_storage_hwinfo(self.id)

    async def resolve_performance_metric(self, info: graphene.ResolveInfo) -> Mapping[str, Any]:
        ctx: GraphQueryContext = info.context
        try:
            proxy_name, volume_name = ctx.storage_manager.get_proxy_and_volume(self.id)
            manager_client = ctx.storage_manager.get_manager_facing_client(proxy_name)
            storage_reply = await manager_client.get_volume_performance_metric(volume_name)
            return storage_reply["metric"]
        except aiohttp.ClientResponseError:
            return {}

    async def resolve_usage(self, info: graphene.ResolveInfo) -> Mapping[str, Any]:
        ctx: GraphQueryContext = info.context
        proxy_name, volume_name = ctx.storage_manager.get_proxy_and_volume(self.id)
        try:
            manager_client = ctx.storage_manager.get_manager_facing_client(proxy_name)
            return await manager_client.get_fs_usage(volume_name)
        except aiohttp.ClientResponseError:
            return {}

    @classmethod
    def from_info(cls, proxy_name: str, volume_info: VolumeInfo) -> StorageVolume:
        return cls(
            id=f"{proxy_name}:{volume_info['name']}",
            backend=volume_info["backend"],
            path=volume_info["path"],
            fsprefix=volume_info["fsprefix"],
            capabilities=volume_info["capabilities"],
            name=volume_info["name"],
            proxy=proxy_name,
        )

    @classmethod
    async def load_count(
        cls,
        ctx: GraphQueryContext,
        filter: Optional[str] = None,
    ) -> int:
        volumes = [*await ctx.storage_manager.get_all_volumes()]
        return len(volumes)

    @classmethod
    async def load_slice(
        cls,
        ctx: GraphQueryContext,
        limit: int,
        offset: int,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence[StorageVolume]:
        # For consistency we add filter/order params here, but it's actually noop.
        if filter is not None or order is not None:
            log.warning(
                "Paginated list of storage volumes igonores custom filtering and/or ordering"
            )
        volumes = [*await ctx.storage_manager.get_all_volumes()]
        return [
            cls.from_info(proxy_name, volume_info)
            for proxy_name, volume_info in volumes[offset : offset + limit]
        ]

    @classmethod
    async def load_by_id(
        cls,
        ctx: GraphQueryContext,
        id: str,
    ) -> StorageVolume:
        proxy_name, volume_name = ctx.storage_manager.get_proxy_and_volume(id)
        try:
            proxy_info = ctx.storage_manager._proxies[proxy_name]
        except KeyError:
            raise ValueError(f"no such storage proxy: {proxy_name!r}")
        async with proxy_info.session.request(
            "GET",
            proxy_info.manager_api_url / "volumes",
            raise_for_status=True,
            headers={AUTH_TOKEN_HDR: proxy_info.secret},
        ) as resp:
            reply = await resp.json()
            for volume_data in reply["volumes"]:
                if volume_data["name"] == volume_name:
                    return cls.from_info(proxy_name, volume_data)
            else:
                raise ValueError(
                    f"no such volume in the storage proxy {proxy_name!r}: {volume_name!r}",
                )


class StorageVolumeList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(StorageVolume, required=True)
