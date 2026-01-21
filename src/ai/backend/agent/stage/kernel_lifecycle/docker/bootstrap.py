"""
Bootstrap stage for kernel lifecycle.

This stage handles creation of bootstrap scripts in the container work directory.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, override

from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage

from .utils import ChownUtil, PathOwnerDeterminer


@dataclass
class AgentConfig:
    kernel_features: frozenset[str]
    kernel_uid: int
    kernel_gid: int


@dataclass
class BootstrapSpec:
    work_dir: Path
    bootstrap_script: Optional[str]

    # Override UID/GID settings
    uid_override: Optional[int]
    gid_override: Optional[int]

    agent_config: AgentConfig


class BootstrapSpecGenerator(ArgsSpecGenerator[BootstrapSpec]):
    pass


@dataclass
class BootstrapResult:
    bootstrap_path: Optional[Path]


class BootstrapProvisioner(Provisioner[BootstrapSpec, BootstrapResult]):
    """
    Provisioner for bootstrap script creation.

    Creates bootstrap.sh script in the work directory if provided in kernel config.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-bootstrap"

    @override
    async def setup(self, spec: BootstrapSpec) -> BootstrapResult:
        loop = asyncio.get_running_loop()

        bootstrap_path = await loop.run_in_executor(None, self._write_bootstrap_script, spec)
        return BootstrapResult(bootstrap_path=bootstrap_path)

    def _write_bootstrap_script(self, spec: BootstrapSpec) -> Optional[Path]:
        if not spec.bootstrap_script:
            return None

        bootstrap_path = spec.work_dir / "bootstrap.sh"
        bootstrap_path.write_text(spec.bootstrap_script)

        # Set proper ownership
        owner_determiner = PathOwnerDeterminer.by_kernel_features(
            spec.agent_config.kernel_uid,
            spec.agent_config.kernel_gid,
            spec.agent_config.kernel_features,
        )
        final_uid, final_gid = owner_determiner.determine(
            bootstrap_path, uid_override=spec.uid_override, gid_override=spec.gid_override
        )
        ChownUtil().chown_path(bootstrap_path, final_uid, final_gid)
        return bootstrap_path

    @override
    async def teardown(self, resource: BootstrapResult) -> None:
        # Bootstrap script is cleaned up with scratch directory
        pass


class BootstrapStage(ProvisionStage[BootstrapSpec, BootstrapResult]):
    """
    Stage for creating bootstrap scripts in kernel containers.
    """

    pass
