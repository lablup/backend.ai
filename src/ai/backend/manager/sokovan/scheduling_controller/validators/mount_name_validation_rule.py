"""Per-kernel mount name / alias validator."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.vfolder import verify_vfolder_name
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidationContext,
    SessionSpecValidatorRule,
)


class MountNameValidationRule(SessionSpecValidatorRule):
    """Each kernel's mount ``kernel_path`` must be unique within that kernel,
    non-empty, and non-reserved.

    Iterates per-kernel ``KernelSpec.vfolder_mounts`` — duplicates are
    scoped per kernel since two kernels can legitimately mount the same
    vfolder at the same path.
    """

    @override
    def name(self) -> str:
        return "mount_name_validation"

    @override
    def validate(
        self,
        spec: SessionSpec,
        _context: SessionSpecValidationContext,
    ) -> None:
        for kernel_idx, kernel in enumerate(spec.kernel_specs):
            seen_paths: set[str] = set()
            for mount_idx, mount in enumerate(kernel.vfolder_mounts):
                path = str(mount.kernel_path)
                path_tail = path.removeprefix("/home/work/")
                if path_tail == "":
                    raise InvalidAPIParameters(
                        extra_msg=(
                            f"kernel_specs[{kernel_idx}].vfolder_mounts[{mount_idx}] "
                            "has an empty alias."
                        ),
                    )
                if not verify_vfolder_name(path_tail):
                    raise InvalidAPIParameters(
                        extra_msg=(
                            f"kernel_specs[{kernel_idx}].vfolder_mounts[{mount_idx}] "
                            f"alias '{path_tail}' is reserved for internal paths."
                        ),
                    )
                if path in seen_paths:
                    raise InvalidAPIParameters(
                        extra_msg=(
                            f"kernel_specs[{kernel_idx}].vfolder_mounts has duplicate "
                            f"kernel_path '{path}'."
                        ),
                    )
                seen_paths.add(path)
