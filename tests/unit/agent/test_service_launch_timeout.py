from __future__ import annotations

import inspect

from ai.backend.agent.kernel import SERVICE_START_REPLY_TIMEOUT_SEC
from ai.backend.kernel.base import BaseRunner

# How long the kernel runner waits for a service port. There is no constant to import for it:
# it is the default of `_start_service(launch_timeout=...)`.
KRUNNER_LAUNCH_TIMEOUT_SEC: float = (
    inspect.signature(BaseRunner._start_service).parameters["launch_timeout"].default
)


def test_the_reply_timeout_outlasts_the_kernel_runner() -> None:
    assert SERVICE_START_REPLY_TIMEOUT_SEC > KRUNNER_LAUNCH_TIMEOUT_SEC
