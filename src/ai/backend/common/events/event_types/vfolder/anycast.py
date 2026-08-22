from typing import override

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
    @classmethod
    @override
    def event_name(cls) -> str:
        return "vfolder_deletion_success"


class VFolderDeletionFailureEvent(VFolderEvent):
    message: str

    @classmethod
    @override
    def event_name(cls) -> str:
        return "vfolder_deletion_failure"


class VFolderCloneSuccessEvent(VFolderEvent):
    dst_vfid: VFolderID

    @classmethod
    @override
    def event_name(cls) -> str:
        return "vfolder_clone_success"


class VFolderCloneFailureEvent(VFolderEvent):
    dst_vfid: VFolderID
    message: str

    @classmethod
    @override
    def event_name(cls) -> str:
        return "vfolder_clone_failure"
