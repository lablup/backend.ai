"""Killing and restarting the privilege helper the agent drives the host through.

Separate from `AgentController` because the two fail differently and a scenario needs to choose:
an agent that dies takes its own bookkeeping with it, while a privnet that dies leaves the agent
running and holding records for a host it can no longer touch.

Restart is a deployment fact, so it is a configured command rather than something guessed here --
the same reason `AgentController` refuses to invent one. On the reference rig that command also
brings the agent back, since the pair is started together and a mixed pair strands sessions.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from ai.backend.testutils.dataplane.nodes import Node

#: Matches the daemon however it was launched: under `setpriv` from the launcher, or directly.
DEFAULT_PATTERN = "ai.backend.agent.network.privnet"


class PrivnetNotStopped(RuntimeError):
    """The daemon was still running after the kill."""


@dataclass(frozen=True)
class PrivnetControlConfig:
    start_cmd: tuple[str, ...] = ()
    socket_path: str = ""
    pattern: str = DEFAULT_PATTERN

    @property
    def configured(self) -> bool:
        return bool(self.start_cmd)


class PrivnetController:
    _node: Node
    _config: PrivnetControlConfig

    def __init__(self, node: Node, config: PrivnetControlConfig) -> None:
        self._node = node
        self._config = config

    async def is_running(self) -> bool:
        result = await self._node.run(["pgrep", "-f", self._config.pattern], check=False)
        return bool(result.stdout.strip())

    async def kill(self, *, max_wait: float = 15.0) -> None:
        """SIGKILL every process matching the pattern, and wait for them to be gone.

        Nothing graceful on purpose: a scenario that kills the privnet is asking what the agent
        does when the host stops answering, and a handler running on the way out would answer a
        different question.
        """
        await self._node.run(["pkill", "-KILL", "-f", self._config.pattern], check=False)
        deadline = asyncio.get_running_loop().time() + max_wait
        while await self.is_running():
            if asyncio.get_running_loop().time() >= deadline:
                raise PrivnetNotStopped(
                    f"{self._config.pattern} on {self._node.name} survived SIGKILL for {max_wait}s"
                )
            await asyncio.sleep(0.5)

    async def start(self, *, max_wait: float = 90.0) -> None:
        """Run the configured start command and wait for the socket to come back.

        The socket, not the process: the agent's calls fail until the daemon is listening, so a
        scenario that continued at process start would be racing the thing it is testing.
        """
        if not self._config.configured:
            raise RuntimeError("no privnet start command is configured")
        await self._node.run(list(self._config.start_cmd))
        if not self._config.socket_path:
            return
        deadline = asyncio.get_running_loop().time() + max_wait
        while True:
            result = await self._node.run(["test", "-S", self._config.socket_path], check=False)
            if result.returncode == 0 and await self.is_running():
                return
            if asyncio.get_running_loop().time() >= deadline:
                raise PrivnetNotStopped(
                    f"privnet socket {self._config.socket_path} on {self._node.name} did not "
                    f"come back within {max_wait}s"
                )
            await asyncio.sleep(1.0)
