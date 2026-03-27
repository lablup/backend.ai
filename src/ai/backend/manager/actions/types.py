import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.common.data.permission.types import EntityType, OperationType


class OperationStatus(enum.StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    UNKNOWN = "unknown"
    RUNNING = "running"


class ActionOperationType(enum.StrEnum):
    GET = "get"
    SEARCH = "search"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PURGE = "purge"

    def to_permission_operation(self) -> OperationType:
        match self:
            case ActionOperationType.GET:
                return OperationType.READ
            case ActionOperationType.SEARCH:
                return OperationType.READ
            case ActionOperationType.CREATE:
                return OperationType.CREATE
            case ActionOperationType.UPDATE:
                return OperationType.UPDATE
            case ActionOperationType.DELETE:
                return OperationType.SOFT_DELETE
            case ActionOperationType.PURGE:
                return OperationType.HARD_DELETE


@dataclass
class ActionSpec:
    entity_type: EntityType
    operation_type: ActionOperationType

    def type(self) -> str:
        return f"{self.entity_type}:{self.operation_type}"


class AbstractProcessorPackage(ABC):
    @abstractmethod
    def supported_actions(self) -> list[ActionSpec]:
        """Get the list of action specs that this processors can handle."""
        raise NotImplementedError
