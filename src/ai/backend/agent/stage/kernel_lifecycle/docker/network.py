from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, override

from ai.backend.agent.exception import NetworkPluginNotFound
from ai.backend.agent.plugin.network import NetworkPluginContext
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import (
    ClusterInfo,
    ClusterSSHKeyPair,
    ClusterSSHPortMapping,
    KernelCreationConfig,
)


@dataclass
class NetworkConfig:
    mode: Optional[str]
    network_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "network_name": self.network_name,
        }


@dataclass
class NetworkSpec:
    kernel_config: KernelCreationConfig

    cluster_size: int
    replicas: Mapping[str, int]  # per-role kernel counts
    network_config: NetworkConfig
    ssh_keypair: ClusterSSHKeyPair
    cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping]

    gwbridge_subnet: Optional[str]
    alternative_bridge: Optional[str]


class NetworkSpecGenerator(ArgsSpecGenerator[NetworkSpec]):
    pass


@dataclass
class NetworkResult:
    container_configs: list[dict[str, Any]]


class NetworkProvisioner(Provisioner[NetworkSpec, NetworkResult]):
    def __init__(self, network_plugin_ctx: NetworkPluginContext) -> None:
        self.network_plugin_ctx = network_plugin_ctx

    @property
    @override
    def name(self) -> str:
        return "docker-network"

    @override
    async def setup(self, spec: NetworkSpec) -> NetworkResult:
        configs = await self._prepare_network_config(spec)
        return NetworkResult(
            container_configs=configs,
        )

    async def _prepare_network_config(self, spec: NetworkSpec) -> list[dict[str, Any]]:
        # FIXME: find out way to inect network ID to kernel resource spec
        base_networks = await self._prepare_base_network(spec)
        alternative_bridge_networks = await self._prepare_alternative_bridge_network(spec)
        rdma_networks = await self._prepare_rdma_network(spec)
        return [
            *base_networks,
            *alternative_bridge_networks,
            *rdma_networks,
        ]

    async def _prepare_base_network(self, spec: NetworkSpec) -> list[dict[str, Any]]:
        match spec.network_config.mode:
            case "bridge":
                return await self._prepare_bridge_network(spec)
            case mode if mode:
                return await self._prepare_plugin_network(spec, mode)
            case _:
                # TODO: handle case when no network mode is specified
                return []

    async def _prepare_bridge_network(self, spec: NetworkSpec) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        result.append({
            "HostConfig": {
                "NetworkMode": spec.network_config.network_name,
            },
            "NetworkingConfig": {
                "EndpointsConfig": {
                    spec.network_config.network_name: {
                        "Aliases": [spec.kernel_config["cluster_hostname"]],
                    },
                },
            },
        })
        return result

    async def _prepare_plugin_network(self, spec: NetworkSpec, mode: str) -> list[dict[str, Any]]:
        try:
            plugin = self.network_plugin_ctx.plugins[mode]
        except KeyError:
            raise NetworkPluginNotFound(f"Network plugin {mode} not loaded!")

        cluster_info = ClusterInfo(
            mode=spec.kernel_config["cluster_mode"],
            size=spec.cluster_size,
            replicas=spec.replicas,
            network_config=spec.network_config.to_dict(),
            ssh_keypair=spec.ssh_keypair,
            cluster_ssh_port_mapping=spec.cluster_ssh_port_mapping,
        )
        container_config = await plugin.join_network(
            spec.kernel_config, cluster_info, **spec.network_config.to_dict()
        )
        result: list[dict[str, Any]] = []
        result.append(container_config)
        if spec.gwbridge_subnet is not None:
            result.append({
                "Env": [f"OMPI_MCA_btl_tcp_if_exclude=127.0.0.1/32,{spec.gwbridge_subnet}"],
            })
        return result

    async def _prepare_alternative_bridge_network(self, spec: NetworkSpec) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        if spec.alternative_bridge is not None:
            result.append({
                "HostConfig": {
                    "NetworkMode": spec.alternative_bridge,
                },
            })
        return result

    async def _prepare_rdma_network(self, spec: NetworkSpec) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        # RDMA mounts
        ib_root = Path("/dev/infiniband")
        if ib_root.is_dir() and (ib_root / "uverbs0").exists():
            result.append({
                "HostConfig": {
                    "Devices": [
                        {
                            "PathOnHost": "/dev/infiniband",
                            "PathInContainer": "/dev/infiniband",
                            "CgroupPermissions": "rwm",
                        },
                    ],
                },
            })
        return result

    @override
    async def teardown(self, resource: NetworkResult) -> None:
        pass


class NetworkStage(ProvisionStage[NetworkSpec, NetworkResult]):
    pass
