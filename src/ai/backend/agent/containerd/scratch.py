"""The per-kernel scratch directory: the config and work dirs mounted into the container."""

from __future__ import annotations

import logging
import os
import shutil
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Final

from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

TASK_LOG_NAME: Final = "task.log"
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
    def task_log(self) -> Path:
        """Task stdio goes here; it is not mounted into the container."""
        return self.root / TASK_LOG_NAME


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


def write_dotfiles(
    dirs: ScratchDirs, dotfiles: Sequence[Mapping[str, Any]], owner: Owner | None
) -> None:
    """Write the user's dotfiles; the ones later in the list take precedence."""
    for dotfile in dotfiles:
        path = dotfile["path"]
        if path.startswith("/home/"):
            target = dirs.root / "/".join(path.split("/")[2:])
        elif path.startswith("/"):
            target = Path(path)
        else:
            target = dirs.work / path
        target.parent.mkdir(parents=True, exist_ok=True)
        content = dotfile["data"]
        target.write_text(content if content.endswith("\n") else content + "\n")
        perm = int(dotfile["perm"], 8)
        dir_perm = perm | ((perm & 0o444) >> 2)  # a directory needs x wherever it has r
        target.chmod(perm)
        touched: list[Path] = [target]
        node = target.parent
        while node != dirs.work and node != node.parent:
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


def write_intrinsic_ports(dirs: ScratchDirs, ports: bytes) -> None:
    """The REPL ports the kernel runner binds, read from /home/config by the runner."""
    (dirs.config / "intrinsic-ports.json").write_bytes(ports)


def remove_scratch(scratch_root: Path, kernel_id: str) -> None:
    shutil.rmtree(scratch_root / kernel_id, ignore_errors=True)
