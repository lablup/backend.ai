import asyncio
import uuid
from collections.abc import Sequence
from decimal import Decimal
from typing import Any, cast, override

import pytest

from ai.backend.agent.errors.agent import UnsupportedBaseDistroError
from ai.backend.agent.errors.kernel import KernelRunnerInvalidReplyError
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


def test_match_distro_data_with_musllinux_krunner() -> None:
    krunner_volumes = {
        "static-gnu": "x1",
        "musllinux_1_2": "m1",
    }

    assert match_distro_data(krunner_volumes, "alpine3.24") == ("musllinux_1_2", "m1")
    assert match_distro_data(krunner_volumes, "ubuntu22.04") == ("static-gnu", "x1")


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


class TestStatusReplyExtensionTypes:
    @pytest.mark.parametrize(
        "reply",
        [
            {"started_at": Decimal("1.5")},
            {"started_at": uuid.UUID(int=1)},
            {"nested": [{"started_at": Decimal("1.5")}]},
        ],
        ids=["decimal", "uuid", "nested"],
    )
    async def test_a_status_with_an_extension_type_is_rejected(self, reply: object) -> None:
        runner = _runner_that_is_never_answered()
        await runner.status_queue.put(msgpack.packb(reply))
        with pytest.raises(KernelRunnerInvalidReplyError):
            await runner.feed_and_get_status()

    async def test_ping_reports_a_rejected_status_as_no_reply(self) -> None:
        runner = _runner_that_is_never_answered()
        runner.kernel_id = cast(Any, "k")
        await runner.status_queue.put(msgpack.packb({"started_at": Decimal("1.5")}))
        assert await runner.ping() is None
