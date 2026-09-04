from __future__ import annotations

import asyncio
import uuid
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, override

import aiodocker
import trafaret as t
from aiodocker.exceptions import DockerError

from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.network.pairing import require_members_can_serve_driver
from ai.backend.manager.plugin.network import AbstractNetworkManagerPlugin, NetworkInfo

plugin_config_iv = t.Dict({
    t.Key("mtu", default=1500): t.Null | t.ToInt,
}).allow_extra("*")


class OverlayNetworkError(RuntimeError):
    pass


class OverlayNetworkPlugin(AbstractNetworkManagerPlugin):
    docker: aiodocker.Docker
    _etcd: AsyncEtcd | None

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        super().__init__(plugin_config, local_config)
        self._etcd = None

        self.plugin_config = plugin_config_iv.check(plugin_config)

    @override
    async def init(self, context: Any = None) -> None:
        self.docker = aiodocker.Docker()
        # Needed to read each member agent's published backend (see _require_members_overlay_capable).
        # Built here rather than injected, matching how CNINetworkPlugin gets its own client.
        etcd_config = EtcdConfig.model_validate(self.local_config["etcd"]).to_dataclass()
        self._etcd = AsyncEtcd.create_from_config(etcd_config)
        await self._etcd.open()

        info = await self.docker.system.info()
        if info["Swarm"]["LocalNodeState"] != "active":
            raise OverlayNetworkError(
                "Docker Swarm is not enabled on this system. "
                "To use overlay networks for multi-node sessions, initialize Docker Swarm with: "
                "'docker swarm init' or 'docker swarm init --advertise-addr <IP_ADDRESS>'"
            )

    @override
    async def cleanup(self) -> None:
        await self.docker.close()
        if self._etcd is not None:
            await self._etcd.close()
            self._etcd = None

    async def _require_members_overlay_capable(self, member_agents: list[str]) -> None:
        """Refuse a member agent whose backend cannot serve the 'overlay' driver.

        This is the half that was missing. 'overlay' is the DEFAULT inter-container driver, and a
        containerd agent does not speak Swarm at all: it would quietly put every kernel on a
        node-local bridge, so a multi-node session would come up with kernels unable to reach each
        other and no error anywhere. The symmetric check for 'cni' lives in CNINetworkPlugin.
        """
        if self._etcd is None:
            return  # not initialized (unit tests construct the plugin directly)
        await require_members_can_serve_driver(self._etcd, "overlay", member_agents)

    @override
    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        return await super().update_plugin_config(plugin_config)

    @override
    async def create_network(
        self, *, identifier: str | None = None, options: dict[str, Any] | None = None
    ) -> NetworkInfo:
        if options is None:
            options = {}
        await self._require_members_overlay_capable(list(options.get("member_agents") or []))
        ident = identifier or f"{uuid.uuid4()}-nw"
        network_name = f"bai-multinode-{ident}"
        mtu: int | None = self.plugin_config["mtu"]

        try:
            # Check and return if existing.
            item = await self.docker.networks.get(network_name)
            info = await item.show()
            return NetworkInfo(
                network_id=network_name,
                options={
                    "mode": info["Driver"],
                    "network_name": network_name,
                    "network_id": info["Id"],
                },
            )
        except DockerError as e:
            if e.status == HTTPStatus.NOT_FOUND:
                # If not exists, proceed to create one.
                pass
            else:
                raise

        # Overlay networks can only be created at the Swarm manager.
        create_options: dict[str, Any] = {
            "Name": network_name,
            "Driver": "overlay",
            "Attachable": True,
            "Labels": {
                "ai.backend.cluster-network": "1",
            },
            "Options": {},
        }
        if mtu:
            create_options["Options"]["com.docker.network.driver.mtu"] = str(mtu)
        result = await self.docker.networks.create(create_options)
        return NetworkInfo(
            network_id=network_name,
            options={
                "mode": "overlay",
                "network_name": network_name,
                "network_id": result.id,
            },
        )

    @override
    async def destroy_network(self, network_id: str) -> None:
        try:
            await asyncio.sleep(2.0)
            network = await self.docker.networks.get(network_id)
            await network.delete()
        except aiodocker.DockerError as e:
            if e.status == 404:
                # It may have been auto-destructed when the last container was detached.
                pass
            else:
                raise
