from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Final

import aiohttp
from kubernetes_asyncio import client

from ai.backend.kube.gateway.errors import KernelExecTimeoutError, KernelFileTooLargeError

_STDIN: Final = 0
_STDOUT: Final = 1
_STDERR: Final = 2
_STATUS: Final = 3
_CHUNK: Final = 64 * 1024
DEFAULT_EXEC_TIMEOUT: Final = 60.0
DEFAULT_STDERR_LIMIT: Final = 64 * 1024
_STATUS_LIMIT: Final = 64 * 1024


@dataclass(frozen=True)
class ExecResult:
    stdout: bytes
    stderr: bytes
    exit_code: int


def _exit_code(status: bytes) -> int:
    if not status:
        return 0
    body = json.loads(status)
    if body.get("status") == "Success":
        return 0
    for cause in body.get("details", {}).get("causes", []):
        if cause.get("reason") == "ExitCode":
            return int(cause["message"])
    return -1


async def exec_in_pod(
    core: client.CoreV1Api,
    namespace: str,
    pod: str,
    container: str,
    command: list[str],
    stdin: bytes | None = None,
    *,
    stdout_limit: int,
    stderr_limit: int = DEFAULT_STDERR_LIMIT,
    exec_timeout: float = DEFAULT_EXEC_TIMEOUT,
) -> ExecResult:
    """Run a command in a container over the exec websocket.

    The exec protocol has no portable end-of-stdin signal, so a command that takes stdin must
    know how many bytes to read. Output past a channel's limit, or a command running past
    `exec_timeout`, aborts the exec. `core` must use a `kubernetes_asyncio.stream.WsApiClient`.
    """
    limits = {_STDOUT: stdout_limit, _STDERR: stderr_limit, _STATUS: _STATUS_LIMIT}
    channels: dict[int, bytearray] = {ch: bytearray() for ch in limits}
    try:
        async with asyncio.timeout(exec_timeout):
            ctx = await core.connect_get_namespaced_pod_exec(
                pod,
                namespace,
                container=container,
                command=command,
                stdin=stdin is not None,
                stdout=True,
                stderr=True,
                tty=False,
                _preload_content=False,
            )
            async with ctx as ws:
                if stdin is not None:
                    for offset in range(0, len(stdin), _CHUNK):
                        await ws.send_bytes(bytes([_STDIN]) + stdin[offset : offset + _CHUNK])
                async for msg in ws:
                    if msg.type != aiohttp.WSMsgType.BINARY or not msg.data:
                        continue
                    channel = msg.data[0]
                    if channel not in channels:
                        continue
                    channels[channel].extend(msg.data[1:])
                    if len(channels[channel]) > limits[channel]:
                        raise KernelFileTooLargeError(
                            f"the output of {command[0]} exceeds {limits[channel]} bytes"
                        )
    except TimeoutError as e:
        raise KernelExecTimeoutError(f"{command[0]} did not finish in {exec_timeout} s") from e
    return ExecResult(
        stdout=bytes(channels[_STDOUT]),
        stderr=bytes(channels[_STDERR]),
        exit_code=_exit_code(bytes(channels[_STATUS])),
    )
