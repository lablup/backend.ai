"""Tests for ai.backend.common.dto.manager.v2.prometheus_query_preset.types module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.prometheus_query_preset.types import (
    MetricLabelEntryInfo,
    MetricValueInfo,
    OrderDirection,
    QueryDefinitionOptionsInfo,
    QueryDefinitionOrderField,
)


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_member_count(self) -> None:
        assert len(OrderDirection) == 2

    def test_is_str_enum(self) -> None:
        assert isinstance(OrderDirection.ASC, str)

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestQueryDefinitionOrderField:
    """Tests for QueryDefinitionOrderField enum."""

    def test_name_value(self) -> None:
        assert QueryDefinitionOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert QueryDefinitionOrderField.CREATED_AT.value == "created_at"

    def test_updated_at_value(self) -> None:
        assert QueryDefinitionOrderField.UPDATED_AT.value == "updated_at"

    def test_member_count(self) -> None:
        assert len(QueryDefinitionOrderField) == 3

    def test_is_str_enum(self) -> None:
        assert isinstance(QueryDefinitionOrderField.NAME, str)

    def test_from_string_name(self) -> None:
        assert QueryDefinitionOrderField("name") is QueryDefinitionOrderField.NAME

    def test_from_string_created_at(self) -> None:
        assert QueryDefinitionOrderField("created_at") is QueryDefinitionOrderField.CREATED_AT


class TestQueryDefinitionOptionsInfo:
    """Tests for QueryDefinitionOptionsInfo sub-model."""

    def test_creation_with_all_fields(self) -> None:
        info = QueryDefinitionOptionsInfo(
            filter_labels=["instance", "job"],
            group_labels=["instance"],
        )
        assert info.filter_labels == ["instance", "job"]
        assert info.group_labels == ["instance"]

    def test_creation_with_empty_lists(self) -> None:
        info = QueryDefinitionOptionsInfo(filter_labels=[], group_labels=[])
        assert info.filter_labels == []
        assert info.group_labels == []

    def test_creation_from_dict(self) -> None:
        info = QueryDefinitionOptionsInfo.model_validate({
            "filter_labels": ["env"],
            "group_labels": ["env", "region"],
        })
        assert info.filter_labels == ["env"]
        assert info.group_labels == ["env", "region"]

    def test_model_dump_json(self) -> None:
        info = QueryDefinitionOptionsInfo(
            filter_labels=["host"],
            group_labels=["host", "service"],
        )
        data = json.loads(info.model_dump_json())
        assert data["filter_labels"] == ["host"]
        assert data["group_labels"] == ["host", "service"]

    def test_round_trip_serialization(self) -> None:
        info = QueryDefinitionOptionsInfo(
            filter_labels=["instance", "job"],
            group_labels=["instance"],
        )
        json_str = info.model_dump_json()
        restored = QueryDefinitionOptionsInfo.model_validate_json(json_str)
        assert restored.filter_labels == ["instance", "job"]
        assert restored.group_labels == ["instance"]


class TestMetricLabelEntryInfo:
    """Tests for MetricLabelEntryInfo sub-model."""

    def test_creation_with_all_fields(self) -> None:
        entry = MetricLabelEntryInfo(key="instance", value="localhost:9090")
        assert entry.key == "instance"
        assert entry.value == "localhost:9090"

    def test_creation_from_dict(self) -> None:
        entry = MetricLabelEntryInfo.model_validate({"key": "job", "value": "prometheus"})
        assert entry.key == "job"
        assert entry.value == "prometheus"

    def test_model_dump_json(self) -> None:
        entry = MetricLabelEntryInfo(key="env", value="production")
        data = json.loads(entry.model_dump_json())
        assert data["key"] == "env"
        assert data["value"] == "production"

    def test_round_trip_serialization(self) -> None:
        entry = MetricLabelEntryInfo(key="region", value="us-east-1")
        json_str = entry.model_dump_json()
        restored = MetricLabelEntryInfo.model_validate_json(json_str)
        assert restored.key == "region"
        assert restored.value == "us-east-1"


class TestMetricValueInfo:
    """Tests for MetricValueInfo sub-model."""

    def test_creation_with_all_fields(self) -> None:
        info = MetricValueInfo(timestamp=1700000000.0, value="42.5")
        assert info.timestamp == 1700000000.0
        assert info.value == "42.5"

    def test_creation_from_dict(self) -> None:
        info = MetricValueInfo.model_validate({"timestamp": 1700000001.5, "value": "100"})
        assert info.timestamp == 1700000001.5
        assert info.value == "100"

    def test_model_dump_json(self) -> None:
        info = MetricValueInfo(timestamp=1700000000.0, value="0.001")
        data = json.loads(info.model_dump_json())
        assert data["timestamp"] == 1700000000.0
        assert data["value"] == "0.001"

    def test_round_trip_serialization(self) -> None:
        info = MetricValueInfo(timestamp=1700000099.9, value="3.14")
        json_str = info.model_dump_json()
        restored = MetricValueInfo.model_validate_json(json_str)
        assert restored.timestamp == 1700000099.9
        assert restored.value == "3.14"

    def test_value_as_string_preserves_precision(self) -> None:
        info = MetricValueInfo(timestamp=1700000000.0, value="1.234567890123456789")
        assert info.value == "1.234567890123456789"
