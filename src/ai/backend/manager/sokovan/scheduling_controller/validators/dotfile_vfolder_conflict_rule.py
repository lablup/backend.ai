"""Dotfile ↔ vfolder kernel-path collision validator.

Ports the ``DotfileVFolderPathConflict`` branch of the legacy
``prepare_dotfiles`` helper into a dedicated validator. The scheduler
repository seeds :attr:`SessionSpecContext.dotfile_data` via
its readonly batch fetch; this rule checks every resolved kernel
mount against each dotfile target.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import override

from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.storage import DotfileVFolderPathConflict
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    SessionSpecContext,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidatorRule,
)


class DotfileVFolderConflictRule(SessionSpecValidatorRule):
    """Dotfile paths must not collide with any kernel's resolved mount path."""

    @override
    def name(self) -> str:
        return "dotfile_vfolder_conflict"

    @override
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecContext,
    ) -> None:
        dotfiles = context.user.dotfiles.dotfiles
        if not dotfiles:
            return
        kernel_paths: set[PurePosixPath] = set()
        for kernel in spec.resource_spec.kernel_specs:
            for mount in kernel.vfolder_mounts:
                kernel_paths.add(mount.kernel_path)
        if not kernel_paths:
            return
        for dotfile in dotfiles:
            raw_path = dotfile.path
            if not raw_path:
                continue
            dotfile_path = PurePosixPath(raw_path)
            if not dotfile_path.is_absolute():
                dotfile_path = PurePosixPath("/home/work", raw_path)
            if dotfile_path in kernel_paths:
                raise DotfileVFolderPathConflict(
                    f"There is a kernel-side path from vfolders that conflicts with "
                    f"a dotfile '{raw_path}'.",
                )
