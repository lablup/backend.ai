from __future__ import annotations

from typing import cast

from ai.backend.agent.containerd.profile.runc import RUNC_RUNTIME_HANDLER, RuncProfile
from ai.backend.common.types import KernelCreationConfig


def test_runc_plan_is_the_plain_runc_runtime() -> None:
    profile = RuncProfile()

    plan = profile.plan(cast(KernelCreationConfig, {}))

    assert profile.name == "runc"
    assert plan.runtime_handler == RUNC_RUNTIME_HANDLER == "io.containerd.runc.v2"
    assert plan.spec_patch == {}
    assert plan.runtime_options is None
