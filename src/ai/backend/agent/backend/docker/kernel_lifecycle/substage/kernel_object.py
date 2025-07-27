"""
Kernel object creation stage for kernel lifecycle.

This stage handles creation of the final DockerKernel object.
"""

from dataclasses import dataclass
from typing import Mapping, Sequence, override

from ai.backend.agent.data.kernel.kernel import KernelObject
from ai.backend.agent.docker.kernel import DockerCodeRunner

# TODO: Implement DockerCodeRunner
from ai.backend.agent.kernel import default_client_features
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage
from ai.backend.common.types import KernelId, ServicePort


@dataclass
class KernelObjectSpec:
    ownership_data: KernelOwnershipData
    image_ref: ImageRef

    repl_in_port: int
    repl_out_port: int

    network_id: str
    network_mode: str

    service_ports: Sequence[ServicePort]
    resource_spec: KernelResourceSpec
    environ: Mapping[str, str]

    event_producer: EventProducer


class KernelObjectSpecGenerator(ArgsSpecGenerator[KernelObjectSpec]):
    pass


@dataclass
class KernelObjectResult:
    kernel: KernelObject


class KernelObjectProvisioner(Provisioner[KernelObjectSpec, KernelObjectResult]):
    """
    Provisioner for kernel object creation.

    Creates the final DockerKernel instance with all prepared configurations.
    """

    def __init__(self) -> None:
        self._kernel_registry: dict[KernelId, KernelObject] = {}

    @property
    @override
    def name(self) -> str:
        return "docker-kernel-object"

    @override
    async def setup(self, spec: KernelObjectSpec) -> KernelObjectResult:
        code_runner = await self._init_code_runner(spec)

        # Create DockerKernel instance
        kernel = KernelObject(
            ownership_data=spec.ownership_data,
            image_ref=spec.image_ref,
            network_id=spec.network_id,
            network_mode=spec.network_mode,
            service_ports=list(spec.service_ports),
            resource_spec=spec.resource_spec,
            environ=spec.environ,
            code_runner=code_runner,
        )
        self._kernel_registry[spec.ownership_data.kernel_id] = kernel

        return KernelObjectResult(kernel=kernel)

    async def _init_code_runner(self, spec: KernelObjectSpec) -> DockerCodeRunner:
        """
        Initialize the code runner for the kernel.
        This is a placeholder for future implementation.
        """
        code_runner = DockerCodeRunner(
            spec.ownership_data.kernel_id,
            spec.ownership_data.session_id,
            spec.event_producer,
            kernel_host="127.0.0.1",  # repl ports are always bound to 127.0.0.1
            repl_in_port=spec.repl_in_port,
            repl_out_port=spec.repl_out_port,
            exec_timeout=0,
            client_features=default_client_features,
        )
        await code_runner.__ainit__()
        return code_runner

    @override
    async def teardown(self, resource: KernelObjectResult) -> None:
        code_runner = resource.kernel.code_runner
        await code_runner.close()
        self._kernel_registry.pop(resource.kernel.ownership_data.kernel_id, None)


class KernelObjectStage(ProvisionStage[KernelObjectSpec, KernelObjectResult]):
    """
    Stage for creating the final DockerKernel object.
    """

    pass
