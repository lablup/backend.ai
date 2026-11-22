from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Coroutine
from typing import Any, cast

import aiohttp
import pytest
from kubernetes_asyncio import client

from ai.backend.kube.gateway.errors import KernelExecTimeoutError, KernelFileTooLargeError
from ai.backend.kube.gateway.pod_exec import ExecResult, _exit_code, exec_in_pod


class TestExitCode:
    @pytest.mark.parametrize(
        ("status", "code"),
        [
            (b"", 0),
            (b'{"status":"Success"}', 0),
            (
                (
                    b'{"status":"Failure","reason":"NonZeroExitCode",'
                    b'"details":{"causes":[{"reason":"ExitCode","message":"3"}]}}'
                ),
                3,
            ),
            (b'{"status":"Failure","message":"container not found"}', -1),
        ],
        ids=["no-status", "success", "non-zero", "exec-failed"],
    )
    def test_parses_status_channel(self, status: bytes, code: int) -> None:
        assert _exit_code(status) == code


class _Message:
    type: aiohttp.WSMsgType
    data: bytes

    def __init__(self, data: bytes) -> None:
        self.type = aiohttp.WSMsgType.BINARY
        self.data = data


class _Socket:
    _messages: list[bytes]
    _delay: float

    def __init__(self, messages: list[bytes], delay: float) -> None:
        self._messages = messages
        self._delay = delay

    async def __aenter__(self) -> _Socket:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        return None

    async def send_bytes(self, data: bytes) -> None:
        return None

    def __aiter__(self) -> AsyncIterator[_Message]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[_Message]:
        for data in self._messages:
            await asyncio.sleep(self._delay)
            yield _Message(data)


class _Core:
    _socket: _Socket

    def __init__(self, messages: list[bytes], delay: float = 0.0) -> None:
        self._socket = _Socket(messages, delay)

    async def connect_get_namespaced_pod_exec(self, *args: Any, **kwargs: Any) -> _Socket:
        return self._socket


def _run(core: _Core, **kwargs: Any) -> Coroutine[Any, Any, ExecResult]:
    return exec_in_pod(cast(client.CoreV1Api, core), "ns", "p", "kernel", ["python"], **kwargs)


class TestExecInPod:
    async def test_collects_the_channels(self) -> None:
        result = await _run(_Core([b"\x01out", b"\x02err"]), stdout_limit=10)
        assert (result.stdout, result.stderr, result.exit_code) == (b"out", b"err", 0)

    async def test_output_past_the_limit_aborts(self) -> None:
        with pytest.raises(KernelFileTooLargeError):
            await _run(_Core([b"\x01" + b"x" * 11]), stdout_limit=10)

    async def test_a_slow_command_times_out(self) -> None:
        with pytest.raises(KernelExecTimeoutError):
            await _run(_Core([b"\x01out"], delay=1.0), stdout_limit=10, exec_timeout=0.01)
