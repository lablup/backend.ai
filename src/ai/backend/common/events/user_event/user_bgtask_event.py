from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional, override

from .user_event import UserEvent


@dataclass
class UserBgTaskEvent(UserEvent):  # TODO: Need to separate UserPartialSuccessEvent
    task_id: str
    message: str
    status: str
    current_progress: str
    total_progress: str

    @override
    def event_name(self) -> Optional[str]:
        return self.status

    @override
    def retry_count(self) -> Optional[int]:
        return None

    @override
    def user_event_mapping(self) -> Mapping[str, Any]:
        return asdict(self)


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


@dataclass
class UserBgtaskAlreadyDoneEvent(UserEvent):
    task_id: str
    message: str
    current_progress: float
    total_progress: float

    @override
    def event_name(self) -> Optional[str]:
        return "bgtask_already_done"

    @override
    def retry_count(self) -> Optional[int]:
        return None

    @override
    def user_event_mapping(self) -> Mapping[str, Any]:
        return asdict(self)
