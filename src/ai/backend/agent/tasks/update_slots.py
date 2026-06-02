"""Periodic task that refreshes per-agent resource slots."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from ai.backend.common.cron import PeriodicTask

if TYPE_CHECKING:
    from ai.backend.agent.runtime import AgentRuntime

_UPDATE_SLOTS_INTERVAL: Final[float] = 30.0


class UpdateSlotsTask(PeriodicTask):
    """Periodically refresh the resource slots of all agents in the runtime."""

    _runtime: Final[AgentRuntime]

    def __init__(self, runtime: AgentRuntime) -> None:
        self._runtime = runtime

    @property
    def name(self) -> str:
        return "update_slots"

    @property
    def interval(self) -> float:
        return _UPDATE_SLOTS_INTERVAL

    @property
    def initial_delay(self) -> float:
        return 0.0

    async def run(self) -> None:
        await self._runtime.update_agent_slots()
