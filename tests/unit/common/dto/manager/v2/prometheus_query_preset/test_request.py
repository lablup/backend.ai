"""Tests for ai.backend.common.dto.manager.v2.prometheus_query_preset.request module."""

from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    CreateQueryDefinitionInput,
    CreateQueryDefinitionOptionsInput,
    DeleteQueryDefinitionInput,
    ExecuteQueryDefinitionInput,
    ExecuteQueryDefinitionOptionsInput,
    MetricLabelEntry,
    ModifyQueryDefinitionInput,
    ModifyQueryDefinitionOptionsInput,
    QueryDefinitionFilter,
    QueryDefinitionOrder,
    SearchQueryDefinitionsInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.types import (
    OrderDirection,
    QueryDefinitionOrderField,
)

_SAMPLE_UUID = UUID("550e8400-e29b-41d4-a716-446655440000")


def _make_create_options() -> CreateQueryDefinitionOptionsInput:
    return CreateQueryDefinitionOptionsInput(
        filter_labels=["instance", "job"],
        group_labels=["instance"],
    )


class TestCreateQueryDefinitionOptionsInput:
    """Tests for CreateQueryDefinitionOptionsInput model."""

    def test_valid_creation(self) -> None:
        opts = CreateQueryDefinitionOptionsInput(
            filter_labels=["instance"],
            group_labels=["instance", "env"],
        )
        assert opts.filter_labels == ["instance"]
        assert opts.group_labels == ["instance", "env"]

    def test_creation_with_empty_lists(self) -> None:
        opts = CreateQueryDefinitionOptionsInput(filter_labels=[], group_labels=[])
        assert opts.filter_labels == []
        assert opts.group_labels == []


class TestCreateQueryDefinitionInput:
    """Tests for CreateQueryDefinitionInput model."""

    def test_valid_creation_with_required_fields(self) -> None:
        inp = CreateQueryDefinitionInput(
            name="cpu_usage",
            metric_name="node_cpu_seconds_total",
            query_template="rate({metric}[{time_window}])",
            options=_make_create_options(),
        )
        assert inp.name == "cpu_usage"
        assert inp.metric_name == "node_cpu_seconds_total"
        assert inp.time_window is None

    def test_valid_creation_with_time_window(self) -> None:
        inp = CreateQueryDefinitionInput(
            name="cpu_usage",
            metric_name="node_cpu_seconds_total",
            query_template="rate({metric}[{time_window}])",
            time_window="5m",
            options=_make_create_options(),
        )
        assert inp.time_window == "5m"

    def test_valid_time_window_formats(self) -> None:
        for tw in ["1m", "5m", "1h", "24h", "7d"]:
            inp = CreateQueryDefinitionInput(
                name="test",
                metric_name="metric",
                query_template="query",
                time_window=tw,
                options=_make_create_options(),
            )
            assert inp.time_window == tw

    def test_invalid_time_window_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateQueryDefinitionInput(
                name="test",
                metric_name="metric",
                query_template="query",
                time_window="invalid",
                options=_make_create_options(),
            )

    def test_blank_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateQueryDefinitionInput(
                name="",
                metric_name="metric",
                query_template="query",
                options=_make_create_options(),
            )

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateQueryDefinitionInput(
                name="   ",
                metric_name="metric",
                query_template="query",
                options=_make_create_options(),
            )

    def test_name_is_stripped(self) -> None:
        inp = CreateQueryDefinitionInput(
            name="  cpu_usage  ",
            metric_name="metric",
            query_template="query",
            options=_make_create_options(),
        )
        assert inp.name == "cpu_usage"

    def test_name_max_length(self) -> None:
        inp = CreateQueryDefinitionInput(
            name="x" * 256,
            metric_name="metric",
            query_template="query",
            options=_make_create_options(),
        )
        assert len(inp.name) == 256

    def test_name_exceeds_max_length_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateQueryDefinitionInput(
                name="x" * 257,
                metric_name="metric",
                query_template="query",
                options=_make_create_options(),
            )

    def test_missing_options_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateQueryDefinitionInput.model_validate({
                "name": "test",
                "metric_name": "metric",
                "query_template": "query",
            })

    def test_round_trip_serialization(self) -> None:
        inp = CreateQueryDefinitionInput(
            name="cpu_usage",
            metric_name="node_cpu",
            query_template="rate({metric}[5m])",
            time_window="5m",
            options=_make_create_options(),
        )
        json_str = inp.model_dump_json()
        restored = CreateQueryDefinitionInput.model_validate_json(json_str)
        assert restored.name == "cpu_usage"
        assert restored.time_window == "5m"


