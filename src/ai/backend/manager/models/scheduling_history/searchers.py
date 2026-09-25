"""List-read specs for the scheduling history tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.deployment.types import DeploymentHistoryData, RouteHistoryData
from ai.backend.manager.data.kernel.types import KernelSchedulingHistoryData
from ai.backend.manager.data.session.types import SessionSchedulingHistoryData
from ai.backend.manager.models.scheduling_history.row import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.scheduling_history.searchable_fields import (
    DeploymentHistorySearchableFields,
    KernelSchedulingHistorySearchableFields,
    RouteHistorySearchableFields,
    SessionSchedulingHistorySearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class SessionSchedulingHistorySearcher(
    Searcher[SessionSchedulingHistoryRow, SessionSchedulingHistoryData]
):
    """Session scheduling history rows matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(SessionSchedulingHistoryRow)

    @override
    def to_data(self, row: SessionSchedulingHistoryRow) -> SessionSchedulingHistoryData:
        return SessionSchedulingHistorySearchableFields.own.to_data(row)


@dataclass
class KernelSchedulingHistorySearcher(
    Searcher[KernelSchedulingHistoryRow, KernelSchedulingHistoryData]
):
    """Kernel scheduling history rows matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KernelSchedulingHistoryRow)

    @override
    def to_data(self, row: KernelSchedulingHistoryRow) -> KernelSchedulingHistoryData:
        return KernelSchedulingHistorySearchableFields.own.to_data(row)


@dataclass
class DeploymentHistorySearcher(Searcher[DeploymentHistoryRow, DeploymentHistoryData]):
    """Deployment history rows matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(DeploymentHistoryRow)

    @override
    def to_data(self, row: DeploymentHistoryRow) -> DeploymentHistoryData:
        return DeploymentHistorySearchableFields.own.to_data(row)


@dataclass
class RouteHistorySearcher(Searcher[RouteHistoryRow, RouteHistoryData]):
    """Route history rows matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RouteHistoryRow)

    @override
    def to_data(self, row: RouteHistoryRow) -> RouteHistoryData:
        return RouteHistorySearchableFields.own.to_data(row)
