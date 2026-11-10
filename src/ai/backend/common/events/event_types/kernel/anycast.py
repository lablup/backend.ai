from __future__ import annotations

from collections.abc import Mapping
from typing import override

from ai.backend.common.events.event_types.kernel.types import KernelCreationInfo
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain, LogScopedEvent
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import AgentId, KernelId, SessionId
from ai.backend.logging.structured import LogValue

from .types import KernelLifecycleEventReason


class BaseKernelEvent(AbstractAnycastEvent, LogScopedEvent):
    kernel_id: KernelId

    @override
    def log_fields(self, source: AgentId) -> Mapping[str, LogValue]:
        return {"kernel_id": self.kernel_id}

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.KERNEL

    @override
    def domain_id(self) -> str | None:
        return str(self.kernel_id)


class KernelLifecycleEvent(BaseKernelEvent):
    session_id: SessionId
    reason: str = ""

    @override
    def log_fields(self, source: AgentId) -> Mapping[str, LogValue]:
        return {"kernel_id": self.kernel_id, "session_id": self.session_id}

    @override
    def user_event(self) -> UserEvent | None:
        return None


class KernelCreationEvent(KernelLifecycleEvent):
    @override
    def user_event(self) -> UserEvent | None:
        return None


class KernelPreparingAnycastEvent(KernelCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_preparing"


class KernelPullingAnycastEvent(KernelCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_pulling"


class KernelCreatingAnycastEvent(KernelCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_creating"


class KernelStartedAnycastEvent(KernelCreationEvent):
    """The only creation event that reports how the container came up."""

    creation_info: KernelCreationInfo

    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_started"


class KernelCancelledAnycastEvent(KernelLifecycleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_cancelled"


class KernelTerminationEvent(BaseKernelEvent):
    session_id: SessionId
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN
    exit_code: int = -1

    @override
    def log_fields(self, source: AgentId) -> Mapping[str, LogValue]:
        return {"kernel_id": self.kernel_id, "session_id": self.session_id}

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class KernelTerminatingAnycastEvent(KernelTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_terminating"


class KernelTerminatedAnycastEvent(KernelTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_terminated"


class DoSyncKernelLogsEvent(BaseKernelEvent):
    container_id: str

    @override
    def user_event(self) -> UserEvent | None:
        return None

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_sync_kernel_logs"
