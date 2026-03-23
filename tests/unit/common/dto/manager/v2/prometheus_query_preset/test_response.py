"""Tests for ai.backend.common.dto.manager.v2.prometheus_query_preset.response module."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    CreateQueryDefinitionPayload,
    DeleteQueryDefinitionPayload,
    ExecuteQueryDefinitionPayload,
    GetQueryDefinitionPayload,
    ModifyQueryDefinitionPayload,
    QueryDefinitionExecuteDataInfo,
    QueryDefinitionMetricResultInfo,
    QueryDefinitionNode,
    SearchQueryDefinitionsPayload,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.types import (
    MetricLabelEntryInfo,
    MetricValueInfo,
    QueryDefinitionOptionsInfo,
)

_UUID1 = UUID("550e8400-e29b-41d4-a716-446655440000")
_UUID2 = UUID("660e8400-e29b-41d4-a716-446655440001")
_NOW = datetime(2025, 3, 17, 12, 0, 0, tzinfo=UTC)


def _make_options() -> QueryDefinitionOptionsInfo:
    return QueryDefinitionOptionsInfo(
        filter_labels=["instance", "job"],
        group_labels=["instance"],
    )


def _make_query_definition_node(
    node_id: UUID = _UUID1,
    name: str = "cpu_usage",
    time_window: str | None = "5m",
) -> QueryDefinitionNode:
    return QueryDefinitionNode(
        id=node_id,
        name=name,
        metric_name="node_cpu_seconds_total",
        query_template="rate({metric}[{time_window}])",
        time_window=time_window,
        options=_make_options(),
        created_at=_NOW,
        updated_at=_NOW,
    )


class TestQueryDefinitionNode:
    """Tests for QueryDefinitionNode model."""

    def test_creation_with_all_fields(self) -> None:
        node = _make_query_definition_node()
        assert node.id == _UUID1
        assert node.name == "cpu_usage"
        assert node.metric_name == "node_cpu_seconds_total"
        assert node.time_window == "5m"

    def test_creation_without_time_window(self) -> None:
        node = _make_query_definition_node(time_window=None)
        assert node.time_window is None

    def test_default_time_window_is_none(self) -> None:
        node = QueryDefinitionNode(
            id=_UUID1,
            name="test",
            metric_name="metric",
            query_template="query",
            options=_make_options(),
            created_at=_NOW,
            updated_at=_NOW,
        )
        assert node.time_window is None

    def test_nested_options(self) -> None:
        node = _make_query_definition_node()
        assert isinstance(node.options, QueryDefinitionOptionsInfo)
        assert node.options.filter_labels == ["instance", "job"]
        assert node.options.group_labels == ["instance"]

    def test_missing_required_field_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            QueryDefinitionNode.model_validate({
                "id": str(_UUID1),
                "name": "test",
                # missing metric_name, query_template, options, created_at, updated_at
            })

    def test_round_trip_serialization(self) -> None:
        node = _make_query_definition_node()
        json_str = node.model_dump_json()
        restored = QueryDefinitionNode.model_validate_json(json_str)
        assert restored.id == _UUID1
        assert restored.name == "cpu_usage"
        assert restored.time_window == "5m"

    def test_round_trip_preserves_nested_options(self) -> None:
        node = _make_query_definition_node()
        json_str = node.model_dump_json()
        restored = QueryDefinitionNode.model_validate_json(json_str)
        assert restored.options.filter_labels == ["instance", "job"]
        assert restored.options.group_labels == ["instance"]

    def test_round_trip_with_none_time_window(self) -> None:
        node = _make_query_definition_node(time_window=None)
        json_str = node.model_dump_json()
        restored = QueryDefinitionNode.model_validate_json(json_str)
        assert restored.time_window is None

    def test_model_dump_json_includes_all_fields(self) -> None:
        node = _make_query_definition_node()
        data = json.loads(node.model_dump_json())
        assert "id" in data
        assert "name" in data
        assert "metric_name" in data
        assert "query_template" in data
        assert "time_window" in data
        assert "options" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_nested_options_in_json(self) -> None:
        node = _make_query_definition_node()
        data = json.loads(node.model_dump_json())
        assert "filter_labels" in data["options"]
        assert "group_labels" in data["options"]
        assert data["options"]["filter_labels"] == ["instance", "job"]


class TestCreateQueryDefinitionPayload:
    """Tests for CreateQueryDefinitionPayload model."""

    def test_creation_with_node(self) -> None:
        node = _make_query_definition_node()
        payload = CreateQueryDefinitionPayload(item=node)
        assert isinstance(payload.item, QueryDefinitionNode)
        assert payload.item.name == "cpu_usage"

    def test_missing_item_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateQueryDefinitionPayload.model_validate({})

    def test_round_trip_serialization(self) -> None:
        node = _make_query_definition_node()
        payload = CreateQueryDefinitionPayload(item=node)
        json_str = payload.model_dump_json()
        restored = CreateQueryDefinitionPayload.model_validate_json(json_str)
        assert restored.item.name == "cpu_usage"
        assert restored.item.options.filter_labels == ["instance", "job"]


class TestModifyQueryDefinitionPayload:
    """Tests for ModifyQueryDefinitionPayload model."""

    def test_creation_with_node(self) -> None:
        node = _make_query_definition_node()
        payload = ModifyQueryDefinitionPayload(item=node)
        assert isinstance(payload.item, QueryDefinitionNode)

    def test_round_trip_serialization(self) -> None:
        node = _make_query_definition_node()
        payload = ModifyQueryDefinitionPayload(item=node)
        json_str = payload.model_dump_json()
        restored = ModifyQueryDefinitionPayload.model_validate_json(json_str)
        assert restored.item.id == _UUID1


class TestDeleteQueryDefinitionPayload:
    """Tests for DeleteQueryDefinitionPayload model."""

    def test_creation_with_id(self) -> None:
        payload = DeleteQueryDefinitionPayload(id=_UUID1)
        assert payload.id == _UUID1

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteQueryDefinitionPayload.model_validate({})

    def test_round_trip_serialization(self) -> None:
        payload = DeleteQueryDefinitionPayload(id=_UUID2)
        json_str = payload.model_dump_json()
        restored = DeleteQueryDefinitionPayload.model_validate_json(json_str)
        assert restored.id == _UUID2


class TestGetQueryDefinitionPayload:
    """Tests for GetQueryDefinitionPayload model."""

    def test_creation_with_node(self) -> None:
        node = _make_query_definition_node()
        payload = GetQueryDefinitionPayload(item=node)
        assert payload.item is not None
        assert payload.item.name == "cpu_usage"

    def test_creation_with_none(self) -> None:
        payload = GetQueryDefinitionPayload(item=None)
        assert payload.item is None

    def test_default_item_is_none(self) -> None:
        payload = GetQueryDefinitionPayload()
        assert payload.item is None

    def test_round_trip_serialization_with_node(self) -> None:
        node = _make_query_definition_node()
        payload = GetQueryDefinitionPayload(item=node)
        json_str = payload.model_dump_json()
        restored = GetQueryDefinitionPayload.model_validate_json(json_str)
        assert restored.item is not None
        assert restored.item.name == "cpu_usage"


class TestSearchQueryDefinitionsPayload:
    """Tests for SearchQueryDefinitionsPayload model."""

    def test_creation_with_empty_list(self) -> None:
        payload = SearchQueryDefinitionsPayload(items=[], total_count=0)
        assert payload.items == []
        assert payload.total_count == 0

    def test_creation_with_items(self) -> None:
        nodes = [
            _make_query_definition_node(_UUID1, "query1"),
            _make_query_definition_node(_UUID2, "query2"),
        ]
        payload = SearchQueryDefinitionsPayload(items=nodes, total_count=2)
        assert len(payload.items) == 2
        assert payload.total_count == 2

    def test_missing_total_count_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchQueryDefinitionsPayload.model_validate({"items": []})

    def test_round_trip_serialization(self) -> None:
        nodes = [_make_query_definition_node()]
        payload = SearchQueryDefinitionsPayload(items=nodes, total_count=1)
        json_str = payload.model_dump_json()
        restored = SearchQueryDefinitionsPayload.model_validate_json(json_str)
        assert restored.total_count == 1
        assert len(restored.items) == 1
        assert restored.items[0].name == "cpu_usage"

    def test_round_trip_preserves_nested_options(self) -> None:
        nodes = [_make_query_definition_node()]
        payload = SearchQueryDefinitionsPayload(items=nodes, total_count=1)
        json_str = payload.model_dump_json()
        restored = SearchQueryDefinitionsPayload.model_validate_json(json_str)
        assert restored.items[0].options.filter_labels == ["instance", "job"]


class TestQueryDefinitionMetricResultInfo:
    """Tests for QueryDefinitionMetricResultInfo model."""

    def test_creation_with_all_fields(self) -> None:
        metric = [MetricLabelEntryInfo(key="instance", value="localhost")]
        values = [MetricValueInfo(timestamp=1700000000.0, value="42.5")]
        result = QueryDefinitionMetricResultInfo(metric=metric, values=values)
        assert len(result.metric) == 1
        assert len(result.values) == 1

    def test_creation_with_empty_lists(self) -> None:
        result = QueryDefinitionMetricResultInfo(metric=[], values=[])
        assert result.metric == []
        assert result.values == []

    def test_nested_metric_labels(self) -> None:
        metric = [
            MetricLabelEntryInfo(key="instance", value="host1"),
            MetricLabelEntryInfo(key="job", value="prometheus"),
        ]
        result = QueryDefinitionMetricResultInfo(metric=metric, values=[])
        assert result.metric[0].key == "instance"
        assert result.metric[1].key == "job"

    def test_nested_metric_values(self) -> None:
        values = [
            MetricValueInfo(timestamp=1700000000.0, value="10.5"),
            MetricValueInfo(timestamp=1700000060.0, value="11.0"),
        ]
        result = QueryDefinitionMetricResultInfo(metric=[], values=values)
        assert result.values[0].timestamp == 1700000000.0
        assert result.values[0].value == "10.5"

    def test_round_trip_serialization(self) -> None:
        metric = [MetricLabelEntryInfo(key="env", value="prod")]
        values = [MetricValueInfo(timestamp=1700000000.0, value="99.9")]
        result = QueryDefinitionMetricResultInfo(metric=metric, values=values)
        json_str = result.model_dump_json()
        restored = QueryDefinitionMetricResultInfo.model_validate_json(json_str)
        assert restored.metric[0].key == "env"
        assert restored.values[0].value == "99.9"


class TestQueryDefinitionExecuteDataInfo:
    """Tests for QueryDefinitionExecuteDataInfo model."""

    def test_creation_with_all_fields(self) -> None:
        metric_result = QueryDefinitionMetricResultInfo(metric=[], values=[])
        data = QueryDefinitionExecuteDataInfo(
            result_type="matrix",
            result=[metric_result],
        )
        assert data.result_type == "matrix"
        assert len(data.result) == 1

    def test_creation_with_empty_result(self) -> None:
        data = QueryDefinitionExecuteDataInfo(result_type="vector", result=[])
        assert data.result_type == "vector"
        assert data.result == []

    def test_round_trip_serialization(self) -> None:
        metric = [MetricLabelEntryInfo(key="job", value="test")]
        values = [MetricValueInfo(timestamp=1700000000.0, value="1.0")]
        metric_result = QueryDefinitionMetricResultInfo(metric=metric, values=values)
        data = QueryDefinitionExecuteDataInfo(result_type="matrix", result=[metric_result])
        json_str = data.model_dump_json()
        restored = QueryDefinitionExecuteDataInfo.model_validate_json(json_str)
        assert restored.result_type == "matrix"
        assert len(restored.result) == 1
        assert restored.result[0].metric[0].key == "job"


class TestExecuteQueryDefinitionPayload:
    """Tests for ExecuteQueryDefinitionPayload model."""

    def test_creation_with_all_fields(self) -> None:
        data = QueryDefinitionExecuteDataInfo(result_type="matrix", result=[])
        payload = ExecuteQueryDefinitionPayload(status="success", data=data)
        assert payload.status == "success"
        assert payload.data.result_type == "matrix"

    def test_missing_status_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ExecuteQueryDefinitionPayload.model_validate({
                "data": {"result_type": "matrix", "result": []}
            })

    def test_nested_data_info(self) -> None:
        metric = [MetricLabelEntryInfo(key="instance", value="host1")]
        values = [MetricValueInfo(timestamp=1700000000.0, value="5.0")]
        metric_result = QueryDefinitionMetricResultInfo(metric=metric, values=values)
        data = QueryDefinitionExecuteDataInfo(result_type="vector", result=[metric_result])
        payload = ExecuteQueryDefinitionPayload(status="success", data=data)
        assert isinstance(payload.data, QueryDefinitionExecuteDataInfo)
        assert payload.data.result[0].metric[0].key == "instance"

    def test_round_trip_serialization(self) -> None:
        data = QueryDefinitionExecuteDataInfo(result_type="matrix", result=[])
        payload = ExecuteQueryDefinitionPayload(status="success", data=data)
        json_str = payload.model_dump_json()
        restored = ExecuteQueryDefinitionPayload.model_validate_json(json_str)
        assert restored.status == "success"
        assert restored.data.result_type == "matrix"

    def test_model_dump_json_includes_all_fields(self) -> None:
        data = QueryDefinitionExecuteDataInfo(result_type="matrix", result=[])
        payload = ExecuteQueryDefinitionPayload(status="success", data=data)
        dumped = json.loads(payload.model_dump_json())
        assert "status" in dumped
        assert "data" in dumped
        assert "result_type" in dumped["data"]
        assert "result" in dumped["data"]
