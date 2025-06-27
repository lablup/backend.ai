from dataclasses import dataclass
from pathlib import Path
from typing import override

from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator
from ai.backend.common.types import BinarySize


@dataclass
class ScratchSpec:
    scrath_type: str
    scrath_root: Path
    scrath_size: BinarySize


class ScratchSpecGenerator(SpecGenerator[ScratchSpec]):
    @override
    async def wait_for_spec(self) -> ScratchSpec:
        """
        Waits for the spec to be ready.
        """
        # In a real implementation, this would wait for some condition to be met.
        return ScratchSpec()


@dataclass
class ScratchResult:
    pass


class ScratchProvisioner(Provisioner[ScratchSpec, ScratchResult]):
    """
    Provisioner for the kernel creation setup stage.
    This is a no-op provisioner as it does not create any resources.
    """

    @property
    @override
    def name(self) -> str:
        return "scratch"

    @override
    async def setup(self, spec: ScratchSpec) -> ScratchResult:
        pass

    @override
    async def teardown(self, resource: None) -> None:
        pass


class ScratchStage(ProvisionStage[ScratchSpec, ScratchResult]):
    pass
