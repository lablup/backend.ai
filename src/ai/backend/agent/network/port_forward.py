"""Host-port ingress for container services (BEP-1058).

The LOCAL bridge is a node-local NAT subnet: the container's address is private and reused on
every node, exactly as ``docker0``'s is. Egress works because the attach runner installs a
MASQUERADE rule; this module is the missing other half — the DNAT that lets anything off the node
reach a container's service port.

Without it a kernel's ``kernel_host`` has to be its private address, and the manager hands that to
an AppProxy which may run on any host in the cluster and has no route to it. With it,
``kernel_host`` is the agent's advertised address and each service is published on a host port,
which is how the Docker backend has always worked (dockerd installs the same rules for
``PortBindings``).

The rules carry an ``-m comment --comment bai:<container_id>`` tag, so **iptables itself is the
record**: teardown finds a container's rules by tag, and an agent restart can enumerate the
published ports without any journal of its own. Same principle as the veth name being a pure
function of the container id.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol

from ai.backend.agent.errors.network import PortForwardError

_COMMENT_PREFIX = "bai:"


@dataclass(frozen=True)
class PortForward:
    container_id: str
    host_port: int
    container_ip: str
    container_port: int


def _comment(container_id: str) -> list[str]:
    return ["-m", "comment", "--comment", f"{_COMMENT_PREFIX}{container_id}"]


def dnat_rule(chain: str, forward: PortForward) -> list[str]:
    """The DNAT rule body, shared by -A (install), -D (remove) and -C (probe).

    ``--dst-type LOCAL`` is not optional. Without it the rule matches on the port alone, and this
    node both forwards overlay traffic for other nodes and originates its own connections — so a
    packet merely *transiting* the host, or an outbound connection to some remote host's port
    30001, would be redirected into a local container. Docker's published-port rules carry the
    same guard for the same reason.
    """
    return [
        chain,
        "-p", "tcp",
        "-m", "addrtype", "--dst-type", "LOCAL",
        "--dport", str(forward.host_port),
        *_comment(forward.container_id),
        "-j", "DNAT",
        "--to-destination", f"{forward.container_ip}:{forward.container_port}",
    ]  # fmt: skip


def chains() -> tuple[str, ...]:
    """PREROUTING catches traffic arriving on a NIC; OUTPUT catches the agent's own connections
    to its advertised address, which never traverse PREROUTING."""
    return ("PREROUTING", "OUTPUT")


def install_args(forward: PortForward) -> list[list[str]]:
    return [["iptables", "-t", "nat", "-A", *dnat_rule(c, forward)] for c in chains()]


def remove_args(forward: PortForward) -> list[list[str]]:
    return [["iptables", "-t", "nat", "-D", *dnat_rule(c, forward)] for c in chains()]


def list_args() -> list[str]:
    return ["iptables", "-t", "nat", "-S", "PREROUTING"]


def _parse_line(line: str) -> PortForward | None:
    """Parse one ``iptables -S`` rule line into a PortForward, or None if it is not one of ours.

    Token-based (not a positional regex) so a future reordering of the match modules — iptables
    is free to emit ``-m addrtype``/``-m tcp``/``-m comment`` in any order — cannot silently
    change what parses. Our comment is ``bai:<id>`` with no spaces, so whitespace tokenizing keeps
    it intact.
    """
    toks = line.split()

    def value_after(flag: str) -> str | None:
        try:
            return toks[toks.index(flag) + 1]
        except (ValueError, IndexError):
            return None

    comment = value_after("--comment")
    if comment is None or not comment.strip('"').startswith(_COMMENT_PREFIX):
        return None
    dport = value_after("--dport")
    dest = value_after("--to-destination")
    if dport is None or dest is None:
        return None
    ip, _, container_port = dest.rpartition(":")
    if not (ip and container_port.isdigit() and dport.isdigit()):
        return None
    return PortForward(
        container_id=comment.strip('"')[len(_COMMENT_PREFIX) :],
        host_port=int(dport),
        container_ip=ip,
        container_port=int(container_port),
    )


def parse_forwards(
    iptables_save_output: str, *, container_id: str | None = None
) -> list[PortForward]:
    """Recover the published ports from the rules themselves.

    With ``container_id`` set, only that container's forwards are returned (teardown); without it,
    every forward this agent ever installed (restart, to reclaim the host ports).
    """
    forwards: list[PortForward] = []
    for line in iptables_save_output.splitlines():
        forward = _parse_line(line)
        if forward is None:
            continue
        if container_id is not None and forward.container_id != container_id:
            continue
        forwards.append(forward)
    return forwards


def forwards_for(
    container_id: str, container_ip: str, ports: Iterable[tuple[int, int]]
) -> list[PortForward]:
    """``ports`` is the (host_port, container_port) pairing the agent allocated."""
    return [
        PortForward(
            container_id=container_id,
            host_port=host_port,
            container_ip=container_ip,
            container_port=container_port,
        )
        for host_port, container_port in ports
    ]


def host_ports_of(forwards: Sequence[PortForward]) -> list[int]:
    return sorted({f.host_port for f in forwards})


class PortPublisher(Protocol):
    """What the agent needs of whoever owns iptables — itself, or the privileged helper."""

    async def install(self, forwards: Sequence[PortForward]) -> None: ...

    async def remove_container(self, container_id: str) -> list[int]: ...

    async def list_forwards(self, *, container_id: str | None = None) -> list[PortForward]: ...


# runner(argv, *, check) -> (rc, stdout, stderr); injected so the builders above stay pure/testable
Runner = Callable[..., Awaitable[tuple[int, bytes, bytes]]]


async def _run_iptables(argv: Sequence[str], *, check: bool = True) -> tuple[int, bytes, bytes]:
    proc = await asyncio.create_subprocess_exec(
        *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    rc = proc.returncode or 0
    if check and rc != 0:
        raise PortForwardError(
            f"command failed (rc={rc}): {' '.join(argv)}: {err.decode(errors='replace').strip()}"
        )
    return rc, out, err


class PortForwarder:
    """Applies / removes / recovers the DNAT rules that publish a container's service ports."""

    _run: Runner

    def __init__(self, runner: Runner | None = None) -> None:
        self._run = runner or _run_iptables

    async def install(self, forwards: Sequence[PortForward]) -> None:
        """Publish each port. Atomic: a partial install is rolled back before re-raising, so a
        failed start never leaves a rule pointing at a container that will not exist."""
        applied: list[PortForward] = []
        try:
            for forward in forwards:
                # Record before applying: install_args writes two chains (PREROUTING, OUTPUT), so a
                # failure on the second leaves the first behind. remove() is idempotent (check=False),
                # so covering a forward whose rules are only partially applied is safe.
                applied.append(forward)
                for argv in install_args(forward):
                    await self._run(argv)
        except Exception:
            with contextlib.suppress(Exception):
                await self.remove(applied)
            raise

    async def remove(self, forwards: Sequence[PortForward]) -> None:
        for forward in forwards:
            for argv in remove_args(forward):
                await self._run(argv, check=False)  # idempotent: a missing rule is not an error

    async def list_forwards(self, *, container_id: str | None = None) -> list[PortForward]:
        _rc, out, _err = await self._run(list_args(), check=False)
        return parse_forwards(out.decode(errors="replace"), container_id=container_id)

    async def remove_container(self, container_id: str) -> list[int]:
        """Drop every rule tagged with this container and return the host ports it held."""
        forwards = await self.list_forwards(container_id=container_id)
        await self.remove(forwards)
        return host_ports_of(forwards)
