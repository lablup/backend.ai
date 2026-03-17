"""Tests for ai.backend.common.dto.manager.v2.auto_scaling_rule.response module."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.auto_scaling_rule.response import (
    AutoScalingRuleNode,
    CreateAutoScalingRulePayload,
    DeleteAutoScalingRulePayload,
    GetAutoScalingRulePayload,
    SearchAutoScalingRulesPayload,
    UpdateAutoScalingRulePayload,
)
from ai.backend.common.types import AutoScalingMetricSource


def make_rule_node(**kwargs: object) -> AutoScalingRuleNode:
    """Helper to create a minimal valid AutoScalingRuleNode."""
    now = datetime.now(tz=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "model_deployment_id": uuid.uuid4(),
        "metric_source": AutoScalingMetricSource.KERNEL,
        "metric_name": "cpu_usage",
        "step_size": 1,
        "time_window": 60,
        "created_at": now,
        "last_triggered_at": now,
    }
    defaults.update(kwargs)
    return AutoScalingRuleNode(**defaults)  # type: ignore[arg-type]


class TestAutoScalingRuleNodeCreation:
    """Tests for AutoScalingRuleNode model creation."""

    def test_creation_with_minimal_fields(self) -> None:
        node = make_rule_node()
        assert node.min_threshold is None
        assert node.max_threshold is None
        assert node.min_replicas is None
        assert node.max_replicas is None

    def test_creation_with_all_fields(self) -> None:
        rule_id = uuid.uuid4()
        dep_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = AutoScalingRuleNode(
            id=rule_id,
            model_deployment_id=dep_id,
            metric_source=AutoScalingMetricSource.INFERENCE_FRAMEWORK,
            metric_name="request_rate",
            min_threshold=Decimal("0.1"),
            max_threshold=Decimal("0.9"),
            step_size=2,
            time_window=120,
            min_replicas=1,
            max_replicas=10,
            created_at=now,
            last_triggered_at=now,
        )
        assert node.id == rule_id
        assert node.model_deployment_id == dep_id
        assert node.metric_source == AutoScalingMetricSource.INFERENCE_FRAMEWORK
        assert node.min_threshold == Decimal("0.1")
        assert node.max_threshold == Decimal("0.9")
        assert node.min_replicas == 1
        assert node.max_replicas == 10

    def test_all_12_fields_present(self) -> None:
        node = make_rule_node(
            min_threshold=Decimal("0.1"),
            max_threshold=Decimal("0.9"),
            min_replicas=1,
            max_replicas=5,
        )
        # Verify all 12 fields from the plan
        assert hasattr(node, "id")
        assert hasattr(node, "model_deployment_id")
        assert hasattr(node, "metric_source")
        assert hasattr(node, "metric_name")
        assert hasattr(node, "min_threshold")
        assert hasattr(node, "max_threshold")
        assert hasattr(node, "step_size")
        assert hasattr(node, "time_window")
        assert hasattr(node, "min_replicas")
        assert hasattr(node, "max_replicas")
        assert hasattr(node, "created_at")
        assert hasattr(node, "last_triggered_at")

    def test_metric_source_kernel(self) -> None:
        node = make_rule_node(metric_source=AutoScalingMetricSource.KERNEL)
        assert node.metric_source == AutoScalingMetricSource.KERNEL

    def test_metric_source_inference_framework(self) -> None:
        node = make_rule_node(metric_source=AutoScalingMetricSource.INFERENCE_FRAMEWORK)
        assert node.metric_source == AutoScalingMetricSource.INFERENCE_FRAMEWORK

    def test_decimal_threshold_precision(self) -> None:
        node = make_rule_node(
            min_threshold=Decimal("0.25"),
            max_threshold=Decimal("0.75"),
        )
        assert node.min_threshold == Decimal("0.25")
        assert node.max_threshold == Decimal("0.75")


class TestAutoScalingRuleNodeRoundTrip:
    """Tests for AutoScalingRuleNode serialization round-trip."""

    def test_round_trip_minimal_fields(self) -> None:
        node = make_rule_node()
        json_str = node.model_dump_json()
        restored = AutoScalingRuleNode.model_validate_json(json_str)
        assert restored.id == node.id
        assert restored.model_deployment_id == node.model_deployment_id
        assert restored.metric_source == node.metric_source
        assert restored.step_size == node.step_size
        assert restored.time_window == node.time_window

    def test_round_trip_preserves_decimal_values(self) -> None:
        node = make_rule_node(
            min_threshold=Decimal("0.12345"),
            max_threshold=Decimal("9.99999"),
        )
        json_str = node.model_dump_json()
        restored = AutoScalingRuleNode.model_validate_json(json_str)
        assert restored.min_threshold == Decimal("0.12345")
        assert restored.max_threshold == Decimal("9.99999")

    def test_round_trip_null_thresholds(self) -> None:
        node = make_rule_node()
        json_str = node.model_dump_json()
        restored = AutoScalingRuleNode.model_validate_json(json_str)
        assert restored.min_threshold is None
        assert restored.max_threshold is None
        assert restored.min_replicas is None
        assert restored.max_replicas is None


class TestCreateAutoScalingRulePayload:
    """Tests for CreateAutoScalingRulePayload model."""

    def test_creation(self) -> None:
        node = make_rule_node()
        payload = CreateAutoScalingRulePayload(rule=node)
        assert payload.rule.id == node.id

    def test_round_trip_serialization(self) -> None:
        node = make_rule_node()
        payload = CreateAutoScalingRulePayload(rule=node)
        json_str = payload.model_dump_json()
        restored = CreateAutoScalingRulePayload.model_validate_json(json_str)
        assert restored.rule.id == node.id
        assert restored.rule.metric_source == node.metric_source


class TestGetAutoScalingRulePayload:
    """Tests for GetAutoScalingRulePayload model."""

    def test_creation(self) -> None:
        node = make_rule_node()
        payload = GetAutoScalingRulePayload(rule=node)
        assert payload.rule.id == node.id

    def test_round_trip_serialization(self) -> None:
        node = make_rule_node()
        payload = GetAutoScalingRulePayload(rule=node)
        json_str = payload.model_dump_json()
        restored = GetAutoScalingRulePayload.model_validate_json(json_str)
        assert restored.rule.id == node.id


class TestSearchAutoScalingRulesPayload:
    """Tests for SearchAutoScalingRulesPayload model."""

    def test_creation_with_items(self) -> None:
        node = make_rule_node()
        pagination = PaginationInfo(total=1, offset=0, limit=50)
        payload = SearchAutoScalingRulesPayload(items=[node], pagination=pagination)
        assert len(payload.items) == 1
        assert payload.pagination.total == 1

    def test_empty_items(self) -> None:
        pagination = PaginationInfo(total=0, offset=0, limit=50)
        payload = SearchAutoScalingRulesPayload(items=[], pagination=pagination)
        assert payload.items == []

    def test_round_trip_serialization(self) -> None:
        node = make_rule_node()
        pagination = PaginationInfo(total=1, offset=0, limit=50)
        payload = SearchAutoScalingRulesPayload(items=[node], pagination=pagination)
        json_str = payload.model_dump_json()
        restored = SearchAutoScalingRulesPayload.model_validate_json(json_str)
        assert len(restored.items) == 1
        assert restored.items[0].id == node.id
        assert restored.pagination.total == 1


class TestUpdateAutoScalingRulePayload:
    """Tests for UpdateAutoScalingRulePayload model."""

    def test_creation(self) -> None:
        node = make_rule_node()
        payload = UpdateAutoScalingRulePayload(rule=node)
        assert payload.rule.id == node.id

    def test_round_trip_serialization(self) -> None:
        node = make_rule_node(min_threshold=Decimal("0.5"))
        payload = UpdateAutoScalingRulePayload(rule=node)
        json_str = payload.model_dump_json()
        restored = UpdateAutoScalingRulePayload.model_validate_json(json_str)
        assert restored.rule.id == node.id
        assert restored.rule.min_threshold == Decimal("0.5")


class TestDeleteAutoScalingRulePayload:
    """Tests for DeleteAutoScalingRulePayload model."""

    def test_creation(self) -> None:
        rule_id = uuid.uuid4()
        payload = DeleteAutoScalingRulePayload(id=rule_id)
        assert payload.id == rule_id

    def test_id_is_uuid_instance(self) -> None:
        rule_id = uuid.uuid4()
        payload = DeleteAutoScalingRulePayload(id=rule_id)
        assert isinstance(payload.id, uuid.UUID)

    def test_creation_from_uuid_string(self) -> None:
        rule_id = uuid.uuid4()
        payload = DeleteAutoScalingRulePayload.model_validate({"id": str(rule_id)})
        assert payload.id == rule_id

    def test_contains_only_id(self) -> None:
        rule_id = uuid.uuid4()
        payload = DeleteAutoScalingRulePayload(id=rule_id)
        data = payload.model_dump()
        assert set(data.keys()) == {"id"}

    def test_round_trip_serialization(self) -> None:
        rule_id = uuid.uuid4()
        payload = DeleteAutoScalingRulePayload(id=rule_id)
        json_str = payload.model_dump_json()
        restored = DeleteAutoScalingRulePayload.model_validate_json(json_str)
        assert restored.id == rule_id
