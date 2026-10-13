"""The per-kernel network: a netns, a veth on the agent's bridge, DNAT for the service ports."""

from __future__ import annotations

import asyncio
import logging
import shlex
import uuid
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network
from typing import Final, Protocol

from ai.backend.agent.errors.containerd import KernelAddressExhausted, KernelNetworkSetupFailed
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import KernelId
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

_COMMAND_TIMEOUT_SEC: Final = 10.0
_COMMENT_PREFIX: Final = "bai-kernel="
_KERNEL_IFNAME: Final = "eth0"
_NETNS_DIR: Final = "/run/netns"
_METADATA_ADDRESS: Final = "169.254.169.254/32"


@dataclass(frozen=True)
class PortForward:
    host_port: int
    kernel_port: int


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
    _bind_address: str | None
    _port_range: tuple[int, int]
    _addresses: dict[KernelId, IPv4Address]
    _run: CommandRunner

    def __init__(
        self,
        bridge: str,
        subnet: IPv4Network,
        bind_host: str,
        port_range: tuple[int, int],
        *,
        run: CommandRunner = run_command,
    ) -> None:
        self._bridge = bridge
        self._subnet = subnet
        self._gateway = subnet[1]
        self._bind_address = bind_host if bind_host not in ("", "0.0.0.0") else None
        self._port_range = port_range
        self._addresses = {}
        self._run = run

    @property
    def published_host(self) -> str:
        """The local address whose DNAT rules reach a kernel.

        OUTPUT DNAT matches any local non-loopback destination when no bind host is set.
        """
        return self._bind_address or str(self._gateway)

    def netns_path(self, kernel_id: KernelId) -> str:
        return f"{_NETNS_DIR}/{self._netns(kernel_id)}"

    def _netns(self, kernel_id: KernelId) -> str:
        return f"{self._bridge}-{kernel_id}"

    def _veth(self, kernel_id: KernelId) -> str:
        return f"bai{kernel_id.hex[:12]}"

    def _chain(self, kind: str) -> str:
        return f"{self._bridge}-{kind}"

    def _prefix(self) -> str:
        return f"{self._gateway}/{self._subnet.prefixlen}"

    async def _iptables(self, table: str | None, *args: str, check: bool = True) -> CommandResult:
        scope = ("-t", table) if table else ()
        return await self._run("iptables", "-w", *scope, *args, check=check)

    async def init(self) -> None:
        """Create the bridge, forwarding and egress rules; safe to repeat."""
        br = self._bridge
        if (await self._run("ip", "link", "show", "dev", br, check=False)).returncode != 0:
            await self._run("ip", "link", "add", br, "type", "bridge")
        await self._run("ip", "addr", "replace", self._prefix(), "dev", br)
        await self._run("ip", "link", "set", br, "up")
        forwarding = await self._run("sysctl", "-n", "net.ipv4.ip_forward")
        if forwarding.stdout.strip() == "0":
            raise KernelNetworkSetupFailed("net.ipv4.ip_forward is 0; enable it before the agent")
        dnat, post = self._chain("DNAT"), self._chain("POSTROUTING")
        fwd, inp = self._chain("FORWARD"), self._chain("INPUT")
        for table, chain in (("nat", dnat), ("nat", post), (None, fwd), (None, inp)):
            if (await self._iptables(table, "-S", chain, check=False)).returncode != 0:
                await self._iptables(table, "-N", chain)
        ports = f"{self._port_range[0]}:{self._port_range[1]}"
        local = ("-p", "tcp", "--dport", ports, "-m", "addrtype", "--dst-type", "LOCAL")
        hooks: Sequence[tuple[str | None, str, tuple[str, ...]]] = (
            ("nat", "PREROUTING", (*local, "-j", dnat)),
            ("nat", "OUTPUT", ("!", "-d", "127.0.0.0/8", *local, "-j", dnat)),
            ("nat", "POSTROUTING", ("-s", str(self._subnet), "-j", post)),
            (None, "FORWARD", ("-i", br, "-j", fwd)),
            (None, "FORWARD", ("-o", br, "-j", fwd)),
            (None, "INPUT", ("-i", br, "-j", inp)),
        )
        ours = {dnat, post, fwd, inp}
        wanted: dict[tuple[str | None, str], list[tuple[str, ...]]] = {}
        for table, hook, rule in hooks:
            wanted.setdefault((table, hook), []).append(rule)
        for (table, hook), group in wanted.items():
            await self._delete_stale_jumps(table, hook, ours, group)
            for rule in group:
                if (await self._iptables(table, "-C", hook, *rule, check=False)).returncode != 0:
                    await self._iptables(table, "-I", hook, "1", *rule)
        subnet = str(self._subnet)
        statics: Sequence[tuple[str | None, str, Sequence[Sequence[str]]]] = (
            (
                "nat",
                post,
                (("-s", subnet, "!", "-o", br, "-j", "MASQUERADE"),),
            ),
            (
                None,
                fwd,
                (
                    ("-i", br, "-d", _METADATA_ADDRESS, "-j", "REJECT"),
                    (
                        "-o",
                        br,
                        "-m",
                        "conntrack",
                        "--ctstate",
                        "RELATED,ESTABLISHED",
                        "-j",
                        "ACCEPT",
                    ),
                    ("-o", br, "-m", "conntrack", "--ctstate", "DNAT", "-j", "ACCEPT"),
                    ("-i", br, "!", "-o", br, "-j", "ACCEPT"),
                    ("-o", br, "-j", "DROP"),
                ),
            ),
            (None, inp, (("-i", br, "-d", _METADATA_ADDRESS, "-j", "REJECT"),)),
        )
        for table, chain, rules in statics:
            await self._iptables(table, "-F", chain)
            for static in rules:
                await self._iptables(table, "-A", chain, *static)
        log.info("kernel bridge ready", bridge_name=br, subnet=subnet)

    async def _delete_stale_jumps(
        self, table: str | None, hook: str, ours: Collection[str], wanted: Sequence[Sequence[str]]
    ) -> None:
        """Delete jumps to our chains in `hook` that match none of `wanted` (older subnet or port-range)."""
        listing = await self._iptables(table, "-S", hook, check=False)
        if listing.returncode != 0:
            return
        for line in listing.stdout.splitlines():
            tokens = shlex.split(line)
            if len(tokens) < 4 or tokens[:2] != ["-A", hook]:
                continue
            if tokens[-2] != "-j" or tokens[-1] not in ours:
                continue
            if _without_implicit_tcp(tokens[2:]) not in [list(rule) for rule in wanted]:
                await self._iptables(table, "-D", hook, *tokens[2:])

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
        ns, veth, br = self._netns(kernel_id), self._veth(kernel_id), self._bridge
        await self._run("ip", "netns", "add", ns)
        await self._run(
            "ip", "link", "add", veth, "type", "veth", "peer", "name", _KERNEL_IFNAME, "netns", ns
        )
        await self._run("ip", "link", "set", veth, "master", br)
        await self._run("ip", "link", "set", "dev", veth, "type", "bridge_slave", "isolated", "on")
        await self._run("ip", "link", "set", veth, "up")
        await self._run(
            "ip",
            "-n",
            ns,
            "addr",
            "add",
            f"{address}/{self._subnet.prefixlen}",
            "dev",
            _KERNEL_IFNAME,
        )
        await self._run("ip", "-n", ns, "link", "set", _KERNEL_IFNAME, "up")
        await self._run("ip", "-n", ns, "link", "set", "lo", "up")
        await self._run("ip", "-n", ns, "route", "add", "default", "via", str(self._gateway))
        log.debug("kernel network set up", kernel_id=kernel_id, address=str(address))
        return address

    async def publish(self, kernel_id: KernelId, forwards: Sequence[PortForward]) -> None:
        """Add one DNAT rule per forward, tagged with the kernel id."""
        address = self._addresses.get(kernel_id)
        if address is None:
            raise KernelNetworkSetupFailed(f"no address for kernel {kernel_id}: setup did not run")
        match = ("-d", f"{self._bind_address}/32") if self._bind_address else ()
        for fw in forwards:
            await self._iptables(
                "nat",
                "-A",
                self._chain("DNAT"),
                "-p",
                "tcp",
                *match,
                "--dport",
                str(fw.host_port),
                "-m",
                "comment",
                "--comment",
                f"{_COMMENT_PREFIX}{kernel_id}",
                "-j",
                "DNAT",
                "--to-destination",
                f"{address}:{fw.kernel_port}",
            )

    async def _dnat_rules(self) -> list[tuple[str, list[str]]]:
        """The `-S` lines of the DNAT chain as (kernel id text, tokens)."""
        listing = await self._iptables("nat", "-S", self._chain("DNAT"), check=False)
        if listing.returncode != 0:
            return []
        rules: list[tuple[str, list[str]]] = []
        for line in listing.stdout.splitlines():
            tokens = shlex.split(line)
            if "--comment" not in tokens:
                continue
            idx = tokens.index("--comment") + 1
            if idx < len(tokens) and tokens[idx].startswith(_COMMENT_PREFIX):
                rules.append((tokens[idx].removeprefix(_COMMENT_PREFIX), tokens))
        return rules

    async def _netns_names(self) -> list[str]:
        listing = await self._run("ip", "netns", "list")
        return [line.split()[0] for line in listing.stdout.splitlines() if line.strip()]

    async def teardown(self, kernel_id: KernelId) -> None:
        """Remove the kernel's DNAT rules, veth and netns; every step tolerates absence."""
        for rule_kid, tokens in await self._dnat_rules():
            if rule_kid == str(kernel_id) and tokens[0] == "-A":
                await self._iptables("nat", "-D", *tokens[1:])
        veth = self._veth(kernel_id)
        if (await self._run("ip", "link", "show", "dev", veth, check=False)).returncode == 0:
            await self._run("ip", "link", "del", veth)
        ns = self._netns(kernel_id)
        if ns in await self._netns_names():
            await self._run("ip", "netns", "del", ns)
        self._addresses.pop(kernel_id, None)

    async def sweep(self, alive: Collection[KernelId]) -> None:
        """Tear down the netns and DNAT rules of this bridge whose kernel is not alive."""
        found: set[KernelId] = set()
        prefix = f"{self._bridge}-"
        for name in await self._netns_names():
            if name.startswith(prefix):
                if (kid := _as_kernel_id(name.removeprefix(prefix))) is not None:
                    found.add(kid)
        for rule_kid, _ in await self._dnat_rules():
            if (kid := _as_kernel_id(rule_kid)) is not None:
                found.add(kid)
        removed = 0
        for kernel_id in sorted(found - set(alive), key=str):
            try:
                await self.teardown(kernel_id)
            except BackendAIError:
                log.exception("stale kernel network teardown failed", kernel_id=kernel_id)
            else:
                removed += 1
        if removed:
            log.info("stale kernel networks removed", kernel_count=removed)
        else:
            log.debug("no stale kernel network")


def _as_kernel_id(text: str) -> KernelId | None:
    try:
        return KernelId(uuid.UUID(text))
    except ValueError:
        return None


def _without_implicit_tcp(tokens: Sequence[str]) -> list[str]:
    """Drop the `-m tcp` pair that `iptables -S` adds after `-p tcp --dport`."""
    out: list[str] = []
    skip = 0
    for i, token in enumerate(tokens):
        if skip:
            skip -= 1
        elif token == "-m" and tokens[i + 1 : i + 2] == ["tcp"]:
            skip = 1
        else:
            out.append(token)
    return out
