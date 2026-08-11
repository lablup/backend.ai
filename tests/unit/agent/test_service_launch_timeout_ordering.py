from __future__ import annotations

import inspect

from ai.backend.agent.kernel import SERVICE_START_REPLY_TIMEOUT_SEC
from ai.backend.kernel.base import BaseRunner


def test_agent_outlasts_the_kernel_runner() -> None:
    """The two budgets sit in packages that cannot import each other, so only a test can
    hold them in order: the runner ships inside the container, and an agent that gives up
    first reports a timeout the runner never declared."""
    launch_timeout = inspect.signature(BaseRunner._start_service).parameters["launch_timeout"]

    assert SERVICE_START_REPLY_TIMEOUT_SEC > launch_timeout.default
