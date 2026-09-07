"""FieldQuerier implementations for routings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.manager.data.deployment.types import ModelReplicaData, RouteInfo
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.specs.querier import BulkFieldQuerier, FieldQuerier


@dataclass
class ModelReplicaQuerier(FieldQuerier[RoutingRow, ModelReplicaData]):
    replica_id: ReplicaID

    @override
    def row_class(self) -> type[RoutingRow]:
        return RoutingRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RoutingRow.id

    @override
    def target_id_value(self) -> ReplicaID:
        return self.replica_id

    @override
    def to_data(self, row: RoutingRow) -> ModelReplicaData:
        return row.to_replica_data()


class BulkModelReplicaQuerier(BulkFieldQuerier[RoutingRow, ModelReplicaData]):
    """The replicas the caller named."""

    @override
    def row_class(self) -> type[RoutingRow]:
        return RoutingRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RoutingRow.id

    @override
    def to_data(self, row: RoutingRow) -> ModelReplicaData:
        return row.to_replica_data()


class BulkRouteQuerier(BulkFieldQuerier[RoutingRow, RouteInfo]):
    """The same rows read as routes."""

    @override
    def row_class(self) -> type[RoutingRow]:
        return RoutingRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RoutingRow.id

    @override
    def to_data(self, row: RoutingRow) -> RouteInfo:
        return row.to_route_info()
