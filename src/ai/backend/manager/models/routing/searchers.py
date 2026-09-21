"""Searcher spec for the routings table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.deployment.types import ModelReplicaData, RouteData, RouteInfo
from ai.backend.manager.data.model_serving.types import RoutingData
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.routing.searchable_fields import ReplicaSearchableFields
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ModelReplicaSearcher(Searcher[RoutingRow, ModelReplicaData]):
    """Routing rows read as replicas."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RoutingRow)

    @override
    def to_data(self, row: RoutingRow) -> ModelReplicaData:
        return ReplicaSearchableFields.own.to_data(row)


@dataclass
class RouteInfoSearcher(Searcher[RoutingRow, RouteInfo]):
    """Routing rows read as routes."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RoutingRow)

    @override
    def to_data(self, row: RoutingRow) -> RouteInfo:
        return ReplicaSearchableFields.own.to_route_info(row)


@dataclass
class RouteDataSearcher(Searcher[RoutingRow, RouteData]):
    """Routing rows read as the reconciler's route records."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RoutingRow)

    @override
    def to_data(self, row: RoutingRow) -> RouteData:
        return ReplicaSearchableFields.own.to_route_data(row)


@dataclass
class RoutingDataSearcher(Searcher[RoutingRow, RoutingData]):
    """Routing rows read as the legacy REST v1 route projection."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RoutingRow)

    @override
    def to_data(self, row: RoutingRow) -> RoutingData:
        return row.to_data()
