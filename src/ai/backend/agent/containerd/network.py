"""The per-kernel network: a netns and a veth on the agent's bridge."""

from __future__ import annotations

import asyncio
import logging
import shlex
import uuid
from collections.abc import Collection
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network
from typing import Final, Protocol

from ai.backend.agent.errors.containerd import (
    KernelAddressExhausted,
    KernelBridgeInvalid,
    KernelNetworkSetupFailed,
)
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import KernelId
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

_COMMAND_TIMEOUT_SEC: Final = 10.0
_KERNEL_IFNAME: Final = "eth0"
_NETNS_DIR: Final = "/run/netns"


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
    _bridge: str
    _subnet: IPv4Network
    _gateway: IPv4Address
    _addresses: dict[KernelId, IPv4Address]
    _run: CommandRunner

    def __init__(
        self, bridge: str, subnet: IPv4Network, *, run: CommandRunner = run_command
    ) -> None:
        self._bridge = bridge
        self._subnet = subnet
        self._gateway = subnet[1]
        self._addresses = {}
        self._run = run

    def netns_path(self, kernel_id: KernelId) -> str:
        return f"{_NETNS_DIR}/{self._netns(kernel_id)}"

    def _netns(self, kernel_id: KernelId) -> str:
        return f"{self._bridge}-{kernel_id}"

    def _veth(self, kernel_id: KernelId) -> str:
        return f"bai{kernel_id.hex[:12]}"

    async def init(self) -> None:
        """Create the bridge with the gateway address; safe to repeat."""
        br = self._bridge
        shown = await self._run("ip", "-d", "link", "show", "dev", br, check=False)
        if shown.returncode != 0:
            await self._run("ip", "link", "add", br, "type", "bridge")
        elif not any(line.split()[:1] == ["bridge"] for line in shown.stdout.splitlines()):
            raise KernelBridgeInvalid(f"{br} exists but is not a bridge")
        await self._run(
            "ip", "addr", "replace", f"{self._gateway}/{self._subnet.prefixlen}", "dev", br
        )
        await self._run("ip", "link", "set", br, "up")
        log.info("kernel bridge ready", bridge_name=br, subnet=str(self._subnet))

    def restore(self, kernel_id: KernelId, address: IPv4Address) -> None:
        self._addresses[kernel_id] = address

    def _allocate(self, kernel_id: KernelId) -> IPv4Address:
        used = set(self._addresses.values())
        for host in self._subnet.hosts():
            if host != self._gateway and host not in used:
                self._addresses[kernel_id] = host
                return host
        raise KernelAddressExhausted(f"no free address in {self._subnet}")

    async def setup(self, kernel_id: KernelId) -> IPv4Address:
        """Create the netns and veth and give them an address and the default route."""
        address = self._allocate(kernel_id)
        ns, veth = self._netns(kernel_id), self._veth(kernel_id)
        await self._run("ip", "netns", "add", ns)
        await self._run(
            "ip", "link", "add", veth, "type", "veth", "peer", "name", _KERNEL_IFNAME, "netns", ns
        )
        await self._run("ip", "link", "set", veth, "master", self._bridge)
        await self._run("ip", "link", "set", "dev", veth, "type", "bridge_slave", "isolated", "on")
        await self._run("ip", "link", "set", veth, "up")
        addr = f"{address}/{self._subnet.prefixlen}"
        await self._run("ip", "-n", ns, "addr", "add", addr, "dev", _KERNEL_IFNAME)
        await self._run("ip", "-n", ns, "link", "set", _KERNEL_IFNAME, "up")
        await self._run("ip", "-n", ns, "link", "set", "lo", "up")
        await self._run("ip", "-n", ns, "route", "add", "default", "via", str(self._gateway))
        log.debug("kernel network set up", kernel_id=kernel_id, address=str(address))
        return address

    async def _netns_names(self) -> list[str]:
        listing = await self._run("ip", "netns", "list")
        return [line.split()[0] for line in listing.stdout.splitlines() if line.strip()]

    async def teardown(self, kernel_id: KernelId) -> None:
        """Remove the kernel's veth and netns; every step tolerates absence."""
        veth = self._veth(kernel_id)
        if (await self._run("ip", "link", "show", "dev", veth, check=False)).returncode == 0:
            await self._run("ip", "link", "del", veth)
        ns = self._netns(kernel_id)
        if ns in await self._netns_names():
            await self._run("ip", "netns", "del", ns)
        self._addresses.pop(kernel_id, None)

    async def sweep(self, alive: Collection[KernelId]) -> None:
        """Tear down the netns of this bridge whose kernel is not alive."""
        prefix = f"{self._bridge}-"
        stale: set[KernelId] = set()
        for name in await self._netns_names():
            if name.startswith(prefix) and (kid := _as_kernel_id(name.removeprefix(prefix))):
                stale.add(kid)
        removed = 0
        for kernel_id in sorted(stale - set(alive), key=str):
            try:
                await self.teardown(kernel_id)
            except BackendAIError:
                log.exception("stale kernel network teardown failed", kernel_id=kernel_id)
            else:
                removed += 1
        if removed:
            log.info("stale kernel networks removed", kernel_count=removed)


def _as_kernel_id(text: str) -> KernelId | None:
    try:
        return KernelId(uuid.UUID(text))
    except ValueError:
        return None
