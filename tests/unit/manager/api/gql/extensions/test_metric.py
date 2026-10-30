from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest
from graphql import GraphQLObjectType, OperationType
from prometheus_client import REGISTRY

from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.manager.api.gql.extensions.metric import GQLMetricExtension


def _recorded_count_samples(field_name: str) -> list[dict[str, str]]:
    return [
        sample.labels
        for family in REGISTRY.collect()
        if family.name == "backendai_graphql_request_count"
        for sample in family.samples
        if sample.name.endswith("_total") and sample.labels.get("field_name") == field_name
    ]


async def _resolver(root: Any, info: Any, **kwargs: Any) -> str:
    return "result"


def _resolve_info(
    *, operation_name: str, field_name: str, parent_type: str, nested: bool
) -> MagicMock:
    info = MagicMock()
    info.context.metric_observer = GraphQLMetricObserver.instance()
    info.return_type = GraphQLObjectType("Item", fields={})
    info.operation.operation = OperationType.QUERY
    info.operation.name.value = operation_name
    info.field_name = field_name
    info.parent_type.name = parent_type
    info.path.prev = MagicMock() if nested else None
    return info


class TestGQLMetricExtension:
    @pytest.fixture
    def extension(self) -> GQLMetricExtension:
        return GQLMetricExtension()

    async def test_operation_names_share_root_field_series(
        self, extension: GQLMetricExtension
    ) -> None:
        for operation_name in ("ScreenA", "ScreenB", "ScreenC"):
            info = _resolve_info(
                operation_name=operation_name,
                field_name="metric_probe_root",
                parent_type="Query",
                nested=False,
            )
            result = extension.resolve(_resolver, None, info)
            assert asyncio.iscoroutine(result)
            await result

        samples = _recorded_count_samples("metric_probe_root")
        assert len(samples) == 1
        assert "operation_name" not in samples[0]
        assert samples[0]["parent_type"] == "Query"

    async def test_nested_fields_are_not_recorded(self, extension: GQLMetricExtension) -> None:
        info = _resolve_info(
            operation_name="Nested",
            field_name="metric_probe_nested",
            parent_type="Item",
            nested=True,
        )

        result = extension.resolve(_resolver, None, info)
        assert asyncio.iscoroutine(result)

        assert await result == "result"
        assert _recorded_count_samples("metric_probe_nested") == []
