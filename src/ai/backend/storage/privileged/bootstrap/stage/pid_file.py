import os
from dataclasses import dataclass
from pathlib import Path
from typing import override

from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)


@dataclass
class PIDFileSpec:
    file_path: Path


class PIDFileSpecGenerator(ArgsSpecGenerator[PIDFileSpec]):
    pass


@dataclass
class PIDFileResult:
    file_path: Path


class PIDFileProvisioner(Provisioner[PIDFileSpec, PIDFileResult]):
    @property
    @override
    def name(self) -> str:
        return "storage-worker-pid-file"

    @override
    async def setup(self, spec: PIDFileSpec) -> PIDFileResult:
        path = spec.file_path
        path.write_text(str(os.getpid()))
        return PIDFileResult(path)

    @override
    async def teardown(self, resource: PIDFileResult) -> None:
        path = resource.file_path
        if path.is_file():
            # check is_file() to prevent deleting /dev/null!
            path.unlink()


class PIDFileStage(ProvisionStage[PIDFileSpec, PIDFileResult]):
    pass
