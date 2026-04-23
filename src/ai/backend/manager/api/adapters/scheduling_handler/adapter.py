"""Adapter surfacing the registered deployment scheduling handlers as DTOs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.dto.manager.v2.scheduling_handler.response import (
    ListSchedulingHandlersPayload,
)
from ai.backend.common.dto.manager.v2.scheduling_handler.types import (
    SchedulingHandlerCategory,
    SchedulingHandlerNode,
)

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
    from ai.backend.manager.sokovan.deployment.handlers import DeploymentHandler


def _first_docstring_line(cls: type[DeploymentHandler]) -> str | None:
    """Return the first non-empty line of ``cls.__doc__`` or ``None``."""
    doc = cls.__doc__
    if doc is None:
        return None
    for raw_line in doc.splitlines():
        stripped = raw_line.strip()
        if stripped:
            return stripped
    return None


class SchedulingHandlerAdapter:
    """Expose the deployment coordinator's live handler registry as DTO nodes.

    Unlike most domain adapters this one has no Processor dependency —
    the data is pulled from the coordinator that actually dispatches the
    handlers, so this enumeration and the validation in
    ``deployment_options_from_input`` always agree on the same set.
    """

    def __init__(self, deployment_coordinator: DeploymentCoordinator) -> None:
        self._deployment_coordinator = deployment_coordinator

    async def list_scheduling_handlers(self) -> ListSchedulingHandlersPayload:
        """Return all handlers currently registered on the coordinator."""
        items = [
            SchedulingHandlerNode(
                name=handler.name(),
                category=SchedulingHandlerCategory(handler.category().value),
                description=_first_docstring_line(type(handler)),
            )
            for handler in self._deployment_coordinator.registered_handlers()
        ]
        return ListSchedulingHandlersPayload(items=items)
