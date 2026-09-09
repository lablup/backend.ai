"""Host-port ingress for container services (BEP-1078).

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

import contextlib
import time
from collections.abc import Awaitable, Callable, Container, Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol

from ai.backend.agent.errors.network import PortForwardError
from ai.backend.agent.network import command

_COMMENT_PREFIX = "bai:"


@dataclass(frozen=True)
class PortForward:
    container_id: str
    host_port: int
    container_ip: str
    container_port: int
    # The host address the service is published on. None, "" and "0.0.0.0" all mean "every local
    # address" (the LOCAL addrtype match). A concrete address confines the DNAT to that interface —
    # 127.0.0.1 for a protected service (a storage node's ttyd shell must not be remotely reachable),
    # or the operator's configured bind-host to keep service ports off the public interface. Docker
    # applies exactly the same per-port host-IP binding.
    host_ip: str | None = None
    # Transport of the published port: ``"tcp"`` (default — http/tcp/vnc/rdp service ports all ride
    # TCP) or ``"udp"``. It is part of the rule's identity: iptables ``--dport`` needs a matching
    # ``-p``, and a ``-D`` must name the same protocol as the ``-A`` or the removal misses.
    protocol: str = "tcp"
    # Which agent installed the rule. A node can carry several at once -- a docker agent and a
    # containerd one, or two of either -- and each publishes ports for containers only its own
    # runtime can see. So "the container is not in my runtime's listing" says nothing about
    # somebody else's rule, and a reclaim that acted on it would cut a live kernel of another
    # runtime off from its published ports. Owning it by name is what keeps each agent to its own.
    # None for a rule written before this was recorded; those are nobody's to reclaim by owner.
    owner_agent_id: str | None = None
    # When the rule was installed, as whole unix seconds, carried in the comment beside the container
    # id. It is what lets a reclaim wait before it acts: "this container is not in Docker" is not
    # by itself a safe reason to delete a rule, because a rule is installed a moment before its
    # container becomes visible and a sweep landing in that window would cut a starting kernel off
    # from its own ports. With the age, only a rule that has been orphaned longer than any such
    # window is taken. None for a rule written by an agent that predates this, which is old by
    # definition -- it belongs to a process that is no longer running.
    created_at: int | None = None


# Host addresses that mean "bind to every local interface" rather than one specific address. Docker
# treats an empty HostIp and "0.0.0.0" identically (bind to all), so we must too — and 0.0.0.0 is
# what the config's ``prod`` example sets bind-host to. A literal ``-d 0.0.0.0/32`` would match no
# inbound packet at all (0.0.0.0 is never a real packet destination), silently making the published
# port unreachable; the wildcard must become the ``--dst-type LOCAL`` match instead.
_WILDCARD_HOST_IPS = frozenset({"0.0.0.0"})


def _binds_every_local_address(host_ip: str | None) -> bool:
    return not host_ip or host_ip in _WILDCARD_HOST_IPS


def _comment(container_id: str, owner_agent_id: str | None, created_at: int | None) -> list[str]:
    """The ownership tag: whose rule this is, for what, and when it was made.

    ``bai:<agent_id>:<container_id>:<unix seconds>``, with the older ``bai:<container_id>`` and
    ``bai:<container_id>:<seconds>`` forms still read back so nothing written by a previous agent
    becomes unremovable.

    Three facts because a reclaim needs all three. The container id says what the rule is for; the
    agent id says whose runtime can answer whether that container still exists -- a node may run a
    docker agent beside a containerd one, and neither can see the other's containers; and the time
    says whether it has been orphaned long enough to act on, since a rule exists for a moment
    before its container does.

    Well inside iptables' 256-character comment limit.
    """
    parts = [container_id]
    if owner_agent_id is not None:
        parts.insert(0, owner_agent_id)
    if created_at is not None:
        parts.append(str(created_at))
    return ["-m", "comment", "--comment", _COMMENT_PREFIX + ":".join(parts)]


def dnat_rule(chain: str, forward: PortForward) -> list[str]:
    """The DNAT rule body, shared by -A (install), -D (remove) and -C (probe).

    A concrete ``host_ip`` binds the rule to one address with ``-d``; a wildcard (None, "" or
    "0.0.0.0" — see ``_binds_every_local_address``) uses ``--dst-type LOCAL`` to match every local
    address. That guard is not optional in the wildcard case: without it the rule matches on the
    port alone, and this node both forwards overlay traffic for other nodes and originates its own
    connections — so a packet merely *transiting* the host, or an outbound connection to some remote
    host's port 30001, would be redirected into a local container. Docker's published-port rules
    carry the same guard for the same reason.
    """
    dst_match = (
        ["-m", "addrtype", "--dst-type", "LOCAL"]
        if _binds_every_local_address(forward.host_ip)
        else ["-d", f"{forward.host_ip}/32"]
    )
    return [
        chain,
        "-p", forward.protocol,
        *dst_match,
        "--dport", str(forward.host_port),
        *_comment(forward.container_id, forward.owner_agent_id, forward.created_at),
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
    # ``-d <ip>/32`` when the rule was bound to one interface; absent for the every-address
    # (``--dst-type LOCAL``) form. Read it back so the removal rule this parses into matches the
    # installed one byte for byte — a ``-D`` that omitted the ``-d`` would fail to delete a bound
    # rule and leak it.
    host_ip: str | None = None
    if raw_d := value_after("-d"):
        host_ip = raw_d.split("/", 1)[0]
    # Read the protocol back so the parsed rule regenerates byte-for-byte (a -D that named the wrong
    # protocol would fail to delete a udp rule and leak it). iptables -S always shows -p for a
    # --dport rule; default to tcp defensively.
    protocol = value_after("-p") or "tcp"
    tag = comment.strip('"')[len(_COMMENT_PREFIX) :]
    # ``<agent>:<container>:<seconds>``, and the two older forms it grew from: ``<container>`` and
    # ``<container>:<seconds>``. Neither an agent id nor a container id contains a colon, so the
    # split is unambiguous, and an all-digit tail is the timestamp. Anything unrecognised parses as
    # "no owner, no time", which leaves the rule reclaimable rather than immortal -- the failure
    # this whole tag exists to prevent.
    parts = tag.split(":")
    created_at: int | None = None
    if len(parts) > 1 and parts[-1].isdigit():
        created_at = int(parts.pop())
    owner_agent_id: str | None = parts[0] if len(parts) == 2 else None
    container_id = parts[-1]
    return PortForward(
        container_id=container_id,
        owner_agent_id=owner_agent_id,
        host_port=int(dport),
        container_ip=ip,
        container_port=int(container_port),
        host_ip=host_ip,
        protocol=protocol,
        created_at=created_at,
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
    container_id: str,
    container_ip: str,
    ports: Iterable[tuple[int, int, str | None, str]],
    *,
    owner_agent_id: str | None = None,
) -> list[PortForward]:
    """``ports`` is the (host_port, container_port, host_ip, protocol) pairing the agent allocated.
    ``host_ip`` is the address the service is published on (None = every local address); ``protocol``
    is ``"tcp"``/``"udp"``.

    Every rule is stamped with the moment it was built, so a later sweep can tell a rule that has
    just been installed from one whose container has been gone for a while. One timestamp for the
    whole batch: they are installed together and are one container's, so giving them separate times
    would only add a second of skew for a reader to reason about.
    """
    # Whole seconds, so the value written into the comment is exactly the value read back:
    # a rule's `-D` is regenerated from what was parsed, and a timestamp that did not round
    # trip would leave a rule nothing could remove -- the very leak this exists against.
    created_at = int(time.time())
    return [
        PortForward(
            container_id=container_id,
            host_port=host_port,
            container_ip=container_ip,
            container_port=container_port,
            host_ip=host_ip,
            protocol=protocol,
            owner_agent_id=owner_agent_id,
            created_at=created_at,
        )
        for host_port, container_port, host_ip, protocol in ports
    ]


#: How long a rule whose container Docker no longer has is left alone before it is reclaimed.
#:
#: Not zero, because the two facts are read at different moments: a rule is installed just before
#: its container becomes visible, and a sweep landing in that window would cut a starting kernel
#: off from its own published ports. Not long either -- while the rule stands, its host port is a
#: black hole for whatever is published on it next, which is how a node ends up unable to start
#: any session on the low end of its port range.
ORPHAN_GRACE_SEC: float = 60.0


def is_orphaned(
    forward: PortForward,
    live_container_ids: Container[str],
    *,
    now: float,
    owner_agent_id: str,
) -> bool:
    """Whether this rule is ours, belongs to nothing, and has for long enough to be sure.

    Ownership first, and it is the part that matters on a shared node. ``live_container_ids`` can
    only be the listing of ONE runtime, so a rule another agent installed for a container that
    runtime cannot see would look orphaned to every caller. Reclaiming it would take a live
    kernel's published ports away — so a rule is only ever reclaimed by the agent that wrote it.

    A rule with no owner recorded predates this and is left alone: nobody can prove it is dead, and
    leaking it costs a port while deleting it could cost a running session.

    A rule with no timestamp was written by an agent that predates the stamp; its process is gone,
    so it is old by definition.
    """
    if forward.owner_agent_id != owner_agent_id:
        return False
    if forward.container_id in live_container_ids:
        return False
    if forward.created_at is None:
        return True
    return now - forward.created_at >= ORPHAN_GRACE_SEC


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
    try:
        rc, out, err = await command.run(argv)
    except command.CommandTimeout as e:
        # An xtables lock somebody else is holding. These run under the privnet's node-wide
        # barrier, so one that never returns stops every session operation on the node.
        raise PortForwardError(f"{e}: {' '.join(argv)}") from e
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
