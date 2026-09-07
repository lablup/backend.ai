"""BulkFieldQuerier implementations for the scheduling history tables."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.deployment.types import DeploymentHistoryData, RouteHistoryData
from ai.backend.manager.data.kernel.types import KernelSchedulingHistoryData
from ai.backend.manager.data.session.types import SessionSchedulingHistoryData
from ai.backend.manager.models.scheduling_history.row import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.specs.querier import BulkFieldQuerier


class BulkSessionSchedulingHistoryQuerier(
    BulkFieldQuerier[SessionSchedulingHistoryRow, SessionSchedulingHistoryData]
):
    """The session scheduling history rows the caller named."""

    @override
    def row_class(self) -> type[SessionSchedulingHistoryRow]:
        return SessionSchedulingHistoryRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return SessionSchedulingHistoryRow.id

    @override
    def to_data(self, row: SessionSchedulingHistoryRow) -> SessionSchedulingHistoryData:
        return row.to_data()


class BulkKernelSchedulingHistoryQuerier(
    BulkFieldQuerier[KernelSchedulingHistoryRow, KernelSchedulingHistoryData]
):
    """The kernel scheduling history rows the caller named."""

    @override
    def row_class(self) -> type[KernelSchedulingHistoryRow]:
        return KernelSchedulingHistoryRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return KernelSchedulingHistoryRow.id

    @override
    def to_data(self, row: KernelSchedulingHistoryRow) -> KernelSchedulingHistoryData:
        return row.to_data()


class BulkDeploymentHistoryQuerier(BulkFieldQuerier[DeploymentHistoryRow, DeploymentHistoryData]):
    """The deployment history rows the caller named."""

    @override
    def row_class(self) -> type[DeploymentHistoryRow]:
        return DeploymentHistoryRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return DeploymentHistoryRow.id

    @override
    def to_data(self, row: DeploymentHistoryRow) -> DeploymentHistoryData:
        return row.to_data()


class BulkRouteHistoryQuerier(BulkFieldQuerier[RouteHistoryRow, RouteHistoryData]):
    """The route history rows the caller named."""

    @override
    def row_class(self) -> type[RouteHistoryRow]:
        return RouteHistoryRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RouteHistoryRow.id

    @override
    def to_data(self, row: RouteHistoryRow) -> RouteHistoryData:
        return row.to_data()
