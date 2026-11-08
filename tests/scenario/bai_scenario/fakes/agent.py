"""Stand-in for the agent registry a session service call reaches.

Only the calls a session scenario makes are answered; everything else stays unasked.
The answers are fixed, so a scenario states them as the value it expects.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ai.backend.common.types import AgentId, KernelId
from ai.backend.manager.models.session.row import SessionRow

CONTAINER_LOG = "the container log this run hands back"
"""The log every read of the agent returns."""


class FakeAgentRegistry:
    """Answers the agent calls a session service makes, and nothing else."""

    async def get_logs_from_agent(
        self, session: SessionRow, kernel_id: KernelId | None = None
    ) -> str:
        return CONTAINER_LOG

    async def shutdown_service(self, session: SessionRow, service: str) -> None:
        return None

    async def start_service(
        self,
        main_kernel_id: KernelId,
        agent_id: AgentId,
        service: str,
        opts: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        return {"status": "succeeded"}
