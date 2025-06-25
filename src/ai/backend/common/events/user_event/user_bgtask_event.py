from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional, override

from .user_event import UserEvent


@dataclass
class UserBgtaskUpdatedEvent(UserEvent):
    task_id: str
    message: str
    current_progress: float
    total_progress: float

    @override
    def event_name(self) -> Optional[str]:
        return "bgtask_updated"

    @override
    def retry_count(self) -> Optional[int]:
        return 5

    @override
    def user_event_mapping(self) -> Mapping[str, Any]:
        return asdict(self)

    @override
    def is_close_event(self) -> bool:
        return False


@dataclass
class UserBgtaskDoneEvent(UserEvent):
    task_id: str
    message: str

    @override
    def event_name(self) -> Optional[str]:
        return "bgtask_done"

    @override
    def retry_count(self) -> Optional[int]:
        return None

    @override
    def user_event_mapping(self) -> Mapping[str, Any]:
        return asdict(self)

    @override
    def is_close_event(self) -> bool:
        return True


@dataclass
class UserBgtaskPartialSuccessEvent(UserEvent):
    task_id: str
    message: str
    errors: list[str]

    @override
    def event_name(self) -> Optional[str]:
        return "bgtask_done"

    @override
    def retry_count(self) -> Optional[int]:
        return None

    @override
    def user_event_mapping(self) -> Mapping[str, Any]:
        return asdict(self)

    @override
    def is_close_event(self) -> bool:
        return True


@dataclass
class UserBgtaskCancelledEvent(UserEvent):
    task_id: str
    message: str

    @override
    def event_name(self) -> Optional[str]:
        return "bgtask_cancelled"

    @override
    def retry_count(self) -> Optional[int]:
        return None

    @override
    def user_event_mapping(self) -> Mapping[str, Any]:
        return asdict(self)

    @override
    def is_close_event(self) -> bool:
        return True


@dataclass
class UserBgtaskFailedEvent(UserEvent):
    task_id: str
    message: str

    @override
    def event_name(self) -> Optional[str]:
        return "bgtask_failed"

    @override
    def retry_count(self) -> Optional[int]:
        return None

    @override
    def user_event_mapping(self) -> Mapping[str, Any]:
        return asdict(self)

    @override
    def is_close_event(self) -> bool:
        return True
