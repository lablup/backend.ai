from dataclasses import dataclass
from typing import Any, Self, override

from ai.backend.common.events.payload import AnycastEventPayload
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import VFolderID


class VFolderDeletionSuccessEventPayload(AnycastEventPayload):
    vfid: VFolderID


class VFolderDeletionFailureEventPayload(AnycastEventPayload):
    vfid: VFolderID
    message: str


class VFolderCloneSuccessEventPayload(AnycastEventPayload):
    vfid: VFolderID
    dst_vfid: VFolderID


class VFolderCloneFailureEventPayload(AnycastEventPayload):
    vfid: VFolderID
    dst_vfid: VFolderID
    message: str


@dataclass
class VFolderEvent[TPayload: AnycastEventPayload](AbstractAnycastEvent[TPayload]):
    vfid: VFolderID

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.VFOLDER

    @override
    def domain_id(self) -> str | None:
        return str(self.vfid)

    @override
    def user_event(self) -> UserEvent | None:
        return None


@dataclass
class VFolderDeletionSuccessEvent(VFolderEvent[VFolderDeletionSuccessEventPayload]):
    @override
    def to_payload(self) -> VFolderDeletionSuccessEventPayload:
        return VFolderDeletionSuccessEventPayload(
            vfid=self.vfid,
        )

    @classmethod
    @override
    def from_payload(cls, payload: VFolderDeletionSuccessEventPayload) -> Self:
        return cls(
            vfid=payload.vfid,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (str(self.vfid),)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            VFolderID.from_str(value[0]),
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "vfolder_deletion_success"


@dataclass
class VFolderDeletionFailureEvent(VFolderEvent[VFolderDeletionFailureEventPayload]):
    message: str

    @override
    def to_payload(self) -> VFolderDeletionFailureEventPayload:
        return VFolderDeletionFailureEventPayload(
            vfid=self.vfid,
            message=self.message,
        )

    @classmethod
    @override
    def from_payload(cls, payload: VFolderDeletionFailureEventPayload) -> Self:
        return cls(
            vfid=payload.vfid,
            message=payload.message,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.vfid),
            self.message,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            VFolderID.from_str(value[0]),
            value[1],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "vfolder_deletion_failure"


@dataclass
class VFolderCloneSuccessEvent(VFolderEvent[VFolderCloneSuccessEventPayload]):
    dst_vfid: VFolderID

    @override
    def to_payload(self) -> VFolderCloneSuccessEventPayload:
        return VFolderCloneSuccessEventPayload(
            vfid=self.vfid,
            dst_vfid=self.dst_vfid,
        )

    @classmethod
    @override
    def from_payload(cls, payload: VFolderCloneSuccessEventPayload) -> Self:
        return cls(
            vfid=payload.vfid,
            dst_vfid=payload.dst_vfid,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.vfid),
            str(self.dst_vfid),
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            VFolderID.from_str(value[0]),
            VFolderID.from_str(value[1]),
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "vfolder_clone_success"


@dataclass
class VFolderCloneFailureEvent(VFolderEvent[VFolderCloneFailureEventPayload]):
    dst_vfid: VFolderID
    message: str

    @override
    def to_payload(self) -> VFolderCloneFailureEventPayload:
        return VFolderCloneFailureEventPayload(
            vfid=self.vfid,
            dst_vfid=self.dst_vfid,
            message=self.message,
        )

    @classmethod
    @override
    def from_payload(cls, payload: VFolderCloneFailureEventPayload) -> Self:
        return cls(
            vfid=payload.vfid,
            dst_vfid=payload.dst_vfid,
            message=payload.message,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.vfid),
            str(self.dst_vfid),
            self.message,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            VFolderID.from_str(value[0]),
            VFolderID.from_str(value[1]),
            value[2],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "vfolder_clone_failure"
