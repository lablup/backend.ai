from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

# TODO: Implement DockerCodeRunner
from ai.backend.agent.docker.kernel import DockerCodeRunner
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import ServicePort


@dataclass
class KernelObject:
    """
    Represents a Docker kernel object with its configuration and ownership data.
    This is used to create and manage Docker containers for kernels.
    """

    ownership_data: KernelOwnershipData

    image_ref: ImageRef

    resource_spec: KernelResourceSpec
    environ: Mapping[str, str]

    network_id: str
    network_mode: str

    service_ports: list[ServicePort]

    code_runner: DockerCodeRunner

    async def check_status(self) -> Optional[dict[str, float]]:
        result = await self.code_runner.feed_and_get_status()
        return result

    async def get_service_apps(self) -> dict[str, Any]:
        result = await self.code_runner.feed_service_apps()
        return result
