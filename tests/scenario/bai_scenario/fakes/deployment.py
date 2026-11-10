"""Stand-ins for what a deployment call reaches outside the database.

Both are asked something a real one answers from state this tree does not run: the
schedule mark goes to a Valkey the coordinator polls, and the handler names come from a
coordinator's live registry. Neither is mocked away — each answers with what it was
built from, so a scenario can read back what the call did.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
from ai.backend.manager.sokovan.deployment.handlers.base import DeploymentHandler


class FakeValkeyScheduleClient(ValkeyScheduleClient):
    """배포 주기를 깨우는 표시를 받아 적기만 한다."""

    _marks: list[tuple[str, str | None]]

    def __init__(self) -> None:
        self._marks = []

    @override
    async def mark_deployment_needed(
        self, lifecycle_type: str, sub_step: str | None = None
    ) -> None:
        self._marks.append((lifecycle_type, sub_step))

    def marked(self) -> tuple[tuple[str, str | None], ...]:
        """어떤 주기를 깨우라고 했는지, 부른 순서대로."""
        return tuple(self._marks)


class FakeDeploymentCoordinator(DeploymentCoordinator):
    """등록된 처리기만 답한다.

    옵션을 갈아끼울 때 이름을 대고 보는 자리가 여기다. 처리기는 실물이고, 이름도 그것이
    답하는 것을 쓴다.
    """

    _registered: tuple[DeploymentHandler, ...]

    def __init__(self, handlers: Sequence[DeploymentHandler]) -> None:
        self._registered = tuple(handlers)

    @override
    def registered_handlers(self) -> tuple[DeploymentHandler, ...]:
        return self._registered
