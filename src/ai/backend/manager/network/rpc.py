"""
RPC-based overlay network plugin.

Splits the responsibility of "calling docker swarm overlay create" out of the
manager process and into a separate `swarm-network-daemon` service that is
pinned to a docker swarm manager (leader) node. The manager itself becomes
location-free and can be scheduled to any k8s node.

Protocol — HTTPS (or HTTP) JSON over a single endpoint, authenticated by a
shared bearer token (`X-Auth-Token` header):

    POST   /networks            { "identifier": "...", "options": {...} }
        -> 200 { "network_id": "bai-multinode-...", "options": {...} }
    DELETE /networks/{name}
        -> 204
    GET    /networks/{name}
        -> 200 { "network_id": "...", "options": {...} }  | 404

The daemon implementation lives under
``deploy/helm/backend-ai-swarm-network-daemon/`` (single-file Python aiohttp
service) and runs as a Deployment with a hostPath docker.sock mount on a
swarm-manager-labelled node.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import aiohttp
import trafaret as t

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.plugin.network import AbstractNetworkManagerPlugin, NetworkInfo

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


plugin_config_iv = t.Dict({
    t.Key("endpoint"): t.String,
    t.Key("auth_token", default=""): t.String(allow_blank=True),
    t.Key("request_timeout", default=10.0): t.Float,
}).allow_extra("*")


class RpcOverlayNetworkError(RuntimeError):
    pass


class RpcOverlayNetworkPlugin(AbstractNetworkManagerPlugin):
    """
    Delegates docker swarm overlay network management to an out-of-process
    daemon over HTTP, so the manager no longer needs direct docker.sock
    access to a swarm manager node.
    """

    _session: aiohttp.ClientSession
    _endpoint: str
    _auth_token: str
    _timeout: aiohttp.ClientTimeout

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        super().__init__(plugin_config, local_config)
        self.plugin_config = plugin_config_iv.check(plugin_config)
        self._endpoint = self.plugin_config["endpoint"].rstrip("/")
        self._auth_token = self.plugin_config["auth_token"]
        self._timeout = aiohttp.ClientTimeout(total=self.plugin_config["request_timeout"])

    async def init(self, context: Any = None) -> None:
        headers = {}
        if self._auth_token:
            headers["X-Auth-Token"] = self._auth_token
        self._session = aiohttp.ClientSession(headers=headers, timeout=self._timeout)

        # Quick reachability probe — fail fast if the daemon is unreachable.
        try:
            async with self._session.get(f"{self._endpoint}/health") as resp:
                if resp.status != 200:
                    raise RpcOverlayNetworkError(
                        f"swarm-network-daemon health check returned HTTP {resp.status}"
                    )
        except aiohttp.ClientError as e:
            raise RpcOverlayNetworkError(
                f"swarm-network-daemon at {self._endpoint} is unreachable: {e}"
            ) from e

    async def cleanup(self) -> None:
        await self._session.close()

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        return await super().update_plugin_config(plugin_config)

    async def create_network(
        self, *, identifier: str | None = None, options: dict[str, Any] | None = None
    ) -> NetworkInfo:
        payload: dict[str, Any] = {"options": options or {}}
        if identifier is not None:
            payload["identifier"] = identifier
        async with self._session.post(f"{self._endpoint}/networks", json=payload) as resp:
            body = await resp.json()
            if resp.status != 200:
                raise RpcOverlayNetworkError(f"create_network failed (HTTP {resp.status}): {body}")
        return NetworkInfo(
            network_id=body["network_id"],
            options=body.get("options", {}),
        )

    async def destroy_network(self, network_id: str) -> None:
        async with self._session.delete(f"{self._endpoint}/networks/{network_id}") as resp:
            if resp.status not in (200, 204, 404):
                body = await resp.text()
                raise RpcOverlayNetworkError(
                    f"destroy_network({network_id}) failed (HTTP {resp.status}): {body}"
                )
