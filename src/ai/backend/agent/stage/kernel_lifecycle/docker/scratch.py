import asyncio
import functools
import os
import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, override

import pkg_resources

from ai.backend.common.docker import KernelFeatures
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import BinarySize, KernelId

from .utils import ScratchUtil


@dataclass
class ContainerOwnershipConfig:
    kernel_uid: Optional[int]
    kernel_gid: Optional[int]
    supplementary_gids: set[int]

    fallback_kernel_uid: int
    fallback_kernel_gid: int

    kernel_features: frozenset[str]


@dataclass
class ScratchSpec:
    kernel_id: KernelId

    container_config: ContainerOwnershipConfig

    scratch_type: str
    scratch_root: Path
    scratch_size: BinarySize


class ScratchSpecGenerator(ArgsSpecGenerator[ScratchSpec]):
    pass


@dataclass
class ScratchResult:
    scratch_dir: Path
    scratch_file: Path
    tmp_dir: Path
    work_dir: Path
    config_dir: Path

    scratch_type: str


class ScratchProvisioner(Provisioner[ScratchSpec, ScratchResult]):
    """
    Provisioner for the kernel creation setup stage.
    This is a no-op provisioner as it does not create any resources.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-scratch"

    @override
    async def setup(self, spec: ScratchSpec) -> ScratchResult:
        await self._create_filesystem(spec)
        await self._create_scratch_dirs(spec)
        await self._clone_dotfiles(spec)
        return ScratchResult(
            scratch_dir=ScratchUtil.scratch_dir(spec.scratch_root, spec.kernel_id),
            scratch_file=ScratchUtil.scratch_file(spec.scratch_root, spec.kernel_id),
            tmp_dir=ScratchUtil.tmp_dir(spec.scratch_root, spec.kernel_id),
            work_dir=ScratchUtil.work_dir(spec.scratch_root, spec.kernel_id),
            config_dir=ScratchUtil.config_dir(spec.scratch_root, spec.kernel_id),
            scratch_type=spec.scratch_type,
        )

    async def _create_filesystem(self, spec: ScratchSpec) -> None:
        loop = asyncio.get_running_loop()
        tmp_dir = ScratchUtil.tmp_dir(spec.scratch_root, spec.kernel_id)
        scratch_dir = ScratchUtil.scratch_dir(spec.scratch_root, spec.kernel_id)
        if sys.platform.startswith("linux") and spec.scratch_type == "memory":
            await loop.run_in_executor(None, functools.partial(tmp_dir.mkdir, exist_ok=True))
            await self._create_scratch_filesystem(scratch_dir, 64)
            await self._create_scratch_filesystem(tmp_dir, 64)
        elif sys.platform.startswith("linux") and spec.scratch_type == "hostfile":
            await self._create_loop_filesystem(spec.scratch_root, spec.scratch_size, spec.kernel_id)
        else:
            await loop.run_in_executor(None, functools.partial(scratch_dir.mkdir, exist_ok=True))

    async def _create_scratch_filesystem(self, scratch_dir: Path, size: int) -> None:
        """
        Create scratch folder size quota by using tmpfs filesystem.

        :param scratch_dir: The path of scratch directory.

        :param size: The quota size of scratch directory.
                    Size parameter is must be MiB(mebibyte).
        """

        proc = await asyncio.create_subprocess_exec(*[
            "mount",
            "-t",
            "tmpfs",
            "-o",
            f"size={size}M",
            "tmpfs",
            f"{scratch_dir}",
        ])
        exit_code = await proc.wait()

        if exit_code < 0:
            raise CalledProcessError(
                exit_code,
                proc.args,  # type: ignore[attr-defined]
                output=proc.stdout,  # type: ignore[arg-type]
                stderr=proc.stderr,  # type: ignore[arg-type]
            )

    def _create_sparse_file(self, name: str, size: int) -> None:
        fd = os.open(name, os.O_CREAT, 0o644)
        os.close(fd)
        os.truncate(name, size)
        # Check that no space was allocated
        stat = os.stat(name)
        if stat.st_blocks != 0:
            raise RuntimeError("could not create sparse file")

    async def _create_loop_filesystem(
        self, scratch_root: Path, scratch_size: int, kernel_id: KernelId
    ) -> None:
        loop = asyncio.get_running_loop()
        scratch_dir = ScratchUtil.scratch_dir(scratch_root, kernel_id)
        scratch_file = ScratchUtil.scratch_file(scratch_root, kernel_id)
        await loop.run_in_executor(
            None, functools.partial(os.makedirs, str(scratch_dir), exist_ok=True)
        )
        await loop.run_in_executor(None, self._create_sparse_file, str(scratch_file), scratch_size)
        mkfs = await asyncio.create_subprocess_exec(
            "/sbin/mkfs.ext4",
            str(scratch_file),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        exit_code = await mkfs.wait()
        if exit_code != 0:
            raise RuntimeError("mkfs failed")
        mount = await asyncio.create_subprocess_exec("mount", str(scratch_file), str(scratch_dir))
        exit_code = await mount.wait()
        if exit_code != 0:
            raise RuntimeError("mount failed")

    async def _create_scratch_dirs(self, spec: ScratchSpec) -> None:
        work_dir = ScratchUtil.work_dir(spec.scratch_root, spec.kernel_id)
        config_dir = ScratchUtil.config_dir(spec.scratch_root, spec.kernel_id)

        def create() -> None:
            config_dir.mkdir(parents=True, exist_ok=True)
            config_dir.chmod(0o755)
            work_dir.mkdir(parents=True, exist_ok=True)
            work_dir.chmod(0o755)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, create)

    async def _clone_dotfiles(self, spec: ScratchSpec) -> None:
        # Since these files are bind-mounted inside a bind-mounted directory,
        # we need to touch them first to avoid their "ghost" files are created
        # as root in the host-side filesystem, which prevents deletion of scratch
        # directories when the agent is running as non-root.

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._clone_func, spec)

    def _clone_func(self, spec: ScratchSpec) -> None:
        work_dir = ScratchUtil.work_dir(spec.scratch_root, spec.kernel_id)
        jupyter_custom_css_path = Path(
            pkg_resources.resource_filename("ai.backend.runner", "jupyter-custom.css")
        )
        logo_path = Path(pkg_resources.resource_filename("ai.backend.runner", "logo.svg"))
        font_path = Path(pkg_resources.resource_filename("ai.backend.runner", "roboto.ttf"))
        font_italic_path = Path(
            pkg_resources.resource_filename("ai.backend.runner", "roboto-italic.ttf")
        )
        bashrc_path = Path(pkg_resources.resource_filename("ai.backend.runner", ".bashrc"))
        bash_profile_path = Path(
            pkg_resources.resource_filename("ai.backend.runner", ".bash_profile")
        )
        zshrc_path = Path(pkg_resources.resource_filename("ai.backend.runner", ".zshrc"))
        vimrc_path = Path(pkg_resources.resource_filename("ai.backend.runner", ".vimrc"))
        tmux_conf_path = Path(pkg_resources.resource_filename("ai.backend.runner", ".tmux.conf"))
        jupyter_custom_dir = work_dir / ".jupyter" / "custom"
        jupyter_custom_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(jupyter_custom_css_path.resolve(), jupyter_custom_dir / "custom.css")
        shutil.copy(logo_path.resolve(), jupyter_custom_dir / "logo.svg")
        shutil.copy(font_path.resolve(), jupyter_custom_dir / "roboto.ttf")
        shutil.copy(font_italic_path.resolve(), jupyter_custom_dir / "roboto-italic.ttf")
        shutil.copy(bashrc_path.resolve(), work_dir / ".bashrc")
        shutil.copy(bash_profile_path.resolve(), work_dir / ".bash_profile")
        shutil.copy(zshrc_path.resolve(), work_dir / ".zshrc")
        shutil.copy(vimrc_path.resolve(), work_dir / ".vimrc")
        shutil.copy(tmux_conf_path.resolve(), work_dir / ".tmux.conf")

        paths = [
            work_dir,
            work_dir / ".jupyter",
            work_dir / ".jupyter" / "custom",
            work_dir / ".bashrc",
            work_dir / ".bash_profile",
            work_dir / ".zshrc",
            work_dir / ".vimrc",
            work_dir / ".tmux.conf",
        ]
        self._chown_paths_if_root(paths, spec.container_config)

    def _chown_paths_if_root(
        self,
        paths: Iterable[Path],
        config: ContainerOwnershipConfig,
    ) -> None:
        valid_uid: Optional[int]
        valid_gid: Optional[int]
        if os.geteuid() == 0:  # only possible when I am root.
            if KernelFeatures.UID_MATCH in config.kernel_features:
                valid_uid = (
                    config.kernel_uid
                    if config.kernel_uid is not None
                    else config.fallback_kernel_uid
                )
                valid_gid = (
                    config.kernel_gid
                    if config.kernel_gid is not None
                    else config.fallback_kernel_gid
                )
            else:
                valid_uid = config.kernel_uid
                valid_gid = config.kernel_gid
            for p in paths:
                if valid_uid is None or valid_gid is None:
                    stat = os.stat(p)
                    valid_uid = stat.st_uid if valid_uid is None else valid_uid
                    valid_gid = stat.st_gid if valid_gid is None else valid_gid
                os.chown(p, valid_uid, valid_gid)

    @override
    async def teardown(self, resource: ScratchResult) -> None:
        loop = asyncio.get_running_loop()
        scratch_dir = resource.scratch_dir
        tmp_dir = resource.tmp_dir
        try:
            if sys.platform.startswith("linux") and resource.scratch_type == "memory":
                await self._destroy_scratch_filesystem(scratch_dir)
                await self._destroy_scratch_filesystem(tmp_dir)
                await loop.run_in_executor(None, shutil.rmtree, scratch_dir)
                await loop.run_in_executor(None, shutil.rmtree, tmp_dir)
            elif sys.platform.startswith("linux") and resource.scratch_type == "hostfile":
                await self._destroy_loop_filesystem(resource)
            else:
                await loop.run_in_executor(None, shutil.rmtree, scratch_dir)
        except CalledProcessError:
            pass
        except FileNotFoundError:
            pass

    async def _destroy_scratch_filesystem(self, scratch_dir: Path) -> None:
        """
        Destroy scratch folder size quota by using tmpfs filesystem.

        :param scratch_dir: The path of scratch directory.
        """
        proc = await asyncio.create_subprocess_exec(*[
            "umount",
            f"{scratch_dir}",
        ])
        exit_code = await proc.wait()

        if exit_code < 0:
            raise CalledProcessError(
                exit_code,
                proc.args,  # type: ignore[attr-defined]
                output=proc.stdout,  # type: ignore[arg-type]
                stderr=proc.stderr,  # type: ignore[arg-type]
            )

    async def _destroy_loop_filesystem(self, resource: ScratchResult) -> None:
        loop = asyncio.get_running_loop()
        scratch_dir = resource.scratch_dir
        scratch_file = resource.scratch_file
        umount = await asyncio.create_subprocess_exec("umount", str(scratch_dir))
        exit_code = await umount.wait()
        if exit_code != 0:
            raise RuntimeError("umount failed")
        await loop.run_in_executor(None, os.remove, str(scratch_file))
        await loop.run_in_executor(None, shutil.rmtree, str(scratch_dir))


class ScratchStage(ProvisionStage[ScratchSpec, ScratchResult]):
    pass
