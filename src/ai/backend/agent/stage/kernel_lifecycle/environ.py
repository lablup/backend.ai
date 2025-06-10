from dataclasses import dataclass
from typing import override

from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator


@dataclass
class EnvironSpec:
    pass


class EnvironSpecGenerator(SpecGenerator[EnvironSpec]):
    @override
    async def wait_for_spec(self) -> EnvironSpec:
        """
        Waits for the spec to be ready.
        """
        # In a real implementation, this would wait for some condition to be met.
        return EnvironSpec()


@dataclass
class EnvironResult:
    pass


class EnvironProvisioner(Provisioner[EnvironSpec, EnvironResult]):
    """
    Provisioner for the kernel creation setup stage.
    This is a no-op provisioner as it does not create any resources.
    """

    @property
    @override
    def name(self) -> str:
        return "environ"

    @override
    async def setup(self, spec: EnvironSpec) -> EnvironResult:
        pass

    @override
    async def teardown(self, resource: None) -> None:
        pass


class EnvironStage(ProvisionStage[EnvironSpec, EnvironResult]):
    pass
