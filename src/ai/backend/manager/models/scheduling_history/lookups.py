"""Lookup specs reaching the session or deployment a history row was recorded for."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_history import DeploymentHistoryID
from ai.backend.common.data.entity.kernel_scheduling_history import KernelSchedulingHistoryID
from ai.backend.common.data.entity.route_history import RouteHistoryID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.session_scheduling_history import SessionSchedulingHistoryID
from ai.backend.manager.models.scheduling_history.row import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


@dataclass
class SessionSchedulingHistoryOwnerLookup(FieldOwnerLookup[SessionSchedulingHistoryID, SessionID]):
    """The session a scheduling history row was recorded for."""

    @override
    def build_query(
        self, field_ids: Sequence[SessionSchedulingHistoryID]
    ) -> sa.sql.Select[tuple[SessionSchedulingHistoryID, SessionID]]:
        return sa.select(
            SessionSchedulingHistoryRow.id, SessionSchedulingHistoryRow.session_id
        ).where(SessionSchedulingHistoryRow.id.in_(field_ids))

    @override
    def to_entity_id(self, value: UUID) -> SessionID:
        return SessionID(value)


@dataclass
class KernelSchedulingHistoryOwnerLookup(FieldOwnerLookup[KernelSchedulingHistoryID, SessionID]):
    """The session a kernel scheduling history row was recorded under."""

    @override
    def build_query(
        self, field_ids: Sequence[KernelSchedulingHistoryID]
    ) -> sa.sql.Select[tuple[KernelSchedulingHistoryID, SessionID]]:
        return sa.select(
            KernelSchedulingHistoryRow.id, KernelSchedulingHistoryRow.session_id
        ).where(KernelSchedulingHistoryRow.id.in_(field_ids))

    @override
    def to_entity_id(self, value: UUID) -> SessionID:
        return SessionID(value)


@dataclass
class DeploymentHistoryOwnerLookup(FieldOwnerLookup[DeploymentHistoryID, DeploymentID]):
    """The deployment a history row was recorded for."""

    @override
    def build_query(
        self, field_ids: Sequence[DeploymentHistoryID]
    ) -> sa.sql.Select[tuple[DeploymentHistoryID, DeploymentID]]:
        return sa.select(DeploymentHistoryRow.id, DeploymentHistoryRow.deployment_id).where(
            DeploymentHistoryRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID) -> DeploymentID:
        return DeploymentID(value)


@dataclass
class RouteHistoryOwnerLookup(FieldOwnerLookup[RouteHistoryID, DeploymentID]):
    """The deployment a route history row was recorded under."""

    @override
    def build_query(
        self, field_ids: Sequence[RouteHistoryID]
    ) -> sa.sql.Select[tuple[RouteHistoryID, DeploymentID]]:
        return sa.select(RouteHistoryRow.id, RouteHistoryRow.deployment_id).where(
            RouteHistoryRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID) -> DeploymentID:
        return DeploymentID(value)
