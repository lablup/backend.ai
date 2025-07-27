from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, override

from ai.backend.agent.exception import NetworkPluginNotFound
from ai.backend.agent.plugin.network import AbstractNetworkAgentPlugin, NetworkPluginContext
from ai.backend.agent.utils import update_nested_dict
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

from ..defs import BRIDGE_NETWORK_MODE
from ..types import NetworkConfig


@dataclass
class NetworkPreSetupSpec:
    kernel_config: KernelCreationConfig

    cluster_size: int
    replicas: Mapping[str, int]  # per-role kernel counts
    network_config: NetworkConfig
    ssh_keypair: ClusterSSHKeyPair
    cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping]

    gwbridge_subnet: Optional[str]
    alternative_bridge: Optional[str]


class NetworkPreSetupSpecGenerator(ArgsSpecGenerator[NetworkPreSetupSpec]):
    pass


@dataclass
class NetworkPreSetupResult:
    mode: str
    container_arg: dict[str, Any]
    network_plugin: Optional[AbstractNetworkAgentPlugin]


class NetworkPreSetupProvisioner(Provisioner[NetworkPreSetupSpec, NetworkPreSetupResult]):
    def __init__(self, network_plugin_ctx: NetworkPluginContext) -> None:
        self._network_plugin_ctx = network_plugin_ctx

    @property
    @override
    def name(self) -> str:
        return "docker-network-pre-setup"

    @override
    async def setup(self, spec: NetworkPreSetupSpec) -> NetworkPreSetupResult:
        bridge_network_config = await self._parse_arg_bridge_network(spec)

        network_plugin = self._get_network_plugin(spec)
        plugin_network_config = await self._parse_arg_plugin_network(network_plugin, spec)

        alternative_bridge_networks = await self._parse_arg_alternative_bridge_network(spec)
        rdma_networks = await self._parse_arg_rdma_network(spec)

        configs = [
            *bridge_network_config,
            *plugin_network_config,
            *alternative_bridge_networks,
            *rdma_networks,
        ]
        container_arg: dict[str, Any] = {}
        for config in configs:
            update_nested_dict(container_arg, config)
        mode = spec.network_config.mode or BRIDGE_NETWORK_MODE
        return NetworkPreSetupResult(
            mode=mode,
            container_arg=container_arg,
            network_plugin=network_plugin,
        )

    def _get_network_plugin(
        self, spec: NetworkPreSetupSpec
    ) -> Optional[AbstractNetworkAgentPlugin]:
        """
        Retrieve the network plugin based on the specified network mode.
        """
        if spec.network_config.mode == BRIDGE_NETWORK_MODE:
            return None  # No plugin needed for bridge mode
        elif spec.network_config.mode:
            try:
                return self._network_plugin_ctx.plugins[spec.network_config.mode]
            except KeyError:
                raise NetworkPluginNotFound(
                    f"Network plugin {spec.network_config.mode} not loaded!"
                )
        return None

    async def _parse_arg_bridge_network(self, spec: NetworkPreSetupSpec) -> list[dict[str, Any]]:
        is_bridge_network = spec.network_config.mode == BRIDGE_NETWORK_MODE
        if not is_bridge_network:
            return []
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

    async def _parse_arg_plugin_network(
        self, plugin: Optional[AbstractNetworkAgentPlugin], spec: NetworkPreSetupSpec
    ) -> list[dict[str, Any]]:
        if plugin is None:
            return []
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

    async def _parse_arg_alternative_bridge_network(
        self, spec: NetworkPreSetupSpec
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        if spec.alternative_bridge is not None:
            result.append({
                "HostConfig": {
                    "NetworkMode": spec.alternative_bridge,
                },
            })
        return result

    async def _parse_arg_rdma_network(self, spec: NetworkPreSetupSpec) -> list[dict[str, Any]]:
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
    async def teardown(self, resource: NetworkPreSetupResult) -> None:
        pass


class NetworkPreSetupStage(ProvisionStage[NetworkPreSetupSpec, NetworkPreSetupResult]):
    pass
