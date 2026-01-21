"""
Dotfiles stage for kernel lifecycle.

This stage handles processing and installation of dotfiles in containers.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, override

from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage

from .utils import ChownUtil, PathOwnerDeterminer


@dataclass
class DotfileInput:
    path: str
    data: str
    perm: str  # Octal permission string like "644"


@dataclass
class DirOwnPermission:
    path: str
    perm: str
    uid: Optional[int]
    gid: Optional[int]


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
    uid_override: Optional[int]
    gid_override: Optional[int]

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
        determined_uid: Optional[int] = None
        determined_gid: Optional[int] = None
        processed_dotfiles: list[DotfileProcResult] = []
        for dotfile in spec.dotfiles:
            file_path = self._resolve_dotfile_path(spec, dotfile.path)

            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file content
            self._write_dotfile(dotfile.data, file_path)

            # Set permissions and ownership
            target_paths = self._get_parent_dirs(spec.work_dir, file_path, dotfile.perm)

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

    def _resolve_dotfile_path(self, spec: DotfilesSpec, dotfile_path: str) -> Path:
        """
        Determine the file path for a dotfile based on its path and the scratch directory.
        """
        if dotfile_path.startswith("/"):
            if dotfile_path.startswith("/home/"):
                # Handle paths under /home/ by redirecting to scratch dir
                path_arr = dotfile_path.split("/")
                file_path = spec.scratch_dir / "/".join(path_arr[2:])
            else:
                # Absolute paths outside /home/
                file_path = Path(dotfile_path)
        else:
            # Relative paths go under work_dir
            file_path = spec.work_dir / dotfile_path
        return file_path

    def _write_dotfile(self, dotfile_content: str, dotfile_path: Path) -> None:
        if not dotfile_content.endswith("\n"):
            dotfile_content += "\n"
        dotfile_path.write_text(dotfile_content)

    def _get_parent_dirs(self, work_dir: Path, base_path: Path, perm: str) -> list[Path]:
        """
        Get all parent directories of a given path.
        """
        # Set permissions and ownership
        tmp = Path(base_path)
        tmp_paths: list[Path] = []

        # Set permissions on file and all parent directories up to work_dir
        while tmp != work_dir:
            tmp.chmod(int(perm, 8))
            tmp_paths.append(tmp)
            tmp = tmp.parent
        return tmp_paths

    @override
    async def teardown(self, resource: DotfilesResult) -> None:
        # Dotfiles are cleaned up with scratch directory
        pass


class DotfilesStage(ProvisionStage[DotfilesSpec, DotfilesResult]):
    """
    Stage for processing and installing dotfiles in kernel containers.
    """

    pass
