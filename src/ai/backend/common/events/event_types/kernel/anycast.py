from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any, Self, override

from pydantic import Field

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
    creation_info: Mapping[str, Any] = Field(default_factory=dict)

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.kernel_id),
            str(self.session_id),
            self.reason,
            self.creation_info,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            kernel_id=KernelId(uuid.UUID(value[0])),
            session_id=SessionId(uuid.UUID(value[1])),
            reason=value[2],
            creation_info=value[3],
        )

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
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_started"


class KernelCancelledAnycastEvent(KernelLifecycleEvent):
    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.kernel_id),
            str(self.session_id),
            self.reason,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            kernel_id=KernelId(uuid.UUID(value[0])),
            session_id=SessionId(uuid.UUID(value[1])),
            reason=value[2],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_cancelled"


class KernelTerminationEvent(BaseKernelEvent):
    session_id: SessionId
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN
    exit_code: int = -1

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.kernel_id),
            str(self.session_id),
            self.reason,
            self.exit_code,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            kernel_id=KernelId(uuid.UUID(value[0])),
            session_id=SessionId(uuid.UUID(value[1])),
            reason=value[2],
            exit_code=value[3],
        )

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
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.kernel_id),
            self.container_id,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            kernel_id=KernelId(uuid.UUID(value[0])),
            container_id=value[1],
        )

    @override
    def user_event(self) -> UserEvent | None:
        return None

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_sync_kernel_logs"
