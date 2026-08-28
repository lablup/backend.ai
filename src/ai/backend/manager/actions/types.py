import enum
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
    RELATION = "relation"
    GLOBAL = "global"
    LOOKUP = "lookup"
    # Still on the legacy ``BaseAction`` base, which declares no shape.
    UNKNOWN = "unknown"

    def describe(self) -> str:
        """What the operation targets, as the catalog listing explains it."""
        match self:
            case ActionKind.SINGLE_ENTITY:
                return "an action naming one entity by id and operating on it"
            case ActionKind.BULK:
                return "an action taking several entity ids and operating on each"
            case ActionKind.SCOPE:
                return "an action reaching every entity under a scope at once"
            case ActionKind.RELATION:
                return "an action linking two entities, or unlinking them"
            case ActionKind.GLOBAL:
                return "an action operating over everything, divided by no scope"
            case ActionKind.LOOKUP:
                return "an action reading an entity id from a natural key"
            case ActionKind.UNKNOWN:
                return "an action still on the legacy base, to be removed"


class ActionGate(enum.StrEnum):
    """Who a wired processor lets through, orthogonal to :class:`ActionKind`."""

    ANONYMOUS = "anonymous"
    # Every authenticated caller, whatever their roles.
    PUBLIC = "public"
    # Checked against the caller's permissions; ``ActionKind`` says where.
    PERMISSION = "permission"

    def describe(self) -> str:
        """Who gets through, as the catalog listing explains it."""
        match self:
            case ActionGate.ANONYMOUS:
                return "an action asking the caller for no permission"
            case ActionGate.PUBLIC:
                return "an action any authenticated user passes"
            case ActionGate.PERMISSION:
                return "an action only a user holding the permission may perform"


class ActionBacking(enum.StrEnum):
    """What runs a wired processor's operation."""

    # The shared implementation over the repository's ops, driven by the action's spec.
    GENERIC = "generic"
    # An implementation the domain wrote for this operation alone.
    CUSTOM = "custom"

    def describe(self) -> str:
        """What runs the operation, as the catalog listing explains it."""
        match self:
            case ActionBacking.GENERIC:
                return "an action the shared implementation performs from its spec"
            case ActionBacking.CUSTOM:
                return "an action the domain implemented itself"


class ActionOperationType(enum.StrEnum):
    GET = "get"
    SEARCH = "search"
    CREATE = "create"
    UPDATE = "update"
    UPSERT = "upsert"
    DELETE = "delete"
    PURGE = "purge"
    RESTORE = "restore"
    LOOKUP = "lookup"

    @classmethod
    def read_operations(cls) -> frozenset["ActionOperationType"]:
        """The operations that only read. Everything else changes state.

        The audit layer draws its "always record" line here: a state change is
        recorded unconditionally, while recording a read is a configurable choice.
        """
        return frozenset({cls.GET, cls.SEARCH, cls.LOOKUP})

    def to_permission_operation(self) -> OperationType:
        """The legacy single :class:`OperationType` this operation maps to.

        ``UPSERT`` narrows to ``CREATE``: this axis carries one value and cannot
        express the ``CREATE | UPDATE`` mask, so it keeps the stronger of the two.
        """
        match self:
            case ActionOperationType.GET:
                return OperationType.READ
            case ActionOperationType.SEARCH:
                return OperationType.READ
            case ActionOperationType.LOOKUP:
                return OperationType.READ
            case ActionOperationType.CREATE:
                return OperationType.CREATE
            case ActionOperationType.UPDATE:
                return OperationType.UPDATE
            case ActionOperationType.UPSERT:
                return OperationType.CREATE
            case ActionOperationType.DELETE:
                return OperationType.SOFT_DELETE
            case ActionOperationType.PURGE:
                return OperationType.HARD_DELETE
            case ActionOperationType.RESTORE:
                return OperationType.SOFT_DELETE

    def to_permission(self) -> Permission:
        """The permission an action performing this operation must hold.

        The result is a mask, not necessarily a single bit, and every bit in it is
        required: ``UPSERT`` may insert or overwrite, so demanding only ``CREATE``
        would let it overwrite without ``UPDATE`` and vice versa.

        ``RESTORE`` shares ``SOFT_DELETE``: undoing a soft delete flips one status
        flag back and reaches nothing the deleter could not already reach.
        """
        match self:
            case ActionOperationType.GET | ActionOperationType.SEARCH | ActionOperationType.LOOKUP:
                return Permission.READ
            case ActionOperationType.CREATE:
                return Permission.CREATE
            case ActionOperationType.UPDATE:
                return Permission.UPDATE
            case ActionOperationType.UPSERT:
                return Permission.CREATE | Permission.UPDATE
            case ActionOperationType.DELETE | ActionOperationType.RESTORE:
                return Permission.SOFT_DELETE
            case ActionOperationType.PURGE:
                return Permission.HARD_DELETE


@dataclass
@dataclass(frozen=True)
class ActionSpec:
    """Legacy actions' (entity, operation) pair. The v2 bases carry an action_name
    instead, which is declared rather than composed."""

    entity_type: EntityType
    operation_type: ActionOperationType

    def type(self) -> str:
        return f"{self.entity_type}:{self.operation_type}"


@dataclass(frozen=True)
class Scope:
    type: ScopeType
    id: str
