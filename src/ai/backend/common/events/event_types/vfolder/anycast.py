from typing import Any, Self, override

from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import VFolderID


class VFolderEvent(AbstractAnycastEvent):
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


class VFolderDeletionSuccessEvent(VFolderEvent):
    @override
    def serialize(self) -> tuple[Any, ...]:
        return (str(self.vfid),)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            vfid=VFolderID.from_str(value[0]),
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "vfolder_deletion_success"


class VFolderDeletionFailureEvent(VFolderEvent):
    message: str

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
            vfid=VFolderID.from_str(value[0]),
            message=value[1],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "vfolder_deletion_failure"


class VFolderCloneSuccessEvent(VFolderEvent):
    dst_vfid: VFolderID

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
            vfid=VFolderID.from_str(value[0]),
            dst_vfid=VFolderID.from_str(value[1]),
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "vfolder_clone_success"


class VFolderCloneFailureEvent(VFolderEvent):
    dst_vfid: VFolderID
    message: str

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
            vfid=VFolderID.from_str(value[0]),
            dst_vfid=VFolderID.from_str(value[1]),
            message=value[2],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "vfolder_clone_failure"
