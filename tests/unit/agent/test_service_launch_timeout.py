from __future__ import annotations

from ai.backend.agent.kernel import SERVICE_START_REPLY_TIMEOUT_SEC
from ai.backend.kernel.base import DEFAULT_SERVICE_LAUNCH_TIMEOUT_SEC


def test_the_reply_timeout_outlasts_the_kernel_runner() -> None:
    assert SERVICE_START_REPLY_TIMEOUT_SEC > DEFAULT_SERVICE_LAUNCH_TIMEOUT_SEC
