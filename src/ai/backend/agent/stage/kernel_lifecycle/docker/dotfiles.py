"""
Dotfiles stage for kernel lifecycle.

This stage handles processing and installation of dotfiles in containers.
"""

<<<<<<< HEAD
import asyncio
=======
import logging
>>>>>>> 249726371 (fix(BA-8786): keep dotfile paths under the kernel work directory (#16231))
from dataclasses import dataclass
from pathlib import Path
from typing import override

<<<<<<< HEAD
=======
from ai.backend.agent.dotfile import DotfileTargetResolver
from ai.backend.common.asyncio import run_in_executor_with_context
from ai.backend.common.dotfile import InvalidDotfilePath
>>>>>>> 249726371 (fix(BA-8786): keep dotfile paths under the kernel work directory (#16231))
from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage
from ai.backend.logging.structured import StructuredLogger

from .utils import ChownUtil, PathOwnerDeterminer

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass
class DotfileInput:
    path: str
    data: str
    perm: str  # Octal permission string like "644"


@dataclass
class DirOwnPermission:
    path: str
    perm: str
    uid: int | None
    gid: int | None


@dataclass
class DotfileProcResult:
    path: str
    data: str
    dir_own_permissions: list[DirOwnPermission]


@dataclass
class AgentConfig:
    kernel_features: frozenset[str]
    kernel_uid: int
    kernel_gid: int


@dataclass
class DotfilesSpec:
    dotfiles: list[DotfileInput]
    scratch_dir: Path
    work_dir: Path

    # Override UID/GID settings
    uid_override: int | None
    gid_override: int | None

    agent_config: AgentConfig


class DotfilesSpecGenerator(ArgsSpecGenerator[DotfilesSpec]):
    pass


@dataclass
class DotfilesResult:
    processed_dotfiles: list[DotfileProcResult]


class DotfilesProvisioner(Provisioner[DotfilesSpec, DotfilesResult]):
    """
    Provisioner for dotfiles processing.

    Processes and installs dotfiles from internal_data into the container filesystem.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-dotfiles"

    @override
    async def setup(self, spec: DotfilesSpec) -> DotfilesResult:
        loop = asyncio.get_running_loop()

        result = await loop.run_in_executor(None, self._process_dotfiles, spec)
        return DotfilesResult(processed_dotfiles=result)

    def _process_dotfiles(self, spec: DotfilesSpec) -> list[DotfileProcResult]:
        if not spec.dotfiles:
            return []
        chown = ChownUtil()
        owner_determiner = PathOwnerDeterminer.by_kernel_features(
            spec.agent_config.kernel_uid,
            spec.agent_config.kernel_gid,
            spec.agent_config.kernel_features,
        )
        determined_uid: int | None = None
        determined_gid: int | None = None
        processed_dotfiles: list[DotfileProcResult] = []
        targets = DotfileTargetResolver(spec.work_dir)
        for dotfile in spec.dotfiles:
            try:
                file_path = targets.resolve(dotfile.path)
            except InvalidDotfilePath:
                log.warning("dotfile skipped by the path rule", path=dotfile.path)
                continue

            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file content
            self._write_dotfile(dotfile.data, file_path)

            # Set permissions and ownership
            target_paths = targets.paths_below_work_dir(file_path)
            for target_path in target_paths:
                target_path.chmod(int(dotfile.perm, 8))

            uid, gid = owner_determiner.determine(
                file_path, uid_override=spec.uid_override, gid_override=spec.gid_override
            )
            chown.chown_paths(target_paths, uid, gid)
            if determined_uid is None:
                determined_uid = uid
            if determined_gid is None:
                determined_gid = gid

            processed_dotfiles.append(
                DotfileProcResult(
                    path=str(file_path),
                    data=dotfile.data,
                    dir_own_permissions=[
                        DirOwnPermission(
                            path=str(p),
                            perm=dotfile.perm,
                            uid=determined_uid,
                            gid=determined_gid,
                        )
                        for p in target_paths
                    ],
                )
            )

        return processed_dotfiles

    def _write_dotfile(self, dotfile_content: str, dotfile_path: Path) -> None:
        if not dotfile_content.endswith("\n"):
            dotfile_content += "\n"
        dotfile_path.write_text(dotfile_content)

    @override
    async def teardown(self, resource: DotfilesResult) -> None:
        # Dotfiles are cleaned up with scratch directory
        pass


class DotfilesStage(ProvisionStage[DotfilesSpec, DotfilesResult]):
    """
    Stage for processing and installing dotfiles in kernel containers.
    """

    pass
