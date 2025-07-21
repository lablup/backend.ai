"""
Kernel object creation stage for kernel lifecycle.

This stage handles creation of the final DockerKernel object.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Sequence, override

from ai.backend.agent.docker.kernel import DockerKernel
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage
from ai.backend.common.types import ClusterInfo, ServicePort


@dataclass
class KernelObjectSpec:
    ownership_data: KernelOwnershipData
    kernel_config: Mapping[str, Any]
    image_ref: ImageRef
    kspec_version: int
    cluster_info: ClusterInfo
    agent_config: Mapping[str, Any]
    service_ports: Sequence[ServicePort]
    resource_spec: KernelResourceSpec
    environ: Mapping[str, str]


class KernelObjectSpecGenerator(ArgsSpecGenerator[KernelObjectSpec]):
    pass


@dataclass
class KernelObjectResult:
    kernel: DockerKernel


class KernelObjectProvisioner(Provisioner[KernelObjectSpec, KernelObjectResult]):
    """
    Provisioner for kernel object creation.

    Creates the final DockerKernel instance with all prepared configurations.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-kernel-object"

    @override
    async def setup(self, spec: KernelObjectSpec) -> KernelObjectResult:
        # Extract network configuration
        network_mode = spec.cluster_info["network_config"].get("mode", "bridge")

        # Create DockerKernel instance
        kernel = DockerKernel(
            ownership_data=spec.ownership_data,
            network_id=spec.kernel_config["network_id"],
            image=spec.image_ref,
            version=spec.kspec_version,
            network_driver=network_mode,
            agent_config=spec.agent_config,
            service_ports=spec.service_ports,
            resource_spec=spec.resource_spec,
            environ=spec.environ,
            data={},  # Additional data can be added here if needed
        )

        return KernelObjectResult(kernel=kernel)

    @override
    async def teardown(self, resource: KernelObjectResult) -> None:
        # No cleanup needed for kernel object
        pass


class KernelObjectStage(ProvisionStage[KernelObjectSpec, KernelObjectResult]):
    """
    Stage for creating the final DockerKernel object.
    """

    pass
