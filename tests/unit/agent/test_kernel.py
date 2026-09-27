import asyncio
import time
from collections.abc import Sequence
from typing import Any, cast, override

import pytest

from ai.backend.agent import kernel as kernel_mod
from ai.backend.agent.errors.agent import UnsupportedBaseDistroError
from ai.backend.agent.kernel import AbstractCodeRunner, match_distro_data
from ai.backend.common import msgpack


def test_match_distro_data() -> None:
    krunner_volumes = {
        "ubuntu8.04": "u1",
        "ubuntu18.04": "u2",
        "centos7.6": "c1",
        "centos8.0": "c2",
        "centos5.0": "c3",
    }

    ret = match_distro_data(krunner_volumes, "centos7.6")
    assert ret[0] == "centos7.6"
    assert ret[1] == "c1"

    ret = match_distro_data(krunner_volumes, "centos8.0")
    assert ret[0] == "centos8.0"
    assert ret[1] == "c2"

    ret = match_distro_data(krunner_volumes, "centos")
    assert ret[0] == "centos8.0"  # assume latest
    assert ret[1] == "c2"

    ret = match_distro_data(krunner_volumes, "ubuntu18.04")
    assert ret[0] == "ubuntu18.04"
    assert ret[1] == "u2"

    ret = match_distro_data(krunner_volumes, "ubuntu20.04")
    assert ret[0] == "ubuntu18.04"
    assert ret[1] == "u2"

    ret = match_distro_data(krunner_volumes, "ubuntu19.10")
    assert ret[0] == "ubuntu18.04"  # assume least old version
    assert ret[1] == "u2"

    ret = match_distro_data(krunner_volumes, "ubuntu4.04")
    assert ret[0] == "ubuntu8.04"  # assume oldest
    assert ret[1] == "u1"

    ret = match_distro_data(krunner_volumes, "ubuntu")
    assert ret[0] == "ubuntu18.04"  # assume latest
    assert ret[1] == "u2"

    with pytest.raises(UnsupportedBaseDistroError):
        match_distro_data(krunner_volumes, "ubnt")

    with pytest.raises(UnsupportedBaseDistroError):
        match_distro_data(krunner_volumes, "xyz")


def test_match_distro_data_with_libc_based_krunners() -> None:
    krunner_volumes = {
        "static-gnu": "x1",
        "static-musl": "x2",
    }

    # when there are static builds, it returns the distro name as-is
    # and only distinguish the libc flavor (gnu or musl).

    ret = match_distro_data(krunner_volumes, "centos7.6")
    assert ret[0] == "static-gnu"
    assert ret[1] == "x1"

    ret = match_distro_data(krunner_volumes, "centos8.0")
    assert ret[0] == "static-gnu"
    assert ret[1] == "x1"

    ret = match_distro_data(krunner_volumes, "centos")
    assert ret[0] == "static-gnu"
    assert ret[1] == "x1"

    ret = match_distro_data(krunner_volumes, "ubuntu18.04")
    assert ret[0] == "static-gnu"
    assert ret[1] == "x1"

    ret = match_distro_data(krunner_volumes, "ubuntu")
    assert ret[0] == "static-gnu"
    assert ret[1] == "x1"

    ret = match_distro_data(krunner_volumes, "alpine3.8")
    assert ret[0] == "static-musl"
    assert ret[1] == "x2"

    ret = match_distro_data(krunner_volumes, "alpine")
    assert ret[0] == "static-musl"
    assert ret[1] == "x2"

    ret = match_distro_data(krunner_volumes, "alpine3.11")
    assert ret[0] == "static-musl"
    assert ret[1] == "x2"

    # static-gnu works as a generic fallback in all unknown distributions
    ret = match_distro_data(krunner_volumes, "ubnt")
    assert ret[0] == "static-gnu"
    assert ret[1] == "x1"

    ret = match_distro_data(krunner_volumes, "xyz")
    assert ret[0] == "static-gnu"
    assert ret[1] == "x1"


