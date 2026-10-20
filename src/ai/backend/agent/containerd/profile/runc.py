from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Final, override

from ai.backend.common.types import SlotName

from .base import (
    GeneratedMountKind,
    KernelLaunch,
    KernelRunnerReadiness,
    LaunchPlan,
    RuntimeProfile,
    StdioMode,
)

RUNC_PROFILE_NAME: Final[str] = "runc"
RUNC_RUNTIME_HANDLER: Final[str] = "io.containerd.runc.v2"


class RuncProfile(RuntimeProfile):
    """The built-in profile: a plain runc container."""

    _readiness_timeout_s: float

    def __init__(self, readiness_timeout_s: float) -> None:
        self._readiness_timeout_s = readiness_timeout_s

    @property
    @override
    def name(self) -> str:
        return RUNC_PROFILE_NAME

    @override
    def accepts(self, slots: Mapping[SlotName, Decimal]) -> bool:
        return True

    @override
    def plan(self, kernel: KernelLaunch) -> LaunchPlan:
        return LaunchPlan(
            runtime_handler=RUNC_RUNTIME_HANDLER,
            rootfs_image=kernel.config["image"]["canonical"],
            spec_patch={},
            allowed_mount_kinds=frozenset(GeneratedMountKind),
            stdio=StdioMode.LOG_FILE,
            readiness=KernelRunnerReadiness(timeout_s=self._readiness_timeout_s),
        )
