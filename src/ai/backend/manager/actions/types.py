import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Final

from ai.backend.common.data.entity.types import EntityType, ScopeType
from ai.backend.common.data.permission.types import OperationType, Permission

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
    RESTORE = "restore"

    @classmethod
    def read_operations(cls) -> frozenset["ActionOperationType"]:
        """The operations that only read. Everything else changes state.

        The audit layer draws its "always record" line here: a state change is
        recorded unconditionally, while recording a read is a configurable choice.
        """
        return frozenset({cls.GET, cls.SEARCH})

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
            case ActionOperationType.RESTORE:
                return OperationType.SOFT_DELETE

    def to_permission(self) -> Permission:
        """The permission an action performing this operation must hold.

        ``RESTORE`` shares ``SOFT_DELETE``: undoing a soft delete flips one status
        flag back and reaches nothing the deleter could not already reach.
        """
        match self:
            case ActionOperationType.GET | ActionOperationType.SEARCH:
                return Permission.READ
            case ActionOperationType.CREATE:
                return Permission.CREATE
            case ActionOperationType.UPDATE:
                return Permission.UPDATE
            case ActionOperationType.DELETE | ActionOperationType.RESTORE:
                return Permission.SOFT_DELETE
            case ActionOperationType.PURGE:
                return Permission.HARD_DELETE


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
