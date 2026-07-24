"""Tests of the agent controller, against a fake node.

The controller kills the developer's agent for a living, so its failure modes deserve pinning
before a scenario uses it: a stop that returns before the port is free, a start that reports
success while the agent is still recovering, a PID query that matches its own shell.

No privileges, no agent — these run in ordinary CI.
"""

from __future__ import annotations

import pytest

from ai.backend.testutils.dataplane.agent_control import (
    AgentControlConfig,
    AgentController,
    AgentNotReady,
)
from ai.backend.testutils.dataplane.nodes import CommandFailed, CommandResult

PORT = 6011
_SS = ("sh", "-c", f"ss -ltn 'sport = :{PORT}' | tail -n +2")
_SS_PID = (
    "sh",
    "-c",
    f"ss -ltnp 'sport = :{PORT}' 2>/dev/null | grep -oE 'pid=[0-9]+' | head -1 || true",
)


def _pgid(pid: str) -> tuple[str, ...]:
    return ("sh", "-c", f"ps -o pgid= -p {pid} 2>/dev/null || true")


class ScriptedNode:
    """Returns a different reply each time the same command is asked, so a poll loop can be
    driven deterministically. Unlisted commands succeed with empty output."""

    calls: list[tuple[str, ...]]

    def __init__(self, scripts: dict[tuple[str, ...], list[str]]) -> None:
        self._scripts = scripts
        self._counts: dict[tuple[str, ...], int] = {}
        self.calls = []

    @property
    def name(self) -> str:
        return "n1"

    async def run(self, argv: list[str], *, check: bool = True) -> CommandResult:
        key = tuple(argv)
        self.calls.append(key)
        script = self._scripts.get(key)
        if script is None:
            return CommandResult("n1", key, 0, "", "")
        index = min(self._counts.get(key, 0), len(script) - 1)
        self._counts[key] = self._counts.get(key, 0) + 1
        return CommandResult("n1", key, 0, script[index], "")


def _controller(
    node: ScriptedNode,
    *,
    start_cmd: tuple[str, ...] | None = None,
    stop_cmd: tuple[str, ...] | None = None,
) -> AgentController:
    config = AgentControlConfig(
        start_cmd=start_cmd,
        stop_cmd=stop_cmd,
        rpc_port=PORT,
        ready_timeout=0.2,
        stop_timeout=0.2,
        poll_interval=0,
    )
    return AgentController(node, config)


LISTENING = "LISTEN 0 1024 127.0.0.1:6011 0.0.0.0:*"


class TestPid:
    async def test_returns_the_rpc_port_owner(self) -> None:
        """The agent is identified by who holds its RPC port, not by a process name — setproctitle
        rewrites the command line, so a name lookup would find nothing."""
        node = ScriptedNode({_SS_PID: ["pid=4242\n"]})
        assert await _controller(node).pid() == 4242

    async def test_none_when_the_port_is_unowned(self) -> None:
        node = ScriptedNode({_SS_PID: [""]})
        assert await _controller(node).pid() is None


class TestReadiness:
    async def test_ready_when_the_rpc_port_listens(self) -> None:
        assert await _controller(ScriptedNode({_SS: [LISTENING]})).is_ready()

    async def test_not_ready_when_the_port_is_silent(self) -> None:
        assert not await _controller(ScriptedNode({_SS: [""]})).is_ready()

    async def test_wait_ready_polls_until_the_port_opens(self) -> None:
        """A process that exists but has not finished recover() would let a scenario snapshot a
        half-rebuilt data plane, so readiness is the port and not the process."""
        node = ScriptedNode({_SS: ["", "", LISTENING]})
        await _controller(node).wait_ready()

    async def test_wait_ready_gives_up_with_a_diagnosable_message(self) -> None:
        node = ScriptedNode({_SS: [""]})
        with pytest.raises(AgentNotReady, match="did not come up"):
            await _controller(node).wait_ready()

    async def test_waiting_for_the_port_to_close_has_its_own_message(self) -> None:
        node = ScriptedNode({_SS: [LISTENING]})
        with pytest.raises(AgentNotReady, match="release its RPC port"):
            await _controller(node).wait_ready(expect=False)


class TestStop:
    async def test_kills_the_whole_process_group_and_waits_for_close(self) -> None:
        """The group, not the port-owning worker alone: the agent is a supervisor plus a worker
        sharing one group, and signalling only the worker leaves the supervisor to respawn it. The
        negative pid targets the group; the tmux parent is in a different one and survives."""
        node = ScriptedNode({
            _SS_PID: ["pid=4242\n"],
            _pgid("4242"): ["4200\n"],
            _SS: [LISTENING, ""],
        })
        await _controller(node).stop()
        assert ("kill", "-TERM", "--", "-4200") in node.calls

    async def test_sigkill_when_not_graceful(self) -> None:
        node = ScriptedNode({
            _SS_PID: ["pid=4242\n"],
            _pgid("4242"): ["4200\n"],
            _SS: [""],
        })
        await _controller(node).stop(graceful=False)
        assert ("kill", "-KILL", "--", "-4200") in node.calls

    async def test_falls_back_to_the_bare_pid_when_the_group_is_unknown(self) -> None:
        node = ScriptedNode({
            _SS_PID: ["pid=4242\n"],
            _pgid("4242"): [""],
            _SS: [""],
        })
        await _controller(node).stop()
        assert ("kill", "-TERM", "4242") in node.calls

    async def test_a_configured_stop_command_wins_over_signalling(self) -> None:
        node = ScriptedNode({_SS: [""]})
        await _controller(node, stop_cmd=("systemctl", "stop", "bai-agent")).stop()
        assert ("systemctl", "stop", "bai-agent") in node.calls
        assert not any(c[0] == "kill" for c in node.calls)

    async def test_stopping_an_absent_agent_is_not_an_error(self) -> None:
        node = ScriptedNode({_SS_PID: [""], _SS: [""]})
        await _controller(node).stop()


class TestStart:
    async def test_runs_the_command_and_waits_for_readiness(self) -> None:
        node = ScriptedNode({_SS: ["", LISTENING]})
        await _controller(node, start_cmd=("systemctl", "start", "bai-agent")).start()
        assert ("systemctl", "start", "bai-agent") in node.calls

    async def test_no_start_command_is_a_loud_failure(self) -> None:
        """Nothing can restart a foreground dev agent on the developer's behalf. Failing here
        beats leaving their stack down and reporting success."""
        node = ScriptedNode({_SS: [""]})
        with pytest.raises(CommandFailed, match="no agent start command configured"):
            await _controller(node).start()


class TestConfig:
    def test_unconfigured_until_a_start_command_exists(self) -> None:
        assert not AgentControlConfig().configured
        assert AgentControlConfig(start_cmd=("true",)).configured
