from dataclasses import dataclass
from typing import override

from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator


@dataclass
class ResourceSpec:
    pass


class ResourceSpecGenerator(SpecGenerator[ResourceSpec]):
    @override
    async def wait_for_spec(self) -> ResourceSpec:
        """
        Waits for the spec to be ready.
        """
        # In a real implementation, this would wait for some condition to be met.
        return ResourceSpec()


@dataclass
class ResourceResult:
    pass


class ResourceProvisioner(Provisioner[ResourceSpec, ResourceResult]):
    """
    Provisioner for the kernel creation setup stage.
    This is a no-op provisioner as it does not create any resources.
    """

    @property
    @override
    def name(self) -> str:
        return "resource"

    @override
    async def setup(self, spec: ResourceSpec) -> ResourceResult:
        pass

    @override
    async def teardown(self, resource: None) -> None:
        pass


class ResourceStage(ProvisionStage[ResourceSpec, ResourceResult]):
    pass
