from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset import (
    PROMETHEUS_QUERY_PRESET_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass(frozen=True)
class QueryMetricAction(BaseGlobalAction):
    """Base for a container metric read, which is a query fixed in code.

    Prometheus answers it, so the entity is the same one a stored query preset names;
    these reads differ only in being built in rather than a row. Whichever labels the
    caller narrows the query by, the operation is a search.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROMETHEUS_QUERY_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH
