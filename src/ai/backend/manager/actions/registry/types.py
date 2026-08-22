"""What a group is built from and what a wiring records."""

from __future__ import annotations

import enum
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


class Concern(enum.StrEnum):
    """The areas a wiring can belong to.

    Every area an entity can be wired under is declared here, so adding a domain is a
    choice of area rather than a new name.
    """

    APP_CONFIG = "app_config"
    ARTIFACT_REGISTRY = "artifact_registry"
    CONTAINER_REGISTRY = "container_registry"
    DEPLOYMENT = "deployment"
    METRIC = "metric"
    NOTIFICATION_CENTER = "notification_center"
    ORGANIZATION = "organization"
    RBAC = "rbac"
    RESOURCE_GROUP = "resource_group"
    RESOURCE_POLICY = "resource_policy"
    SESSION = "session"
    SYSTEM = "system"
    VFOLDER = "vfolder"
    VISIBILITY = "visibility"

    def describe(self) -> str:
        """What the area holds, as the catalog listing explains it."""
        match self:
            case Concern.APP_CONFIG:
                return "the domain storing the settings the frontend builds its screens from"
            case Concern.ARTIFACT_REGISTRY:
                return "the domain pulling artifacts in from outside and storing them"
            case Concern.CONTAINER_REGISTRY:
                return "the domain reading the images a session runs from"
            case Concern.DEPLOYMENT:
                return "the domain creating and running the deployments that serve a model"
            case Concern.METRIC:
                return "the domain keeping the queries a metric is read with"
            case Concern.NOTIFICATION_CENTER:
                return "the domain sending what the system announces along a set route"
            case Concern.ORGANIZATION:
                return "the domain managing users and the organization they belong to"
            case Concern.RBAC:
                return "the domain deciding through roles who may do what"
            case Concern.RESOURCE_GROUP:
                return "the domain managing a group's capacity and how it is shared out"
            case Concern.RESOURCE_POLICY:
                return "the domain setting the limits on what a user may consume"
            case Concern.SESSION:
                return "the domain creating and managing the sessions a user runs"
            case Concern.SYSTEM:
                return "the domain holding what a superadmin applies to the whole system"
            case Concern.VFOLDER:
                return "the domain of the virtual folders a user stores and shares data in"
            case Concern.VISIBILITY:
                return "the domain letting a user look back at what happened in the system"


@dataclass(frozen=True)
class ConcernMeta:
    """The area a group's operations belong to, for listing them."""

    name: Concern


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
