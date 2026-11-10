from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.clients.prometheus.metric_types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResult,
)
from ai.backend.manager.clients.prometheus.types import ValueType


@dataclass(frozen=True)
class SearchUserContainerMetricsAction(BaseSingleEntityAction):
    """Read one metric of a user's containers over a time range; answered for that user."""

    user_id: UserID
    metric_name: str
    value_type: ValueType
    time_range: QueryTimeRange

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_user_container_metrics"

    def labels(self) -> ContainerMetricOptionalLabel:
        return ContainerMetricOptionalLabel(user_id=self.user_id, value_type=self.value_type)


@dataclass(frozen=True)
class SearchUserContainerMetricsActionResult:
    result: list[ContainerMetricResult]
