import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Final

from ai.backend.common.data.entity.types import EntityType, ScopeType
from ai.backend.common.data.permission.types import OperationType

# Placeholder substituted when an id (request_id, entity_id, ...) is absent while
# materializing action metadata into audit/report records.
BLANK_ID: Final[str] = "(unknown)"


class OperationStatus(enum.StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    UNKNOWN = "unknown"
    RUNNING = "running"
    # Rejected by a validator before the action ran. Kept apart from ERROR because a
    # denial is an authorization signal, not the operation failing.
    DENIED = "denied"


class ActionKind(enum.StrEnum):
    """The shape of an action's target, recorded on every audit row."""

    SINGLE_ENTITY = "single_entity"
    BULK = "bulk"
    SCOPE = "scope"
    GLOBAL = "global"
    LOOKUP = "lookup"
    # Still on the legacy ``BaseAction`` base, which declares no shape.
    UNKNOWN = "unknown"


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


@dataclass(frozen=True)
class Scope:
    type: ScopeType
    id: str
