"""Owner resolutions reaching the session or deployment a history row was recorded for."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.deployment import DEPLOYMENT_ENTITY_TYPE, DeploymentID
from ai.backend.common.data.entity.deployment_history import DeploymentHistoryID
from ai.backend.common.data.entity.kernel_scheduling_history import KernelSchedulingHistoryID
from ai.backend.common.data.entity.route_history import RouteHistoryID
from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE, SessionID
from ai.backend.common.data.entity.session_scheduling_history import SessionSchedulingHistoryID
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.scheduling_history.lookups import (
    DeploymentHistoryOwnerLookup,
    KernelSchedulingHistoryOwnerLookup,
    RouteHistoryOwnerLookup,
    SessionSchedulingHistoryOwnerLookup,
)


@dataclass(frozen=True)
class HistoryIDLookupKey(LookupKey):
    """A history row's id, resolved into the entity it was recorded for."""

    history_id: FieldIdentifier

    @override
    def kind(self) -> str:
        return f"{self.history_id.field_type()}_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.history_id)}


@dataclass
class LookupSessionSchedulingHistoryOwnerAction(
    LookupFieldOwnerOpsAction[SessionSchedulingHistoryID, SessionID]
):
    """The session a scheduling history row was recorded for."""

    history_id: SessionSchedulingHistoryID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_session_scheduling_history_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return HistoryIDLookupKey(self.history_id)

    @override
    def field_id(self) -> SessionSchedulingHistoryID:
        return self.history_id

    @override
    def to_owner_lookup(self) -> SessionSchedulingHistoryOwnerLookup:
        return SessionSchedulingHistoryOwnerLookup()


@dataclass
class LookupBulkSessionSchedulingHistoryOwnerAction(
    LookupBulkFieldOwnerOpsAction[SessionSchedulingHistoryID, SessionID]
):
    """The sessions several scheduling history rows were recorded for."""

    history_ids: Sequence[SessionSchedulingHistoryID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_session_scheduling_history_owner"

    @override
    def to_lookup_key(self, field_id: SessionSchedulingHistoryID) -> LookupKey:
        return HistoryIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[SessionSchedulingHistoryID]:
        return tuple(self.history_ids)

    @override
    def to_owner_lookup(self) -> SessionSchedulingHistoryOwnerLookup:
        return SessionSchedulingHistoryOwnerLookup()


@dataclass
class LookupKernelSchedulingHistoryOwnerAction(
    LookupFieldOwnerOpsAction[KernelSchedulingHistoryID, SessionID]
):
    """The session a kernel scheduling history row was recorded under."""

    history_id: KernelSchedulingHistoryID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_kernel_scheduling_history_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return HistoryIDLookupKey(self.history_id)

    @override
    def field_id(self) -> KernelSchedulingHistoryID:
        return self.history_id

    @override
    def to_owner_lookup(self) -> KernelSchedulingHistoryOwnerLookup:
        return KernelSchedulingHistoryOwnerLookup()


@dataclass
class LookupBulkKernelSchedulingHistoryOwnerAction(
    LookupBulkFieldOwnerOpsAction[KernelSchedulingHistoryID, SessionID]
):
    """The sessions several kernel scheduling history rows were recorded under."""

    history_ids: Sequence[KernelSchedulingHistoryID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_kernel_scheduling_history_owner"

    @override
    def to_lookup_key(self, field_id: KernelSchedulingHistoryID) -> LookupKey:
        return HistoryIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[KernelSchedulingHistoryID]:
        return tuple(self.history_ids)

    @override
    def to_owner_lookup(self) -> KernelSchedulingHistoryOwnerLookup:
        return KernelSchedulingHistoryOwnerLookup()


@dataclass
class LookupDeploymentHistoryOwnerAction(
    LookupFieldOwnerOpsAction[DeploymentHistoryID, DeploymentID]
):
    """The deployment a history row was recorded for."""

    history_id: DeploymentHistoryID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_deployment_history_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return HistoryIDLookupKey(self.history_id)

    @override
    def field_id(self) -> DeploymentHistoryID:
        return self.history_id

    @override
    def to_owner_lookup(self) -> DeploymentHistoryOwnerLookup:
        return DeploymentHistoryOwnerLookup()


@dataclass
class LookupBulkDeploymentHistoryOwnerAction(
    LookupBulkFieldOwnerOpsAction[DeploymentHistoryID, DeploymentID]
):
    """The deployments several history rows were recorded for."""

    history_ids: Sequence[DeploymentHistoryID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_deployment_history_owner"

    @override
    def to_lookup_key(self, field_id: DeploymentHistoryID) -> LookupKey:
        return HistoryIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[DeploymentHistoryID]:
        return tuple(self.history_ids)

    @override
    def to_owner_lookup(self) -> DeploymentHistoryOwnerLookup:
        return DeploymentHistoryOwnerLookup()


@dataclass
class LookupRouteHistoryOwnerAction(LookupFieldOwnerOpsAction[RouteHistoryID, DeploymentID]):
    """The deployment a route history row was recorded under."""

    history_id: RouteHistoryID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_route_history_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return HistoryIDLookupKey(self.history_id)

    @override
    def field_id(self) -> RouteHistoryID:
        return self.history_id

    @override
    def to_owner_lookup(self) -> RouteHistoryOwnerLookup:
        return RouteHistoryOwnerLookup()


@dataclass
class LookupBulkRouteHistoryOwnerAction(
    LookupBulkFieldOwnerOpsAction[RouteHistoryID, DeploymentID]
):
    """The deployments several route history rows were recorded under."""

    history_ids: Sequence[RouteHistoryID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_route_history_owner"

    @override
    def to_lookup_key(self, field_id: RouteHistoryID) -> LookupKey:
        return HistoryIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[RouteHistoryID]:
        return tuple(self.history_ids)

    @override
    def to_owner_lookup(self) -> RouteHistoryOwnerLookup:
        return RouteHistoryOwnerLookup()
