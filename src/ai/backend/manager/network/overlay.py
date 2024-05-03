import asyncio
import uuid
from typing import Any, Mapping

import aiodocker
import trafaret as t

from ..plugin.network import AbstractNetworkManagerPlugin

plugin_config_iv = t.Dict({
    t.Key("mtu", default=1500): t.Null | t.ToInt,
}).allow_extra("*")


class OverlayNetworkError(RuntimeError):
    pass


class OverlayNetworkPlugin(AbstractNetworkManagerPlugin):
    docker: aiodocker.Docker

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        super().__init__(plugin_config, local_config)

        plugin_config_iv.check(plugin_config)

    async def init(self, context: Any = None) -> None:
        await super().init(context)
        self.docker = aiodocker.Docker()

        info = await self.docker.system.info()
        if info["Swarm"]["LocalNodeState"] != "active":
            raise OverlayNetworkError("Docker swarm not enabled on system!")

    async def cleanup(self) -> None:
        await self.docker.close()
        await super().cleanup()

    async def create_network(
        self, *, identifier: str | None = None, options: dict[str, Any] = {}
    ) -> dict[str, Any]:
        ident = identifier or f"{uuid.uuid4()}-nw"
        network_name = f"bai-multinode-{ident}"
        mtu: int | None = self.plugin_config["mtu"]

        # Overlay networks can only be created at the Swarm manager.
        create_options = {
            "Name": network_name,
            "Driver": "overlay",
            "Attachable": True,
            "Labels": {
                "ai.backend.cluster-network": "1",
            },
            "Options": {},
        }
        if mtu:
            create_options["Options"] = {"com.docker.network.driver.mtu": str(mtu)}
        await self.docker.networks.create(create_options)

        return {"mode": "overlay", "network_name": network_name, "network_id": str(session.id)}

    async def destroy_network(self, session: SessionRow) -> None:
        try:
            network_name = f"bai-multinode-{session.id}"
            await asyncio.sleep(2.0)
            network = await self.docker.networks.get(network_name)
            await network.delete()
        except aiodocker.DockerError as e:
            if e.status == 404:
                # It may have been auto-destructed when the last container was detached.
                pass
            else:
                raise
