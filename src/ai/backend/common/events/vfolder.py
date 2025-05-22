from dataclasses import dataclass
from typing import Optional, Self, override

from ai.backend.common.events.types import AbstractEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import VFolderID


@dataclass
class VFolderEvent(AbstractEvent):
    vfid: VFolderID

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.VFOLDER

    @override
    def domain_id(self) -> Optional[str]:
        return str(self.vfid)

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class VFolderDeletionSuccessEvent(VFolderEvent):
    def serialize(self) -> tuple:
        return (str(self.vfid),)

    @classmethod
    def deserialize(cls, value: tuple) -> Self:
        return cls(
            VFolderID.from_str(value[0]),
        )

    @classmethod
    def event_name(cls) -> str:
        return "vfolder_deletion_success"


@dataclass
class VFolderDeletionFailureEvent(VFolderEvent):
    message: str

    def serialize(self) -> tuple:
        return (
            str(self.vfid),
            self.message,
        )

    @classmethod
    def deserialize(cls, value: tuple) -> Self:
        return cls(
            VFolderID.from_str(value[0]),
            value[1],
        )

    @classmethod
    def event_name(cls) -> str:
        return "vfolder_deletion_failure"
