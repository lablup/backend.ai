from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Self, override

from pydantic import Field as PydanticField

from ai.backend.common.events.payload import BroadcastEventPayload
from ai.backend.common.events.types import AbstractBroadcastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import KernelId, SessionId

from .types import KernelLifecycleEventReason


class KernelLifecycleEventPayload(BroadcastEventPayload):
    kernel_id: KernelId
    session_id: SessionId
    reason: str = ""


class KernelCreationEventPayload(BroadcastEventPayload):
    kernel_id: KernelId
    session_id: SessionId
    reason: str = ""
    creation_info: Mapping[str, Any] = PydanticField(default_factory=dict)


class KernelTerminationEventPayload(BroadcastEventPayload):
    kernel_id: KernelId
    session_id: SessionId
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN
    exit_code: int = -1


class SyncKernelLogsEventPayload(BroadcastEventPayload):
    kernel_id: KernelId
    container_id: str


@dataclass
class BaseKernelEvent[TPayload: BroadcastEventPayload](AbstractBroadcastEvent[TPayload]):
    kernel_id: KernelId

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.KERNEL

    @override
    def domain_id(self) -> str | None:
        return str(self.kernel_id)


@dataclass
class KernelLifecycleEvent[TPayload: BroadcastEventPayload](BaseKernelEvent[TPayload]):
    session_id: SessionId
    reason: str = ""

    @override
    def user_event(self) -> UserEvent | None:
        return None


@dataclass
class KernelCreationEvent(KernelLifecycleEvent[KernelCreationEventPayload]):
    creation_info: Mapping[str, Any] = field(default_factory=dict)

    @override
    def to_payload(self) -> KernelCreationEventPayload:
        return KernelCreationEventPayload(
            kernel_id=self.kernel_id,
            session_id=self.session_id,
            reason=self.reason,
            creation_info=self.creation_info,
        )

    @classmethod
    @override
    def from_payload(cls, payload: KernelCreationEventPayload) -> Self:
        return cls(
            kernel_id=payload.kernel_id,
            session_id=payload.session_id,
            reason=payload.reason,
            creation_info=payload.creation_info,
        )

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


@dataclass
class KernelPreparingBroadcastEvent(KernelCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_preparing"


@dataclass
class KernelPullingBroadcastEvent(KernelCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_pulling"


@dataclass
class KernelCreatingBroadcastEvent(KernelCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_creating"


class KernelStartedBroadcastEvent(KernelCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_started"


class KernelCancelledBroadcastEvent(KernelLifecycleEvent[KernelLifecycleEventPayload]):
    @override
    def to_payload(self) -> KernelLifecycleEventPayload:
        return KernelLifecycleEventPayload(
            kernel_id=self.kernel_id,
            session_id=self.session_id,
            reason=self.reason,
        )

    @classmethod
    @override
    def from_payload(cls, payload: KernelLifecycleEventPayload) -> Self:
        return cls(
            kernel_id=payload.kernel_id,
            session_id=payload.session_id,
            reason=payload.reason,
        )

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


@dataclass
class KernelTerminationEvent(BaseKernelEvent[KernelTerminationEventPayload]):
    session_id: SessionId
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN
    exit_code: int = -1

    @override
    def to_payload(self) -> KernelTerminationEventPayload:
        return KernelTerminationEventPayload(
            kernel_id=self.kernel_id,
            session_id=self.session_id,
            reason=self.reason,
            exit_code=self.exit_code,
        )

    @classmethod
    @override
    def from_payload(cls, payload: KernelTerminationEventPayload) -> Self:
        return cls(
            kernel_id=payload.kernel_id,
            session_id=payload.session_id,
            reason=payload.reason,
            exit_code=payload.exit_code,
        )

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
            KernelId(uuid.UUID(value[0])),
            session_id=SessionId(uuid.UUID(value[1])),
            reason=value[2],
            exit_code=value[3],
        )

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
