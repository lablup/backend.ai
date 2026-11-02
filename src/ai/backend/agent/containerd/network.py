"""The per-kernel network namespace: loopback only, no published port."""

from __future__ import annotations

import asyncio
import logging
import shlex
from dataclasses import dataclass
from typing import Final, Protocol

from ai.backend.agent.errors.containerd import KernelNetworkSetupFailed
from ai.backend.common.types import KernelId
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

_COMMAND_TIMEOUT_SEC: Final = 10.0
_NETNS_DIR: Final = "/run/netns"
_NETNS_PREFIX: Final = "bai-"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    async def __call__(self, *argv: str, check: bool = True) -> CommandResult: ...


async def run_command(*argv: str, check: bool = True) -> CommandResult:
    """Run a host command; a start failure, a timeout, or (with check) a non-zero exit raises."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
    except OSError as e:
        raise KernelNetworkSetupFailed(f"cannot run {shlex.join(argv)}: {e}") from e
    try:
        async with asyncio.timeout(_COMMAND_TIMEOUT_SEC):
            stdout, stderr = await proc.communicate()
    except BaseException as e:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()
        if isinstance(e, TimeoutError):
            raise KernelNetworkSetupFailed(f"timed out: {shlex.join(argv)}") from e
        raise
    result = CommandResult(
        proc.returncode if proc.returncode is not None else -1,
        stdout.decode(errors="replace"),
        stderr.decode(errors="replace"),
    )
    if check and result.returncode != 0:
        raise KernelNetworkSetupFailed(
            f"{shlex.join(argv)} exited with {result.returncode}: {result.stderr.strip()}"
        )
    return result


class KernelNetwork:
    _run: CommandRunner

    def __init__(self, *, run: CommandRunner = run_command) -> None:
        self._run = run

    def netns_path(self, kernel_id: KernelId) -> str:
        return f"{_NETNS_DIR}/{self._netns(kernel_id)}"

    def _netns(self, kernel_id: KernelId) -> str:
        return f"{_NETNS_PREFIX}{kernel_id}"

    async def setup(self, kernel_id: KernelId) -> None:
        """Create the kernel's netns with only the loopback interface up."""
        ns = self._netns(kernel_id)
        await self._run("ip", "netns", "add", ns)
        await self._run("ip", "-n", ns, "link", "set", "lo", "up")
        log.debug("kernel netns created", kernel_id=kernel_id)

    async def teardown(self, kernel_id: KernelId) -> None:
        """Remove the kernel's netns; an absent one is skipped."""
        ns = self._netns(kernel_id)
        listing = await self._run("ip", "netns", "list")
        if ns in (line.split()[0] for line in listing.stdout.splitlines() if line.strip()):
            await self._run("ip", "netns", "del", ns)
