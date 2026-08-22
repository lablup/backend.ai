"""What a group is built from and what a wiring records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.backend.common.data.entity.types import EntityData, EntityType, FieldType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.types import ActionBacking, ActionGate, ActionKind
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.repositories.ops.repository import OpsRepository


@dataclass(frozen=True)
class ProcessorDependencies[TData: EntityData]:
    monitors: ActionMonitors
    validators: ActionValidators
    repository: OpsRepository[TData]


@dataclass(frozen=True)
class ConcernMeta:
    """The area a group's operations belong to, for listing them.

    Declared where several entities share one area; a domain that is its own area
    takes its entity type's name.
    """

    name: str


@dataclass(frozen=True)
class GroupMeta:
    """What every operation of one group is answered for."""

    entity_type: EntityType


@dataclass(frozen=True)
class FieldGroupMeta:
    """What every operation of one field group is answered for.

    Names the field's own type; the entity owning it is the parent group's.
    """

    field_type: FieldType


@dataclass(frozen=True)
class SidecarGroupMeta:
    """What every read of one sidecar group is answered for."""

    entity_type: EntityType


@dataclass(frozen=True)
class WiredProcessor:
    """One wiring call, as the catalog records it.

    The action class carries what it declares — the operation, the action name, whether
    it runs against ops. What only the wiring knows is here.
    """

    concern: str
    entity_type: EntityType
    # Set when the operation is over a field row, whose owner ``entity_type`` names.
    field_type: FieldType | None
    action_cls: type[Any]
    kind: ActionKind
    gate: ActionGate
    backing: ActionBacking
