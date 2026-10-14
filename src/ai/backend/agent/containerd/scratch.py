"""The per-kernel scratch directory: the config and work dirs mounted into the container."""

from __future__ import annotations

import logging
import os
import re
import shutil
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Final

import aiofiles

from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

TASK_LOG_NAME: Final = "task.log"
TRUSTED_STORE_NAME: Final = "trusted-store.img"
HOSTS_NAME: Final = "hosts"
_HOST_HOSTS_FILE: Final = Path("/etc/hosts")
_HOSTNAME_RE: Final = re.compile(r"[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?")
CONFIG_DIR_LABEL: Final = "ai.backend.containerd.config-dir"
_RUNNER_DOTFILES: Final = (".bashrc", ".bash_profile", ".zshrc", ".vimrc", ".tmux.conf")
_JUPYTER_FILES: Final = {
    "jupyter-custom.css": "custom.css",
    "logo.svg": "logo.svg",
    "roboto.ttf": "roboto.ttf",
    "roboto-italic.ttf": "roboto-italic.ttf",
}


@dataclass(frozen=True)
class ScratchDirs:
    root: Path
    config: Path
    work: Path

    @classmethod
    def for_kernel(cls, scratch_root: Path, kernel_id: str) -> ScratchDirs:
        root = (scratch_root / kernel_id).resolve()
        return cls(root=root, config=root / "config", work=root / "work")

    @property
    def hosts(self) -> Path:
        """The kernel's /etc/hosts; it is not under a mounted directory."""
        return self.root / HOSTS_NAME

    @property
    def task_log(self) -> Path:
        """Task stdio goes here; it is not mounted into the container."""
        return self.root / TASK_LOG_NAME

    @property
    def trusted_store(self) -> Path:
        """The sparse backing file of the trusted storage; it is not mounted either."""
        return self.root / TRUSTED_STORE_NAME


@dataclass(frozen=True)
class Owner:
    """The uid/gid the files in the work dir belong to; None leaves a part unchanged."""

    uid: int | None
    gid: int | None


def chown_if_root(paths: Iterable[Path], owner: Owner | None) -> None:
    if owner is None or os.geteuid() != 0:
        return
    for path in paths:
        try:
            os.chown(
                path,
                -1 if owner.uid is None else owner.uid,
                -1 if owner.gid is None else owner.gid,
            )
        except OSError:
            log.exception("chown failed", file_path=str(path))


def create_scratch(dirs: ScratchDirs, owner: Owner | None, *, clone_dotfiles: bool) -> None:
    for d in (dirs.config, dirs.work):
        d.mkdir(parents=True, exist_ok=True)
        d.chmod(0o755)
    if not clone_dotfiles:
        return
    runner = files("ai.backend.runner")
    jupyter_dir = dirs.work / ".jupyter" / "custom"
    jupyter_dir.mkdir(parents=True, exist_ok=True)
    copied = [dirs.work, dirs.work / ".jupyter", jupyter_dir]
    for src_name, dst_name in _JUPYTER_FILES.items():
        shutil.copy(Path(str(runner.joinpath(src_name))).resolve(), jupyter_dir / dst_name)
        copied.append(jupyter_dir / dst_name)
    for name in (*_RUNNER_DOTFILES, "DO_NOT_STORE_PERSISTENT_FILES_HERE.md"):
        shutil.copy(Path(str(runner.joinpath(name))).resolve(), dirs.work / name)
        copied.append(dirs.work / name)
    chown_if_root(copied, owner)


def _dotfile_target(dirs: ScratchDirs, path: str) -> Path | None:
    """Where a dotfile goes, or None when it is outside the kernel's scratch dir or a directory."""
    if path.startswith("/home/"):
        target = dirs.root / "/".join(path.split("/")[2:])
    elif path.startswith("/"):
        return None  # the Docker agent writes this on the host; here it is refused
    else:
        target = dirs.work / path
    target = target.resolve()
    if target.is_dir() or not target.is_relative_to(dirs.root):
        return None  # a directory ("." or "") cannot hold the file either
    return target


def write_dotfiles(
    dirs: ScratchDirs, dotfiles: Sequence[Mapping[str, Any]], owner: Owner | None
) -> None:
    """Write the user's dotfiles; the ones later in the list take precedence.

    A path that leaves the scratch dir or names a directory is skipped with a warning.
    """
    for dotfile in dotfiles:
        target = _dotfile_target(dirs, dotfile["path"])
        if target is None:
            log.warning(
                "dotfile outside the scratch dir or on a directory skipped",
                dotfile_path=dotfile["path"],
            )
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        content = dotfile["data"]
        target.write_text(content if content.endswith("\n") else content + "\n")
        perm = int(dotfile["perm"], 8)
        dir_perm = perm | ((perm & 0o444) >> 2)  # a directory needs x wherever it has r
        target.chmod(perm)
        touched: list[Path] = [target]
        base = dirs.work if target.is_relative_to(dirs.work) else dirs.root
        node = target.parent
        while node != base and node.is_relative_to(base):
            node.chmod(dir_perm)
            touched.append(node)
            node = node.parent
        chown_if_root(touched, owner)


def write_config_files(
    dirs: ScratchDirs,
    *,
    environ: str,
    resource: str,
    bootstrap_script: str | None,
    owner: Owner | None,
) -> None:
    (dirs.config / "environ.txt").write_text(environ)
    (dirs.config / "resource.txt").write_text(resource)
    shutil.copyfile(dirs.config / "environ.txt", dirs.config / "environ_base.txt")
    shutil.copyfile(dirs.config / "resource.txt", dirs.config / "resource_base.txt")
    if bootstrap_script:
        (dirs.work / "bootstrap.sh").write_text(bootstrap_script)
        chown_if_root([dirs.work / "bootstrap.sh"], owner)


def write_hosts_file(dirs: ScratchDirs, hostname: str) -> None:
    """The host's /etc/hosts plus the kernel's own hostname on the loopback address."""
    try:
        content = _HOST_HOSTS_FILE.read_text()
    except FileNotFoundError:
        content = ""
    if content and not content.endswith("\n"):
        content += "\n"
    if _HOSTNAME_RE.fullmatch(hostname):
        content += f"127.0.0.1 {hostname}\n"
    else:
        log.warning("kernel hostname left out of the hosts file", hostname=hostname)
    dirs.hosts.write_text(content)
    dirs.hosts.chmod(0o644)


def write_intrinsic_ports(dirs: ScratchDirs, ports: bytes) -> None:
    """The REPL ports the kernel runner binds, read from /home/config by the runner."""
    (dirs.config / "intrinsic-ports.json").write_bytes(ports)


async def read_resource_spec(labels: Mapping[str, str]) -> KernelResourceSpec | None:
    """The resource spec a running kernel was created with, from its config dir."""
    config_dir = labels.get(CONFIG_DIR_LABEL)
    if not config_dir:
        return None
    async with aiofiles.open(Path(config_dir) / "resource.txt") as f:
        return await KernelResourceSpec.aread_from_file(f)


def remove_scratch(scratch_root: Path, kernel_id: str) -> None:
    shutil.rmtree(scratch_root / kernel_id, ignore_errors=True)
