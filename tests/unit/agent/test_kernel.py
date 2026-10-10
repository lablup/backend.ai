import asyncio
import time
from collections.abc import Sequence
from typing import Any, cast, override

import pytest

from ai.backend.agent import kernel as kernel_mod
from ai.backend.agent.docker.kernel import DockerKernel
from ai.backend.agent.errors.agent import UnsupportedBaseDistroError
from ai.backend.agent.errors.kernel import KernelRunnerReplyTimeoutError
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
    """The real runner with its abstract addresses filled in; built with `__new__` so that no
    sockets or tasks are created."""

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
    """`create_kernel` retries `status` then `get-apps` under one `stop_after_delay` budget, so an
    unbounded wait on either one consumes the retries of both."""

    async def test_a_status_that_is_never_answered_gives_up(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(kernel_mod, "KERNEL_REPLY_TIMEOUT_SEC", 0.05)
        runner = _runner_that_is_never_answered()
        started = time.monotonic()
        with pytest.raises(KernelRunnerReplyTimeoutError):
            await runner.feed_and_get_status()
        assert time.monotonic() - started < 2.0

    async def test_a_status_that_arrives_is_still_returned(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(kernel_mod, "KERNEL_REPLY_TIMEOUT_SEC", 5.0)
        runner = _runner_that_is_never_answered()
        await runner.status_queue.put(msgpack.packb({"started_at": 1.0}, use_bin_type=True))
        assert await runner.feed_and_get_status() == {"started_at": 1.0}

    async def test_the_apps_wait_uses_the_same_bound(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(kernel_mod, "KERNEL_REPLY_TIMEOUT_SEC", 0.05)
        runner = _runner_that_is_never_answered()
        result = await runner.feed_service_apps()
        assert result["status"] == "failed"

    async def test_ping_reports_an_unanswered_status_as_no_reply(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(kernel_mod, "KERNEL_REPLY_TIMEOUT_SEC", 0.05)
        runner = _runner_that_is_never_answered()
        runner.kernel_id = cast(Any, "k")
        assert await runner.ping() is None


class TestStatusPingSurvivesAnUnansweredStatus:
    """`ping_status` keeps the REPL ports' NAT entries alive; a runner slow to start serving
    must not stop it for good."""

    async def test_ping_status_asks_again_after_a_timeout(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(kernel_mod, "KERNEL_REPLY_TIMEOUT_SEC", 0.05)
        real_sleep = asyncio.sleep

        async def _no_wait(_delay: float) -> None:
            await real_sleep(0)

        monkeypatch.setattr(asyncio, "sleep", _no_wait)
        runner = _BareRunner.__new__(_BareRunner)
        runner.kernel_id = cast(Any, "k")
        runner.status_queue = asyncio.Queue()
        asked_again = asyncio.Event()
        sends: list[Sequence[bytes]] = []

        class _SilentCountingSocket:
            async def send_multipart(self, parts: Sequence[bytes]) -> None:
                sends.append(parts)
                if len(sends) >= 2:
                    asked_again.set()

        runner._sockets = cast(Any, _SilentCountingSocket())
        task = asyncio.create_task(runner.ping_status())
        try:
            async with asyncio.timeout(2.0):
                await asked_again.wait()  # without the fix ping_status returns after one timeout
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


class TestCreatePathKeepsNoReplyAsNone:
    """`create_kernel` ignores `check_status`'s value and goes on to the retried apps request."""

    async def test_docker_check_status_maps_a_timeout_to_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(kernel_mod, "KERNEL_REPLY_TIMEOUT_SEC", 0.05)
        kernel = DockerKernel.__new__(DockerKernel)
        kernel.runner = _runner_that_is_never_answered()
        assert await kernel.check_status() is None


class TestLateStatusRepliesNeverBlockOutput:
    """Late status replies stay in the bounded `status_queue`; once it fills, `read_output` must
    still deliver every other message type."""

    async def test_a_full_status_queue_keeps_the_newest_reply_and_reads_on(self) -> None:
        runner = _BareRunner.__new__(_BareRunner)
        runner.kernel_id = cast(Any, "k")
        runner.status_queue = asyncio.Queue(maxsize=2)
        runner.completion_queue = asyncio.Queue()
        for stale in (b"stale-1", b"stale-2"):
            runner.status_queue.put_nowait(stale)
        incoming = [[b"status", b"fresh"], [b"completion", b"done"]]
        never = asyncio.Event()

        class _ScriptedSocket:
            async def recv_multipart(self) -> list[bytes]:
                if incoming:
                    return incoming.pop(0)
                await never.wait()
                return []

        runner._sockets = cast(Any, _ScriptedSocket())
        task = asyncio.create_task(runner.read_output())
        try:
            async with asyncio.timeout(2.0):
                assert await runner.completion_queue.get() == b"done"
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        assert [runner.status_queue.get_nowait() for _ in range(2)] == [b"stale-2", b"fresh"]
