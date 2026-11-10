from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.route_history import RouteHistoryID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.deployment.types import RouteHistoryData
from ai.backend.manager.models.scheduling_history.queriers import BulkRouteHistoryQuerier
from ai.backend.manager.models.scheduling_history.row import RouteHistoryRow
from ai.backend.manager.services.scheduling_history.actions.lookup_owner import (
    LookupBulkRouteHistoryOwnerAction,
)


@dataclass
class BulkGetRouteHistoriesAction(
    PartialBulkGetFieldOpsAction[RouteHistoryID, DeploymentID, RouteHistoryRow, RouteHistoryData]
):
    """Read the route history rows the caller named."""

    ids: Sequence[RouteHistoryID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_route_histories"

    @override
    def field_ids(self) -> Sequence[RouteHistoryID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkRouteHistoryOwnerAction:
        return LookupBulkRouteHistoryOwnerAction(history_ids=self.ids)

    @override
    def to_querier(self) -> BulkRouteHistoryQuerier:
        return BulkRouteHistoryQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[RouteHistoryID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
