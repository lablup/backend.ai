from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import SchedulingHistoryAction


@dataclass
class ResolveKernelSessionAction(SchedulingHistoryAction):
    """Resolve the session owning a kernel.

    Pre-step for kernel-scoped queries: the owning session is the authorization
    subject, so the caller resolves it first and passes it to the scoped action.
    """

    kernel_id: KernelId

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.KERNEL

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return str(self.kernel_id)


@dataclass
class ResolveKernelSessionActionResult(BaseActionResult):
    """Result of resolving the session owning a kernel."""

    session_id: SessionId

    @override
    def entity_id(self) -> str | None:
        return str(self.session_id)
