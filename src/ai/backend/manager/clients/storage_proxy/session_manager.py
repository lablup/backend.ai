from __future__ import annotations

import asyncio
import itertools
import logging
from collections.abc import Iterable, Mapping
from contextlib import asynccontextmanager as actxmgr
from contextvars import ContextVar
from pathlib import PurePosixPath
from typing import (
    AsyncIterator,
    Final,
    TypedDict,
)

import aiohttp
import attrs
import yarl

from ai.backend.common.defs import NOOP_STORAGE_VOLUME_NAME
from ai.backend.common.types import (
    VFolderID,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.base import (
    StorageProxyClientArgs,
    StorageProxyHTTPClient,
)
from ai.backend.manager.clients.storage_proxy.client_facing_client import (
    StorageProxyClientFacingClient,
)
from ai.backend.manager.clients.storage_proxy.manager_facing_client import (
    StorageProxyManagerFacingClient,
)
from ai.backend.manager.config.unified import VolumesConfig
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.storage import (
    StorageProxyNotFound,
    VFolderGone,
    VFolderOperationFailed,
)
from ai.backend.manager.exceptions import InvalidArgument

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
    _client_facing_clients: Mapping[str, StorageProxyClientFacingClient]

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
    ) -> Mapping[str, StorageProxyClientFacingClient]:
        client_facing_clients = {}
        for proxy_name, proxy_config in storage_config.proxies.items():
            if proxy_name in client_facing_clients:
                log.error("Storage proxy {} is already registered.", proxy_name)
                continue
            connector = aiohttp.TCPConnector(ssl=proxy_config.ssl_verify)
            session = aiohttp.ClientSession(connector=connector)
            client_facing_clients[proxy_name] = StorageProxyClientFacingClient(
                StorageProxyHTTPClient(
                    session,
                    StorageProxyClientArgs(
                        endpoint=yarl.URL(proxy_config.client_api),
                        secret=proxy_config.secret,
                    ),
                )
            )
        return client_facing_clients

    def get_manager_facing_client(self, proxy_name: str) -> StorageProxyManagerFacingClient:
        if proxy_name not in self._manager_facing_clients:
            raise StorageProxyNotFound(
                f"Storage proxy {proxy_name} not found.",
            )
        return self._manager_facing_clients[proxy_name]

    def get_client_facing_client(self, proxy_name: str) -> StorageProxyClientFacingClient:
        if proxy_name not in self._client_facing_clients:
            raise StorageProxyNotFound(
                f"Storage proxy {proxy_name} not found.",
            )
        return self._client_facing_clients[proxy_name]

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
            proxy_info: StorageProxyInfo,
        ) -> Iterable[tuple[str, VolumeInfo]]:
            async with proxy_info.session.request(
                "GET",
                proxy_info.manager_api_url / "volumes",
                raise_for_status=True,
                headers={AUTH_TOKEN_HDR: proxy_info.secret},
            ) as resp:
                reply = await resp.json()
                return ((proxy_name, volume_data) for volume_data in reply["volumes"])

        for proxy_name, proxy_info in self._proxies.items():
            fetch_aws.append(_fetch(proxy_name, proxy_info))
        results = [*itertools.chain(*await asyncio.gather(*fetch_aws))]
        _ctx_volumes_cache.set(results)
        return results

    async def get_sftp_scaling_groups(self, proxy_name: str) -> list[str]:
        if proxy_name not in self._proxies:
            raise IndexError(f"proxy {proxy_name} does not exist")
        return self._proxies[proxy_name].sftp_scaling_groups or []

    async def get_mount_path(
        self,
        vfolder_host: str,
        vfolder_id: VFolderID,
        subpath: PurePosixPath = PurePosixPath("."),
    ) -> str:
        async with self.request(
            vfolder_host,
            "GET",
            "folder/mount",
            json={
                "volume": self.get_proxy_and_volume(vfolder_host)[1],
                "vfid": str(vfolder_id),
                "subpath": str(subpath),
            },
        ) as (_, resp):
            reply = await resp.json()
            return reply["path"]

    @actxmgr
    async def request(
        self,
        vfolder_host_or_proxy_name: str,
        method: str,
        request_relpath: str,
        *args,
        **kwargs,
    ) -> AsyncIterator[tuple[yarl.URL, aiohttp.ClientResponse]]:
        proxy_name, _ = self.get_proxy_and_volume(vfolder_host_or_proxy_name)
        try:
            proxy_info = self._proxies[proxy_name]
        except KeyError:
            raise InvalidArgument("There is no such storage proxy", proxy_name)
        headers = kwargs.pop("headers", {})
        headers[AUTH_TOKEN_HDR] = proxy_info.secret
        async with proxy_info.session.request(
            method,
            proxy_info.manager_api_url / request_relpath,
            *args,
            headers=headers,
            **kwargs,
        ) as client_resp:
            if client_resp.status // 100 != 2:
                try:
                    error_data = await client_resp.json()
                    raise VFolderOperationFailed(
                        extra_msg=error_data.pop("msg", None),
                        extra_data=error_data,
                    )
                except aiohttp.ClientResponseError:
                    # when the response body is not JSON, just raise with status info.
                    if client_resp.status == 410:
                        raise VFolderGone(
                            extra_msg=(
                                "The requested resource is gone. It may have been deleted or moved."
                            ),
                        )
                    raise VFolderOperationFailed(
                        extra_msg=(
                            "Storage proxy responded with "
                            f"{client_resp.status} {client_resp.reason}"
                        ),
                        extra_data=None,
                    )
                except VFolderOperationFailed as e:
                    if client_resp.status // 100 == 5:
                        raise InvalidAPIParameters(e.extra_msg, e.extra_data)
                    # Raise as-is for semantic failures, not server errors.
                    raise
            yield proxy_info.client_api_url, client_resp
