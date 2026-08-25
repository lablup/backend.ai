from __future__ import annotations

from typing import override

from ai.backend.common.events.event_types.kernel.types import KernelCreationInfo
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import KernelId, SessionId

from .types import KernelLifecycleEventReason


class BaseKernelEvent(AbstractAnycastEvent):
    kernel_id: KernelId

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
