"""Docker-specific agent plugins: the overlay/host network backends, plus the Docker stats API.

The intrinsic CPU/memory compute plugins used to live here and are now in
``ai.backend.agent.intrinsic`` — they read cgroups, which is the same on every runtime, and
holding an aiodocker client meant a containerd-only node could not start its agent. Only things
that genuinely need Docker remain here.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, override

import aiohttp
from aiodocker.docker import DockerContainer
from aiodocker.exceptions import DockerError

from ai.backend.agent.docker.kernel import DockerKernel
from ai.backend.agent.plugin.network import (
    AbstractNetworkAgentPlugin,
    ContainerNetworkCapability,
    ContainerNetworkInfo,
)
from ai.backend.common.asyncio import current_loop
from ai.backend.common.json import dump_json
from ai.backend.common.types import ClusterInfo, KernelCreationConfig
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


async def fetch_api_stats(container: DockerContainer) -> dict[str, Any] | None:
    short_cid = container.id[:7]
    try:
        # aiodocker may return list[dict] or dict depending on version
        ret: list[dict[str, Any]] | dict[str, Any] = await container.stats(stream=False)
    except RuntimeError as e:
        msg = str(e.args[0]).lower()
        if "event loop is closed" in msg or "session is closed" in msg:
            return None
        raise
    except (DockerError, aiohttp.ClientError) as e:
        log.error(
            "cannot read stats (cid:{}): client error: {!r}.",
            short_cid,
            e,
        )
        return None
    else:
        entry = {"read": "0001-01-01"}
        # aiodocker 0.16 or later returns a list of dict, even when not streaming.
        match ret:
            case list() if ret:
                entry = ret[0]
            case dict() if ret:
                entry = ret
            case _:
                # The API may return an empty result upon container termination.
                log.warning(
                    "cannot read stats (cid:{}): got an empty result: {}",
                    short_cid,
                    ret,
                )
                return None
        if entry["read"].startswith("0001-01-01") or entry["preread"].startswith("0001-01-01"):
            return None
        return entry


class OverlayNetworkPlugin(AbstractNetworkAgentPlugin[DockerKernel]):
    @override
    async def init(self, context: Any = None) -> None:
        pass

    @override
    async def cleanup(self) -> None:
        pass

    @override
    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        return await super().update_plugin_config(plugin_config)

    @override
    async def get_capabilities(self) -> set[ContainerNetworkCapability]:
        return set()

    @override
    async def join_network(
        self,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        **kwargs: Any,
    ) -> dict[str, Any]:
        network_name: str = kwargs["network_name"]
        return {
            "HostConfig": {
                "NetworkMode": network_name,
            },
            "NetworkingConfig": {
                "EndpointsConfig": {
                    network_name: {
                        "Aliases": [kernel_config["cluster_hostname"]],
                        "DriverOpts": {"com.docker.network.endpoint.ifname": "baimulti0"},
                    },
                },
            },
        }

    @override
    async def leave_network(self, kernel: DockerKernel) -> None:
        pass


class HostNetworkPlugin(AbstractNetworkAgentPlugin[DockerKernel]):
    @override
    async def init(self, context: Any = None) -> None:
        pass

    @override
    async def cleanup(self) -> None:
        pass

    @override
    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        return await super().update_plugin_config(plugin_config)

    @override
    async def get_capabilities(self) -> set[ContainerNetworkCapability]:
        return {ContainerNetworkCapability.GLOBAL}

    @override
    async def join_network(
        self, kernel_config: KernelCreationConfig, cluster_info: ClusterInfo, **kwargs: Any
    ) -> dict[str, Any]:
        if _cluster_ssh_port_mapping := cluster_info.get("cluster_ssh_port_mapping"):
            return {
                "HostConfig": {
                    "ExtraHosts": [
                        f"{hostname}:{host_port[0]}"
                        for hostname, host_port in _cluster_ssh_port_mapping.items()
                    ],
                    "NetworkMode": "host",
                }
            }
        return {
            "HostConfig": {
                "NetworkMode": "host",
            },
        }

    @override
    async def leave_network(self, kernel: DockerKernel) -> None:
        pass

    @override
    async def prepare_port_forward(
        self, kernel: DockerKernel, bind_host: str, ports: Iterable[tuple[int, int]], **kwargs: Any
    ) -> None:
        host_ports = [p[0] for p in ports]
        scratch_dir = (
            self.local_config["container"]["scratch-root"] / str(kernel.kernel_id)
        ).resolve()
        config_dir: Path = scratch_dir / "config"

        intrinsic_ports = {
            "replin": host_ports[0],
            "replout": host_ports[1],
        }
        for index, port_info in enumerate(kernel.service_ports):
            port_name = port_info["name"]
            if port_name in ("sshd", "ttyd"):
                intrinsic_ports[port_name] = host_ports[index + 2]

        await current_loop().run_in_executor(
            None,
            lambda: (config_dir / "intrinsic-ports.json").write_bytes(dump_json(intrinsic_ports)),
        )

    @override
    async def expose_ports(
        self, kernel: DockerKernel, bind_host: str, ports: Iterable[tuple[int, int]], **kwargs: Any
    ) -> ContainerNetworkInfo:
        host_ports = [p[0] for p in ports]

        intrinsic_ports = {
            "replin": host_ports[0],
            "replout": host_ports[1],
        }
        for index, port_info in enumerate(kernel.service_ports):
            port_name = port_info["name"]
            if port_name in ("sshd", "ttyd"):
                intrinsic_ports[port_name] = host_ports[index + 2]

        return ContainerNetworkInfo(
            bind_host,
            {service_name: {port: port} for service_name, port in intrinsic_ports.items()},
        )
