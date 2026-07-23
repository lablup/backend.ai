"""Stopping and starting the agent under test.

The restart scenarios are the reason this suite exists — every destructive defect this backend has
shipped landed on the recovery path — but *how* an agent is restarted is a fact about the
deployment, not about the agent. Production runs it under systemd; the dev stack runs it in the
foreground inside tmux; CI might run it under supervisord. Guessing wrong does not fail loudly, it
kills the developer's agent and never brings it back.

So the commands come from configuration and nothing is inferred. With them unset the restart
fixtures skip, exactly like the node fixtures do without ``BAI_DATAPLANE_NODES``.

Readiness is judged by the agent's RPC port accepting connections, not by the process existing: a
process that is up but has not finished `recover()` would let a scenario snapshot a half-rebuilt
data plane and call the difference a leak.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from ai.backend.testutils.dataplane.nodes import CommandFailed, Node


class AgentNotReady(RuntimeError):
    """The agent did not come back within the bound."""


@dataclass(frozen=True)
class AgentControlConfig:
    """How to stop and start the agent on one node.

    `stop_cmd` is optional: with it unset the controller signals the matched process directly,
    which is what a foreground dev agent needs. `start_cmd` has no fallback — nothing can restart
    a foreground process on the developer's behalf, and pretending otherwise would leave their
    stack down.
    """

    start_cmd: tuple[str, ...] | None = None
    stop_cmd: tuple[str, ...] | None = None
    process_pattern: str = "ai.backend.agent"
    rpc_port: int = 6011
    ready_timeout: float = 120.0
    stop_timeout: float = 60.0
    poll_interval: float = 1.0

    @property
    def configured(self) -> bool:
        return self.start_cmd is not None


class AgentController:
    _node: Node
    _config: AgentControlConfig

    def __init__(self, node: Node, config: AgentControlConfig) -> None:
        self._node = node
        self._config = config

    @property
    def node_name(self) -> str:
        return self._node.name

    async def pid(self) -> int | None:
        """The agent's PID, or None when it is not running.

        Rows naming `pgrep` are dropped for the same reason the gauge collector drops them: the
        shell running the query matches the pattern, and counting it would make the agent look
        alive for as long as the query itself lives.
        """
        result = await self._node.run(
            ["sh", "-c", f"pgrep -f {self._config.process_pattern!r} || true"], check=False
        )
        for line in result.lines:
            candidate = line.strip()
            if not candidate.isdigit():
                continue
            cmdline = await self._node.run(
                ["sh", "-c", f'tr "\\0" " " < /proc/{candidate}/cmdline 2>/dev/null || true'],
                check=False,
            )
            if "pgrep" in cmdline.stdout:
                continue
            return int(candidate)
        return None

    async def is_ready(self) -> bool:
        """Whether the RPC port is accepting, i.e. the agent finished coming up."""
        result = await self._node.run(
            ["sh", "-c", f"ss -ltn 'sport = :{self._config.rpc_port}' | tail -n +2"],
            check=False,
        )
        return bool(result.lines)

    async def wait_ready(self, *, expect: bool = True) -> None:
        """Poll the RPC port until it matches `expect`.

        Used both ways: after a start, to know recovery finished; after a stop, to know the port
        is actually gone before starting a replacement that would fail to bind.
        """
        deadline = time.monotonic() + (
            self._config.ready_timeout if expect else self._config.stop_timeout
        )
        while True:
            if await self.is_ready() == expect:
                return
            if time.monotonic() >= deadline:
                state = "come up" if expect else "release its RPC port"
                raise AgentNotReady(
                    f"[{self._node.name}] agent did not {state} within the bound "
                    f"(port {self._config.rpc_port})"
                )
            await asyncio.sleep(self._config.poll_interval)

    async def stop(self, *, graceful: bool = True) -> None:
        if self._config.stop_cmd is not None:
            await self._node.run(list(self._config.stop_cmd))
        else:
            pid = await self.pid()
            if pid is None:
                return
            signal = "TERM" if graceful else "KILL"
            await self._node.run(["kill", f"-{signal}", str(pid)])
        await self.wait_ready(expect=False)

    async def start(self) -> None:
        if self._config.start_cmd is None:
            raise CommandFailed(
                f"[{self._node.name}] no agent start command configured; set "
                "BAI_DATAPLANE_AGENT_START_CMD, or the suite cannot bring the agent back"
            )
        await self._node.run(list(self._config.start_cmd))
        await self.wait_ready()

    async def restart(self, *, graceful: bool = True) -> None:
        await self.stop(graceful=graceful)
        await self.start()
