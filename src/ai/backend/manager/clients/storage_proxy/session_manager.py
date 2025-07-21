from __future__ import annotations

import asyncio
import itertools
import logging
from collections.abc import Iterable, Mapping
from contextvars import ContextVar
from typing import (
    Final,
    TypedDict,
)

import aiohttp
import attrs
import yarl

from ai.backend.common.defs import NOOP_STORAGE_VOLUME_NAME
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.base import (
    StorageProxyClientArgs,
    StorageProxyHTTPClient,
)
from ai.backend.manager.clients.storage_proxy.client_facing_info import (
    StorageProxyClientFacingInfo,
)
from ai.backend.manager.clients.storage_proxy.manager_facing_client import (
    StorageProxyManagerFacingClient,
)
from ai.backend.manager.config.unified import VolumesConfig
from ai.backend.manager.errors.storage import (
    StorageProxyNotFound,
)

_ctx_volumes_cache: ContextVar[list[tuple[str, VolumeInfo]]] = ContextVar("_ctx_volumes")


AUTH_TOKEN_HDR: Final = "X-BackendAI-Storage-Auth-Token"


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VolumeInfo(TypedDict):
    name: str
    backend: str
    path: str
    fsprefix: str
    capabilities: list[str]


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class StorageProxyInfo:
    session: aiohttp.ClientSession
    secret: str
    client_api_url: yarl.URL
    manager_api_url: yarl.URL
    sftp_scaling_groups: list[str]


class StorageSessionManager:
    _proxies: Mapping[str, StorageProxyInfo]
    _exposed_volume_info: list[str]
    _manager_facing_clients: Mapping[str, StorageProxyManagerFacingClient]
    _client_facing_clients: Mapping[str, StorageProxyClientFacingInfo]

    def __init__(self, storage_config: VolumesConfig) -> None:
        self.config = storage_config
        self._exposed_volume_info = self.config.exposed_volume_info
        self._proxies = {}
        for proxy_name, proxy_config in self.config.proxies.items():
            connector = aiohttp.TCPConnector(ssl=proxy_config.ssl_verify)
            session = aiohttp.ClientSession(connector=connector)
            self._proxies[proxy_name] = StorageProxyInfo(
                session=session,
                secret=proxy_config.secret,
                client_api_url=yarl.URL(proxy_config.client_api),
                manager_api_url=yarl.URL(proxy_config.manager_api),
                sftp_scaling_groups=proxy_config.sftp_scaling_groups or [],
            )
        self._manager_facing_clients = self._setup_manager_facing_clients(storage_config)
        self._client_facing_clients = self._setup_client_facing_clients(storage_config)

    @classmethod
    def _setup_manager_facing_clients(
        cls,
        storage_config: VolumesConfig,
    ) -> Mapping[str, StorageProxyManagerFacingClient]:
        manager_facing_clients = {}
        for proxy_name, proxy_config in storage_config.proxies.items():
            if proxy_name in manager_facing_clients:
                log.error("Storage proxy {} is already registered.", proxy_name)
                continue
            connector = aiohttp.TCPConnector(ssl=proxy_config.ssl_verify)
            session = aiohttp.ClientSession(connector=connector)
            manager_facing_clients[proxy_name] = StorageProxyManagerFacingClient(
                StorageProxyHTTPClient(
                    session,
                    StorageProxyClientArgs(
                        endpoint=yarl.URL(proxy_config.manager_api),
                        secret=proxy_config.secret,
                    ),
                )
            )
        return manager_facing_clients

    @classmethod
    def _setup_client_facing_clients(
        cls,
        storage_config: VolumesConfig,
    ) -> Mapping[str, StorageProxyClientFacingInfo]:
        client_facing_clients = {}
        for proxy_name, proxy_config in storage_config.proxies.items():
            if proxy_name in client_facing_clients:
                log.error("Storage proxy {} is already registered.", proxy_name)
                continue
            client_facing_clients[proxy_name] = StorageProxyClientFacingInfo(
                base_url=yarl.URL(proxy_config.client_api),
            )
        return client_facing_clients

    def get_manager_facing_client(self, proxy_name: str) -> StorageProxyManagerFacingClient:
        if proxy_name not in self._manager_facing_clients:
            raise StorageProxyNotFound(
                f"Storage proxy {proxy_name} not found.",
            )
        return self._manager_facing_clients[proxy_name]

    def get_client_api_url(self, proxy_name: str) -> yarl.URL:
        client = self._client_facing_clients.get(proxy_name, None)
        if client is None:
            raise StorageProxyNotFound(
                f"Storage proxy {proxy_name} not found.",
            )
        return client.base_url

    async def aclose(self) -> None:
        close_aws = []
        for proxy_info in self._proxies.values():
            close_aws.append(proxy_info.session.close())
        await asyncio.gather(*close_aws, return_exceptions=True)

    @staticmethod
    def _split_host(vfolder_host: str) -> tuple[str, str]:
        proxy_name, _, volume_name = vfolder_host.partition(":")
        return proxy_name, volume_name

    @classmethod
    def get_proxy_and_volume(
        cls, vfolder_host: str, should_be_noop: bool = False
    ) -> tuple[str, str]:
        proxy_name, volume_name = cls._split_host(vfolder_host)
        if should_be_noop:
            volume_name = NOOP_STORAGE_VOLUME_NAME
        return proxy_name, volume_name

    @staticmethod
    def parse_host(proxy_name: str, volume_name: str) -> str:
        return f"{proxy_name}:{volume_name}"

    @classmethod
    def is_noop_host(cls, vfolder_host: str) -> bool:
        return cls._split_host(vfolder_host)[1] == NOOP_STORAGE_VOLUME_NAME

    async def get_all_volumes(self) -> Iterable[tuple[str, VolumeInfo]]:
        """
        Returns a list of tuple
        [(proxy_name: str, volume_info: VolumeInfo), ...]
        """
        try:
            # per-asyncio-task cache
            return _ctx_volumes_cache.get()
        except LookupError:
            pass
        fetch_aws = []

        async def _fetch(
            proxy_name: str,
            client: StorageProxyManagerFacingClient,
        ) -> Iterable[tuple[str, VolumeInfo]]:
            reply = await client.get_volumes()
            return ((proxy_name, volume_data) for volume_data in reply["volumes"])

        for proxy_name, client in self._manager_facing_clients.items():
            fetch_aws.append(_fetch(proxy_name, client))
        results = [*itertools.chain(*await asyncio.gather(*fetch_aws))]
        _ctx_volumes_cache.set(results)
        return results

    async def get_sftp_scaling_groups(self, proxy_name: str) -> list[str]:
        if proxy_name not in self._proxies:
            raise IndexError(f"proxy {proxy_name} does not exist")
        return self._proxies[proxy_name].sftp_scaling_groups or []