def test_match_distro_data_with_libc_based_krunners_mixed() -> None:
    krunner_volumes = {
        "static-gnu": "x1",
        "alpine3.8": "c1",
        "alpine3.11": "c2",
    }

    ret = match_distro_data(krunner_volumes, "centos7.6")
    assert ret[0] == "static-gnu"
    assert ret[1] == "x1"

    ret = match_distro_data(krunner_volumes, "centos8.0")
    assert ret[0] == "static-gnu"
    assert ret[1] == "x1"

    ret = match_distro_data(krunner_volumes, "centos")
    assert ret[0] == "static-gnu"
    assert ret[1] == "x1"

    ret = match_distro_data(krunner_volumes, "ubuntu18.04")
    assert ret[0] == "static-gnu"
    assert ret[1] == "x1"

    ret = match_distro_data(krunner_volumes, "ubuntu")
    assert ret[0] == "static-gnu"
    assert ret[1] == "x1"

    ret = match_distro_data(krunner_volumes, "alpine3.8")
    assert ret[0] == "alpine3.8"
    assert ret[1] == "c1"

    ret = match_distro_data(krunner_volumes, "alpine")
    assert ret[0] == "alpine3.11"  # assume latest
    assert ret[1] == "c2"

    ret = match_distro_data(krunner_volumes, "alpine3.11")
    assert ret[0] == "alpine3.11"
    assert ret[1] == "c2"

    # static-gnu works as a generic fallback in all unknown distributions
    ret = match_distro_data(krunner_volumes, "ubnt")
    assert ret[0] == "static-gnu"
    assert ret[1] == "x1"

    ret = match_distro_data(krunner_volumes, "xyz")
    assert ret[0] == "static-gnu"
    assert ret[1] == "x1"


class _BareRunner(AbstractCodeRunner):
    """The real runner with its two abstract addresses filled in and nothing else.

    Subclassed rather than stubbed so the methods under test are the shipped ones; instances are
    built with `__new__`, because a real construction opens sockets and starts tasks and what is
    under test is a wait, not a kernel.
    """

    @override
    async def get_repl_in_addr(self) -> str:
        return "tcp://127.0.0.1:1"

    @override
    async def get_repl_out_addr(self) -> str:
        return "tcp://127.0.0.1:2"


def _runner_that_is_never_answered() -> AbstractCodeRunner:
    """A runner whose kernel never replies: the queues stay empty and the send goes nowhere."""
    runner = _BareRunner.__new__(_BareRunner)
    runner.status_queue = asyncio.Queue()
    runner.service_apps_info_queue = asyncio.Queue()

    class _Silent:
        async def send_multipart(self, parts: Sequence[bytes]) -> None:
            pass

    runner._sockets = cast(Any, _Silent())
    return runner


class TestEveryWaitOnTheKernelIsBounded:
    """`create_kernel` retries `status` then `get-apps` under ONE `stop_after_delay` budget, so an
    unbounded wait does not just stall itself -- it eats every retry the others were going to get.

    `feed_and_get_status` had no bound. A runner that is not yet serving requests (it reads its
    input socket only after every intrinsic service has spawned) held the agent for 50s, left 10s
    for `get-apps`, and turned a ten-attempt retry into exactly one. Measured on a live node: the
    kernel was destroyed with `failed-to-create` while its container sat healthy and idle.
    """

    async def test_a_status_that_is_never_answered_gives_up(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(kernel_mod, "KERNEL_REPLY_TIMEOUT_SEC", 0.05)
        runner = _runner_that_is_never_answered()
        assert await runner.feed_and_get_status() is None, (
            "an unanswered status blocks forever and consumes the whole create_kernel budget"
        )

    async def test_it_gives_up_within_the_bound(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(kernel_mod, "KERNEL_REPLY_TIMEOUT_SEC", 0.05)
        runner = _runner_that_is_never_answered()
        started = time.monotonic()
        await runner.feed_and_get_status()
        assert time.monotonic() - started < 2.0

    async def test_a_status_that_arrives_is_still_returned(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The bound must not swallow the answer it was waiting for."""
        monkeypatch.setattr(kernel_mod, "KERNEL_REPLY_TIMEOUT_SEC", 5.0)
        runner = _runner_that_is_never_answered()
        await runner.status_queue.put(msgpack.packb({"started_at": 1.0}, use_bin_type=True))
        assert await runner.feed_and_get_status() == {"started_at": 1.0}

    async def test_the_apps_wait_uses_the_same_bound(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Both waits are the same kind of thing and share one budget, so they share one bound --
        the two drifting apart is what let this happen."""
        monkeypatch.setattr(kernel_mod, "KERNEL_REPLY_TIMEOUT_SEC", 0.05)
        runner = _runner_that_is_never_answered()
        runner._is_socket_invalid = False
        result = await runner.feed_service_apps()
        assert result["status"] == "failed"
