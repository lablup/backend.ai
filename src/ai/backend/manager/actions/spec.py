import enum
from dataclasses import dataclass

from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType


class ActionKind(enum.StrEnum):
    """The shape of an action's target, recorded on every audit row."""

    SINGLE_ENTITY = "single_entity"
    BULK = "bulk"
    SCOPE = "scope"
    RELATION = "relation"
    MEMBERSHIP = "membership"
    GLOBAL = "global"
    LOOKUP = "lookup"

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
            case ActionKind.MEMBERSHIP:
                return "an action moving one entity into scopes, or out of them"
            case ActionKind.GLOBAL:
                return "an action operating over everything, divided by no scope"
            case ActionKind.LOOKUP:
                return "an action reading an entity id from a natural key"


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
    type: EntityType
    id: str
