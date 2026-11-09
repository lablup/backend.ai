from __future__ import annotations

from typing import Final, override

from ai.backend.agent.containerd.profile.base import LaunchPlan, RuntimeProfile
from ai.backend.common.types import KernelCreationConfig

RUNC_PROFILE_NAME: Final = "runc"
RUNC_RUNTIME_HANDLER: Final = "io.containerd.runc.v2"


class RuncProfile(RuntimeProfile):
    """The built-in profile: a plain runc container."""

    @property
    @override
    def name(self) -> str:
        return RUNC_PROFILE_NAME

    @override
    def plan(self, kernel_config: KernelCreationConfig) -> LaunchPlan:
        return LaunchPlan(runtime_handler=RUNC_RUNTIME_HANDLER)
