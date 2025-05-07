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
    def user_event_dict(self) -> Mapping[str, Any]:
        return asdict(self)
