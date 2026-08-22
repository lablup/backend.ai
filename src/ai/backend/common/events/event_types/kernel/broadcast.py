from __future__ import annotations

from typing import override

from ai.backend.common.events.event_types.kernel.types import KernelCreationInfo
from ai.backend.common.events.types import AbstractBroadcastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import KernelId, SessionId

from .types import KernelLifecycleEventReason


class BaseKernelEvent(AbstractBroadcastEvent):
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


class KernelPreparingBroadcastEvent(KernelCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_preparing"


class KernelPullingBroadcastEvent(KernelCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_pulling"


class KernelCreatingBroadcastEvent(KernelCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_creating"


class KernelStartedBroadcastEvent(KernelCreationEvent):
    """The only creation event that reports how the container came up."""

    creation_info: KernelCreationInfo

    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_started"


class KernelCancelledBroadcastEvent(KernelLifecycleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_cancelled"


class KernelTerminationEvent(BaseKernelEvent):
    session_id: SessionId
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN
    exit_code: int = -1

    @override
    def user_event(self) -> UserEvent | None:
        return None


class KernelTerminatingBroadcastEvent(KernelTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_terminating"


class KernelTerminatedBroadcastEvent(KernelTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_terminated"