class TestModifyQueryDefinitionOptionsInput:
    """Tests for ModifyQueryDefinitionOptionsInput model."""

    def test_default_values(self) -> None:
        opts = ModifyQueryDefinitionOptionsInput()
        assert opts.filter_labels is None
        assert opts.group_labels is None

    def test_creation_with_values(self) -> None:
        opts = ModifyQueryDefinitionOptionsInput(
            filter_labels=["instance"],
            group_labels=[],
        )
        assert opts.filter_labels == ["instance"]
        assert opts.group_labels == []


class TestModifyQueryDefinitionInput:
    """Tests for ModifyQueryDefinitionInput model."""

    def test_default_time_window_is_sentinel(self) -> None:
        inp = ModifyQueryDefinitionInput()
        assert isinstance(inp.time_window, Sentinel)

    def test_all_fields_default_to_none_or_sentinel(self) -> None:
        inp = ModifyQueryDefinitionInput()
        assert inp.name is None
        assert inp.metric_name is None
        assert inp.query_template is None
        assert inp.options is None
        assert isinstance(inp.time_window, Sentinel)

    def test_time_window_none_means_clear(self) -> None:
        inp = ModifyQueryDefinitionInput(time_window=None)
        assert inp.time_window is None

    def test_time_window_valid_format(self) -> None:
        inp = ModifyQueryDefinitionInput(time_window="15m")
        assert inp.time_window == "15m"

    def test_time_window_invalid_format_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ModifyQueryDefinitionInput(time_window="invalid")

    def test_time_window_invalid_unit_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ModifyQueryDefinitionInput(time_window="5x")

    def test_blank_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ModifyQueryDefinitionInput(name="")

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ModifyQueryDefinitionInput(name="   ")

    def test_name_none_is_valid(self) -> None:
        inp = ModifyQueryDefinitionInput(name=None)
        assert inp.name is None

    def test_name_is_stripped(self) -> None:
        inp = ModifyQueryDefinitionInput(name="  test_query  ")
        assert inp.name == "test_query"

    def test_partial_update(self) -> None:
        inp = ModifyQueryDefinitionInput(
            name="new_name",
            metric_name="new_metric",
        )
        assert inp.name == "new_name"
        assert inp.metric_name == "new_metric"
        assert inp.query_template is None

    def test_round_trip_serialization(self) -> None:
        inp = ModifyQueryDefinitionInput(
            name="updated",
            time_window="10m",
        )
        json_str = inp.model_dump_json()
        restored = ModifyQueryDefinitionInput.model_validate_json(json_str)
        assert restored.name == "updated"
        assert restored.time_window == "10m"


class TestDeleteQueryDefinitionInput:
    """Tests for DeleteQueryDefinitionInput model."""

    def test_valid_creation(self) -> None:
        inp = DeleteQueryDefinitionInput(id=_SAMPLE_UUID)
        assert inp.id == _SAMPLE_UUID

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteQueryDefinitionInput.model_validate({})

    def test_round_trip_serialization(self) -> None:
        inp = DeleteQueryDefinitionInput(id=_SAMPLE_UUID)
        json_str = inp.model_dump_json()
        restored = DeleteQueryDefinitionInput.model_validate_json(json_str)
        assert restored.id == _SAMPLE_UUID


class TestQueryDefinitionFilter:
    """Tests for QueryDefinitionFilter model."""

    def test_default_name_is_none(self) -> None:
        f = QueryDefinitionFilter()
        assert f.name is None

    def test_creation_from_dict(self) -> None:
        f = QueryDefinitionFilter.model_validate({})
        assert f.name is None


