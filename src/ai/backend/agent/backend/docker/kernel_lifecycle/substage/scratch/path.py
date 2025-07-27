from dataclasses import dataclass
from pathlib import Path
from typing import override

from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import BinarySize, KernelId

from ..utils import ScratchUtil


@dataclass
class ScratchPathSpec:
    kernel_id: KernelId

    scratch_type: str
    scratch_root: Path
    scratch_size: BinarySize


class ScratchPathSpecGenerator(ArgsSpecGenerator[ScratchPathSpec]):
    pass


@dataclass
class ScratchPathResult:
    scratch_dir: Path
    scratch_file: Path
    tmp_dir: Path
    work_dir: Path
    config_dir: Path

    scratch_type: str


class ScratchPathProvisioner(Provisioner[ScratchPathSpec, ScratchPathResult]):
    """
    Provisioner for the kernel creation setup stage.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-scratch-path"

    @override
    async def setup(self, spec: ScratchPathSpec) -> ScratchPathResult:
        return ScratchPathResult(
            scratch_dir=ScratchUtil.scratch_dir(spec.scratch_root, spec.kernel_id),
            scratch_file=ScratchUtil.scratch_file(spec.scratch_root, spec.kernel_id),
            tmp_dir=ScratchUtil.tmp_dir(spec.scratch_root, spec.kernel_id),
            work_dir=ScratchUtil.work_dir(spec.scratch_root, spec.kernel_id),
            config_dir=ScratchUtil.config_dir(spec.scratch_root, spec.kernel_id),
            scratch_type=spec.scratch_type,
        )

    @override
    async def teardown(self, resource: ScratchPathResult) -> None:
        return


class ScratchPathStage(ProvisionStage[ScratchPathSpec, ScratchPathResult]):
    pass
