"""Command execution against the hosts under test.

A data-plane assertion is a question about one host's kernel state ("is there still a `baibr7`
device?"), and the multi-node scenarios have to ask it of every node. `Node` is the one seam that
makes a collector node-agnostic: the same collector runs against the local host and against a peer
reached over SSH.

Nodes are named, and the name travels into every `Resource` — a leak report must say *which* host
kept the device, otherwise a two-node failure is unactionable.

Commands run through `argv` lists, never a shell string, so a collector cannot accidentally depend
on the local shell's quoting. `SshNode` re-quotes the argv for the remote shell exactly once.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import shlex
import signal
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

DEFAULT_COMMAND_LIMIT = 30.0
"""Seconds a single command may take. This is a property of the *connection*, not of the call:
a collector has no idea whether it is talking to the local host or to a peer three racks away,
and a hung `ssh` is the failure this bounds."""


class CommandFailed(RuntimeError):
    """A command the harness depends on did not succeed.

    Collectors let this propagate. A collector that swallowed it would return an empty set, and an
    empty set is indistinguishable from "the host is clean" — the harness would then certify a
    leaking host as leak-free.
    """


@dataclass(frozen=True)
class CommandResult:
    node: str
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    def check(self) -> str:
        if self.returncode != 0:
            raise CommandFailed(
                f"[{self.node}] rc={self.returncode}: {shlex.join(self.argv)}\n"
                f"stdout: {self.stdout.strip()}\nstderr: {self.stderr.strip()}"
            )
        return self.stdout

    @property
    def lines(self) -> list[str]:
        return [line for line in self.stdout.splitlines() if line.strip()]


@runtime_checkable
class Node(Protocol):
    """A host the harness can run commands on."""

    @property
    def name(self) -> str: ...

    async def run(self, argv: list[str], *, check: bool = True) -> CommandResult: ...


REAP_LIMIT_SEC = 5.0
"""Seconds to wait for a killed child. A child that outlives this is left to the OS: waiting on
it without a bound is what turned one unkillable process into a run that never ended."""


async def _kill_group(proc: asyncio.subprocess.Process, *, privileged: bool) -> None:
    """SIGKILL the child's whole process group.

    The group, not the process: killing `sudo` alone leaves the command it exec'd, and killing
    `ssh` alone leaves the remote command running. `privileged` escalates through `sudo`, which
    is what a collector's root child needs -- an unprivileged signal to it is EPERM, and a group
    holding both ours and root's reports success while the root half keeps running.
    """
    if privileged:
        escalated = await asyncio.create_subprocess_exec(
            "sudo",
            "-n",
            "kill",
            "-KILL",
            "--",
            f"-{proc.pid}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        with contextlib.suppress(BaseException):
            await escalated.wait()
        return
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(proc.pid, signal.SIGKILL)


async def _wait_briefly(proc: asyncio.subprocess.Process) -> bool:
    """Wait out `REAP_LIMIT_SEC` for the child, leaving no task behind either way.

    The wait cannot simply be shielded: a shield leaves the inner wait running as its own task,
    and a child that never exits then keeps the event loop from ever closing -- the run hangs
    rather than reporting whatever brought us here.
    """
    waiter = asyncio.ensure_future(proc.wait())
    try:
        await asyncio.wait({waiter}, timeout=REAP_LIMIT_SEC)
    finally:
        if not waiter.done():
            waiter.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await waiter
    return proc.returncode is not None


def _group_alive(pgid: int) -> bool:
    """Whether any process of the group is still running.

    EPERM answers the question as well as success does -- it is a member we are not allowed to
    signal, which is exactly the case worth escalating for.
    """
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


async def _reap(proc: asyncio.subprocess.Process) -> None:
    """Kill a child's group and wait for it, bounded, whatever the cancellation state of the
    caller.

    The direct child going is not the end of it: `sudo` keeps our real uid until it execs, so a
    plain group kill takes `sudo` and leaves the root command it started -- with our waiter
    already satisfied. The group is what has to be empty.
    """
    if proc.returncode is not None and not _group_alive(proc.pid):
        return
    await _kill_group(proc, privileged=False)
    await _wait_briefly(proc)
    if not _group_alive(proc.pid):
        return
    await _kill_group(proc, privileged=True)
    await _wait_briefly(proc)


async def _exec(
    node_name: str,
    argv: list[str],
    wire_argv: list[str],
    *,
    check: bool,
    limit_sec: float,
) -> CommandResult:
    proc = await asyncio.create_subprocess_exec(
        *wire_argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        # Its own process group, so a reap can take the whole tree -- `sudo` and what it exec'd,
        # `ssh` and the remote command it is carrying.
        start_new_session=True,
    )
    try:
        async with asyncio.timeout(limit_sec):
            raw_out, raw_err = await proc.communicate()
    except TimeoutError:
        await _reap(proc)
        raise CommandFailed(
            f"[{node_name}] timed out after {limit_sec}s: {shlex.join(argv)}"
        ) from None
    except asyncio.CancelledError:
        # A snapshot gathers every collector at once, so one collector raising cancels all the
        # others mid-`communicate`. Without this the child survives its awaiter: an abandoned
        # `ssh` keeps the remote command running, and the un-reaped transport keeps the event
        # loop from shutting down — the whole run hangs instead of reporting the original error.
        await _reap(proc)
        raise
    result = CommandResult(
        node=node_name,
        argv=tuple(argv),
        returncode=proc.returncode if proc.returncode is not None else -1,
        stdout=raw_out.decode(errors="replace"),
        stderr=raw_err.decode(errors="replace"),
    )
    if check:
        result.check()
    return result


class LocalNode:
    """The host the test process itself runs on."""

    _name: str
    _limit_sec: float

    def __init__(self, name: str = "local", *, limit_sec: float = DEFAULT_COMMAND_LIMIT) -> None:
        self._name = name
        self._limit_sec = limit_sec

    @property
    def name(self) -> str:
        return self._name

    async def run(self, argv: list[str], *, check: bool = True) -> CommandResult:
        return await _exec(self._name, argv, argv, check=check, limit_sec=self._limit_sec)


SSH_TRANSPORT_RETRIES = 3
SSH_RETRY_DELAY_SEC = 1.0


#: What ssh writes when it could not carry the command, rather than the command failing. The mux
#: line is the shared connection refusing another session, which is sshd's per-connection limit.
_TRANSPORT_MARKERS = ("mux_client_request_session", "Connection closed by", "Connection timed out")


def is_transport_failure(result: CommandResult) -> bool:
    """Whether ssh itself failed to run the command, rather than the command failing.

    ssh exits 255 for its own errors and passes any other exit code through from the remote
    command, so a 255 that says nothing -- or says one of the things ssh says about its own
    transport -- is the connection, not the command. A remote command that genuinely exits 255
    reports its own reason.
    """
    if result.returncode != 255:
        return False
    if not result.stdout and not result.stderr:
        return True
    return any(marker in result.stderr for marker in _TRANSPORT_MARKERS)


def _default_ssh_options() -> tuple[str, ...]:
    """``BatchMode=yes`` keeps a missing key a fast failure instead of a password prompt that hangs
    the suite; the harness is meant to run unattended.

    The rest is connection multiplexing. A leak-guard snapshot runs every collector at once, which
    is a dozen simultaneous handshakes per node -- past sshd's default `MaxStartups`, where it
    starts refusing connections at random. Those arrived as a collector failing with no output,
    which reads like the node dropping off the network. One shared connection per node has no
    startup burst to throttle.
    """
    control = Path(tempfile.gettempdir()) / f"bai-dataplane-ssh-{os.getpid()}-%C"
    return (
        "-o",
        "BatchMode=yes",
        "-o",
        "LogLevel=ERROR",
        "-o",
        "ControlMaster=auto",
        "-o",
        f"ControlPath={control}",
        "-o",
        "ControlPersist=120s",
    )


#: Commands one node runs at a time. A leak-guard snapshot asks for a dozen at once, and sshd
#: allows ten sessions on a connection by default -- past that it refuses, and a collector that
#: was never run is indistinguishable from a node that answered "nothing here". Bounded on this
#: side so the answer does not depend on the remote's configuration.
SSH_MAX_CONCURRENCY = 6


class SshNode:
    """A peer node reached over SSH."""

    _name: str
    _target: str
    _ssh_options: tuple[str, ...]
    _limit_sec: float
    _slots: asyncio.Semaphore

    def __init__(
        self,
        target: str,
        *,
        name: str | None = None,
        ssh_options: tuple[str, ...] | None = None,
        limit_sec: float = DEFAULT_COMMAND_LIMIT,
    ) -> None:
        self._name = name or target
        self._target = target
        self._ssh_options = _default_ssh_options() if ssh_options is None else ssh_options
        self._slots = asyncio.Semaphore(SSH_MAX_CONCURRENCY)
        self._limit_sec = limit_sec

    @property
    def name(self) -> str:
        return self._name

    def wire_argv(self, argv: list[str]) -> list[str]:
        return ["ssh", *self._ssh_options, self._target, "--", shlex.join(argv)]

    async def run(self, argv: list[str], *, check: bool = True) -> CommandResult:
        async with self._slots:
            for remaining in reversed(range(SSH_TRANSPORT_RETRIES)):
                result = await _exec(
                    self._name, argv, self.wire_argv(argv), check=False, limit_sec=self._limit_sec
                )
                if not (remaining and is_transport_failure(result)):
                    if check:
                        result.check()
                    return result
                await asyncio.sleep(SSH_RETRY_DELAY_SEC)
        raise AssertionError("unreachable")


class SudoNode:
    """Wraps a node so every command runs privileged.

    The collectors need root — `iptables-save`, another user's `/proc/<pid>/fd`, the containerd
    socket — but nothing about *how* privilege is obtained belongs in a collector. ``sudo -n``
    keeps a missing sudoers entry a loud failure instead of a hidden password prompt.
    """

    _inner: Node
    _sudo_argv: tuple[str, ...]

    def __init__(self, inner: Node, *, sudo_argv: tuple[str, ...] = ("sudo", "-n")) -> None:
        self._inner = inner
        self._sudo_argv = sudo_argv

    @property
    def name(self) -> str:
        return self._inner.name

    async def run(self, argv: list[str], *, check: bool = True) -> CommandResult:
        return await self._inner.run([*self._sudo_argv, *argv], check=check)


def parse_node_spec(spec: str, *, index: int) -> Node:
    """Build a node from one entry of ``BAI_DATAPLANE_NODES``.

    Accepted forms: ``local``, ``ssh://user@host``, ``name=ssh://user@host``.
    """
    spec = spec.strip()
    if not spec:
        raise ValueError("empty node spec")
    name: str | None = None
    if "=" in spec and not spec.startswith("ssh://"):
        name, _, spec = spec.partition("=")
        name = name.strip()
        spec = spec.strip()
    if spec == "local":
        return LocalNode(name or "local")
    if spec.startswith("ssh://"):
        return SshNode(spec.removeprefix("ssh://"), name=name or f"node{index}")
    raise ValueError(f"unrecognized node spec: {spec!r} (want 'local' or 'ssh://user@host')")


def parse_node_specs(raw: str) -> list[Node]:
    return [parse_node_spec(spec, index=i) for i, spec in enumerate(raw.split(",")) if spec.strip()]