class TestQueryDefinitionOrder:
    """Tests for QueryDefinitionOrder model."""

    def test_creation_with_field(self) -> None:
        order = QueryDefinitionOrder(field=QueryDefinitionOrderField.NAME)
        assert order.field == QueryDefinitionOrderField.NAME

    def test_default_direction_is_asc(self) -> None:
        order = QueryDefinitionOrder(field=QueryDefinitionOrderField.CREATED_AT)
        assert order.direction == OrderDirection.ASC

    def test_explicit_desc_direction(self) -> None:
        order = QueryDefinitionOrder(
            field=QueryDefinitionOrderField.UPDATED_AT,
            direction=OrderDirection.DESC,
        )
        assert order.direction == OrderDirection.DESC


class TestSearchQueryDefinitionsInput:
    """Tests for SearchQueryDefinitionsInput model."""

    def test_default_values(self) -> None:
        inp = SearchQueryDefinitionsInput()
        assert inp.filter is None
        assert inp.order is None
        assert inp.limit == 50
        assert inp.offset == 0

    def test_custom_pagination(self) -> None:
        inp = SearchQueryDefinitionsInput(limit=25, offset=50)
        assert inp.limit == 25
        assert inp.offset == 50

    def test_limit_min_boundary(self) -> None:
        inp = SearchQueryDefinitionsInput(limit=1)
        assert inp.limit == 1

    def test_limit_max_boundary(self) -> None:
        inp = SearchQueryDefinitionsInput(limit=1000)
        assert inp.limit == 1000

    def test_limit_exceeds_max_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchQueryDefinitionsInput(limit=1001)

    def test_limit_below_min_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchQueryDefinitionsInput(limit=0)

    def test_offset_negative_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchQueryDefinitionsInput(offset=-1)

    def test_with_order(self) -> None:
        order = QueryDefinitionOrder(field=QueryDefinitionOrderField.NAME)
        inp = SearchQueryDefinitionsInput(order=[order])
        assert inp.order is not None
        assert len(inp.order) == 1


class TestMetricLabelEntry:
    """Tests for MetricLabelEntry model."""

    def test_valid_creation(self) -> None:
        entry = MetricLabelEntry(key="instance", value="localhost:9090")
        assert entry.key == "instance"
        assert entry.value == "localhost:9090"

    def test_round_trip_serialization(self) -> None:
        entry = MetricLabelEntry(key="job", value="prometheus")
        json_str = entry.model_dump_json()
        restored = MetricLabelEntry.model_validate_json(json_str)
        assert restored.key == "job"
        assert restored.value == "prometheus"


class TestExecuteQueryDefinitionOptionsInput:
    """Tests for ExecuteQueryDefinitionOptionsInput model."""

    def test_default_values(self) -> None:
        opts = ExecuteQueryDefinitionOptionsInput()
        assert opts.filter_labels == []
        assert opts.group_labels == []

    def test_creation_with_filter_labels(self) -> None:
        labels = [MetricLabelEntry(key="instance", value="host1")]
        opts = ExecuteQueryDefinitionOptionsInput(filter_labels=labels)
        assert len(opts.filter_labels) == 1
        assert opts.filter_labels[0].key == "instance"

    def test_creation_with_group_labels(self) -> None:
        opts = ExecuteQueryDefinitionOptionsInput(group_labels=["instance", "env"])
        assert opts.group_labels == ["instance", "env"]


class TestExecuteQueryDefinitionInput:
    """Tests for ExecuteQueryDefinitionInput model."""

    def test_default_values(self) -> None:
        inp = ExecuteQueryDefinitionInput()
        assert inp.time_window is None
        assert inp.time_range is None
        assert isinstance(inp.options, ExecuteQueryDefinitionOptionsInput)

    def test_with_time_window(self) -> None:
        inp = ExecuteQueryDefinitionInput(time_window="5m")
        assert inp.time_window == "5m"

    def test_invalid_time_window_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ExecuteQueryDefinitionInput(time_window="bad_format")

    def test_with_options(self) -> None:
        labels = [MetricLabelEntry(key="env", value="prod")]
        opts = ExecuteQueryDefinitionOptionsInput(filter_labels=labels, group_labels=["env"])
        inp = ExecuteQueryDefinitionInput(options=opts)
        assert len(inp.options.filter_labels) == 1

    def test_round_trip_serialization(self) -> None:
        inp = ExecuteQueryDefinitionInput(time_window="1h")
        json_str = inp.model_dump_json()
        restored = ExecuteQueryDefinitionInput.model_validate_json(json_str)
        assert restored.time_window == "1h"
