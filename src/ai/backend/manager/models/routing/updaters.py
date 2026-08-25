"""Update specs for the routings table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteSubStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.model_serving.types import RoutingData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ReplicaUpdater(DataUpdater[RoutingRow, RoutingData]):
    """Edits one replica: its statuses, the session behind it, its share of the
    traffic and the revision it serves."""

    replica_id: ReplicaID
    status: OptionalState[RouteStatus] = field(default_factory=OptionalState[RouteStatus].nop)
    traffic_status: OptionalState[RouteTrafficStatus] = field(
        default_factory=OptionalState[RouteTrafficStatus].nop
    )
    session: OptionalState[UUID] = field(default_factory=OptionalState[UUID].nop)
    traffic_ratio: OptionalState[float] = field(default_factory=OptionalState[float].nop)
    revision: OptionalState[UUID] = field(default_factory=OptionalState[UUID].nop)
    error_data: OptionalState[dict[str, Any]] = field(
        default_factory=OptionalState[dict[str, Any]].nop
    )

    @property
    @override
    def row_class(self) -> type[RoutingRow]:
        return RoutingRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RoutingRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.replica_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.status.update_dict(to_update, "status")
        self.traffic_status.update_dict(to_update, "traffic_status")
        self.session.update_dict(to_update, "session")
        self.traffic_ratio.update_dict(to_update, "traffic_ratio")
        self.revision.update_dict(to_update, "revision")
        self.error_data.update_dict(to_update, "error_data")
        return to_update

    @override
    def to_data(self, row: RoutingRow) -> RoutingData:
        return row.to_data()


@dataclass
class ReplicaBatchUpdater(DataBatchUpdater[RoutingRow, RoutingData]):
    """Moves every named replica to the same statuses.

    ``sub_status`` is a :class:`TriState` because a replica leaving the
    PROVISIONING stage clears it explicitly.
    """

    replica_ids: Sequence[UUID]
    status: OptionalState[RouteStatus] = field(default_factory=OptionalState.nop)
    health_status: OptionalState[RouteHealthStatus] = field(default_factory=OptionalState.nop)
    traffic_status: OptionalState[RouteTrafficStatus] = field(default_factory=OptionalState.nop)
    sub_status: TriState[RouteSubStatus] = field(default_factory=TriState.nop)

    @property
    @override
    def row_class(self) -> type[RoutingRow]:
        return RoutingRow

    @override
    def conditions(self) -> list[QueryCondition]:
        return [RouteConditions.by_ids(list(self.replica_ids))]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        self.status.update_dict(values, "status")
        self.health_status.update_dict(values, "health_status")
        self.traffic_status.update_dict(values, "traffic_status")
        self.sub_status.update_dict(values, "sub_status")
        return values

    @override
    def to_data(self, row: RoutingRow) -> RoutingData:
        return row.to_data()
