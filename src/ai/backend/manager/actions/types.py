import enum
from abc import ABC, abstractmethod


class OperationStatus(enum.StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    UNKNOWN = "unknown"
    RUNNING = "running"


class AbstractProcessorPackage(ABC):
    @abstractmethod
    def supported_actions(self) -> list[str]:
        """Get the list of action types that this processors can handle."""
        raise NotImplementedError
