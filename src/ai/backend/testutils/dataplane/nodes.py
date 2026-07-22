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
import shlex
from dataclasses import dataclass
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


async def _reap(proc: asyncio.subprocess.Process) -> None:
    """Kill a child and wait for it, shielded from the cancellation that brought us here.

    `proc.wait()` on the cancellation path would itself be cancelled immediately, leaving a
    zombie and an open transport — so the wait has to be shielded.
    """
    if proc.returncode is not None:
        return
    proc.kill()
    # Awaiting inside an already-cancelling task re-raises at once; the shielded wait still runs
    # to completion in the background, which is all the reaping needs. The caller re-raises, so
    # nothing is swallowed here.
    with contextlib.suppress(asyncio.CancelledError):
        await asyncio.shield(proc.wait())


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


class SshNode:
    """A peer node reached over SSH.

    ``BatchMode=yes`` keeps a missing key a fast failure instead of a password prompt that hangs
    the suite; the harness is meant to run unattended.
    """

    _name: str
    _target: str
    _ssh_options: tuple[str, ...]
    _limit_sec: float

    def __init__(
        self,
        target: str,
        *,
        name: str | None = None,
        ssh_options: tuple[str, ...] = ("-o", "BatchMode=yes", "-o", "LogLevel=ERROR"),
        limit_sec: float = DEFAULT_COMMAND_LIMIT,
    ) -> None:
        self._name = name or target
        self._target = target
        self._ssh_options = ssh_options
        self._limit_sec = limit_sec

    @property
    def name(self) -> str:
        return self._name

    def wire_argv(self, argv: list[str]) -> list[str]:
        return ["ssh", *self._ssh_options, self._target, "--", shlex.join(argv)]

    async def run(self, argv: list[str], *, check: bool = True) -> CommandResult:
        return await _exec(
            self._name, argv, self.wire_argv(argv), check=check, limit_sec=self._limit_sec
        )


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
