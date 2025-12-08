import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass


class OperationStatus(enum.StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    UNKNOWN = "unknown"
    RUNNING = "running"


class MonitorTag(enum.StrEnum):
    SKIP_AUDIT_LOG = "skip_audit_log"


@dataclass
class ActionSpec:
    entity_type: str
    operation_type: str

    def type(self) -> str:
        return f"{self.entity_type}:{self.operation_type}"


class AbstractProcessorPackage(ABC):
    @abstractmethod
    def supported_actions(self) -> list[ActionSpec]:
        """Get the list of action specs that this processors can handle."""
        raise NotImplementedError
