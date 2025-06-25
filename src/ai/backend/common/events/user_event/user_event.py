from abc import ABC, abstractmethod
from typing import Any, Mapping, Optional


class UserEvent(ABC):
    @abstractmethod
    def event_name(self) -> Optional[str]:
        """Get the name of the event."""
        raise NotImplementedError

    @abstractmethod
    def retry_count(self) -> Optional[int]:
        """Get the retry count for the event."""
        raise NotImplementedError

    @abstractmethod
    def user_event_mapping(self) -> Mapping[str, Any]:
        """Get the user event as a dictionary."""
        raise NotImplementedError

    @abstractmethod
    def is_close_event(self) -> bool:
        """
        Indicate if the event is a close event.
        Close events are used to signal that the event is no longer needed to be propagated.
        """
        raise NotImplementedError
