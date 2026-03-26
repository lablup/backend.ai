"""Tests for ai.backend.common.dto.manager.v2.auto_scaling_rule.request module."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
    AutoScalingRuleFilter,
    AutoScalingRuleOrder,
    CreateAutoScalingRuleInput,
    DeleteAutoScalingRuleInput,
    SearchAutoScalingRulesInput,
    UpdateAutoScalingRuleInput,
)
from ai.backend.common.dto.manager.v2.auto_scaling_rule.types import (
    AutoScalingRuleOrderField,
    OrderDirection,
)
from ai.backend.common.types import AutoScalingMetricSource


class TestCreateAutoScalingRuleInput:
    """Tests for CreateAutoScalingRuleInput model creation and validation."""

    def test_valid_creation_minimal(self) -> None:
        dep_id = uuid.uuid4()
        req = CreateAutoScalingRuleInput(
            model_deployment_id=dep_id,
            metric_source=AutoScalingMetricSource.KERNEL,
            metric_name="cpu_usage",
            step_size=1,
            time_window=60,
        )
        assert req.model_deployment_id == dep_id
        assert req.metric_source == AutoScalingMetricSource.KERNEL
        assert req.metric_name == "cpu_usage"
        assert req.step_size == 1
        assert req.time_window == 60
        assert req.min_threshold is None
        assert req.max_threshold is None
        assert req.min_replicas is None
        assert req.max_replicas is None

    def test_valid_creation_with_all_fields(self) -> None:
        dep_id = uuid.uuid4()
        req = CreateAutoScalingRuleInput(
            model_deployment_id=dep_id,
            metric_source=AutoScalingMetricSource.INFERENCE_FRAMEWORK,
            metric_name="request_rate",
            min_threshold=Decimal("0.1"),
            max_threshold=Decimal("0.9"),
            step_size=2,
            time_window=120,
            min_replicas=1,
            max_replicas=10,
        )
        assert req.min_threshold == Decimal("0.1")
        assert req.max_threshold == Decimal("0.9")
        assert req.min_replicas == 1
        assert req.max_replicas == 10

    def test_step_size_minimum_valid(self) -> None:
        req = CreateAutoScalingRuleInput(
            model_deployment_id=uuid.uuid4(),
            metric_source=AutoScalingMetricSource.KERNEL,
            metric_name="cpu",
            step_size=1,
            time_window=60,
        )
        assert req.step_size == 1

    def test_step_size_below_minimum_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateAutoScalingRuleInput(
                model_deployment_id=uuid.uuid4(),
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="cpu",
                step_size=0,
                time_window=60,
            )

    def test_time_window_minimum_valid(self) -> None:
        req = CreateAutoScalingRuleInput(
            model_deployment_id=uuid.uuid4(),
            metric_source=AutoScalingMetricSource.KERNEL,
            metric_name="cpu",
            step_size=1,
            time_window=1,
        )
        assert req.time_window == 1

    def test_time_window_below_minimum_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateAutoScalingRuleInput(
                model_deployment_id=uuid.uuid4(),
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="cpu",
                step_size=1,
                time_window=0,
            )

    def test_min_replicas_zero_is_valid(self) -> None:
        req = CreateAutoScalingRuleInput(
            model_deployment_id=uuid.uuid4(),
            metric_source=AutoScalingMetricSource.KERNEL,
            metric_name="cpu",
            step_size=1,
            time_window=60,
            min_replicas=0,
        )
        assert req.min_replicas == 0

    def test_min_replicas_negative_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateAutoScalingRuleInput(
                model_deployment_id=uuid.uuid4(),
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="cpu",
                step_size=1,
                time_window=60,
                min_replicas=-1,
            )

    def test_max_replicas_minimum_one_valid(self) -> None:
        req = CreateAutoScalingRuleInput(
            model_deployment_id=uuid.uuid4(),
            metric_source=AutoScalingMetricSource.KERNEL,
            metric_name="cpu",
            step_size=1,
            time_window=60,
            max_replicas=1,
        )
        assert req.max_replicas == 1

    def test_max_replicas_zero_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateAutoScalingRuleInput(
                model_deployment_id=uuid.uuid4(),
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="cpu",
                step_size=1,
                time_window=60,
                max_replicas=0,
            )

    def test_empty_metric_name_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateAutoScalingRuleInput(
                model_deployment_id=uuid.uuid4(),
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="",
                step_size=1,
                time_window=60,
            )

    def test_round_trip_serialization(self) -> None:
        dep_id = uuid.uuid4()
        req = CreateAutoScalingRuleInput(
            model_deployment_id=dep_id,
            metric_source=AutoScalingMetricSource.KERNEL,
            metric_name="cpu_usage",
            min_threshold=Decimal("0.5"),
            max_threshold=Decimal("0.9"),
            step_size=2,
            time_window=60,
        )
        json_str = req.model_dump_json()
        restored = CreateAutoScalingRuleInput.model_validate_json(json_str)
        assert restored.model_deployment_id == dep_id
        assert restored.metric_source == AutoScalingMetricSource.KERNEL
        assert restored.min_threshold == Decimal("0.5")
        assert restored.max_threshold == Decimal("0.9")


class TestUpdateAutoScalingRuleInput:
    """Tests for UpdateAutoScalingRuleInput SENTINEL handling."""

    @pytest.fixture
    def rule_id(self) -> uuid.UUID:
        return uuid.UUID("00000000-0000-0000-0000-000000000001")

    def test_default_sentinel_fields(self, rule_id: uuid.UUID) -> None:
        req = UpdateAutoScalingRuleInput(id=rule_id)
        assert req.min_threshold is SENTINEL
        assert isinstance(req.min_threshold, Sentinel)
        assert req.max_threshold is SENTINEL
        assert isinstance(req.max_threshold, Sentinel)
        assert req.min_replicas is SENTINEL
        assert isinstance(req.min_replicas, Sentinel)
        assert req.max_replicas is SENTINEL
        assert isinstance(req.max_replicas, Sentinel)

    def test_none_for_non_sentinel_fields_means_no_change(self, rule_id: uuid.UUID) -> None:
        req = UpdateAutoScalingRuleInput(id=rule_id)
        assert req.metric_source is None
        assert req.metric_name is None
        assert req.step_size is None
        assert req.time_window is None

    def test_set_min_threshold_to_none_clears_field(self, rule_id: uuid.UUID) -> None:
        req = UpdateAutoScalingRuleInput(id=rule_id, min_threshold=None)
        assert req.min_threshold is None

    def test_set_min_threshold_to_value(self, rule_id: uuid.UUID) -> None:
        req = UpdateAutoScalingRuleInput(id=rule_id, min_threshold=Decimal("0.3"))
        assert req.min_threshold == Decimal("0.3")

    def test_set_max_threshold_to_none_clears_field(self, rule_id: uuid.UUID) -> None:
        req = UpdateAutoScalingRuleInput(id=rule_id, max_threshold=None)
        assert req.max_threshold is None

    def test_set_min_replicas_to_none_clears_field(self, rule_id: uuid.UUID) -> None:
        req = UpdateAutoScalingRuleInput(id=rule_id, min_replicas=None)
        assert req.min_replicas is None

    def test_set_max_replicas_to_value(self, rule_id: uuid.UUID) -> None:
        req = UpdateAutoScalingRuleInput(id=rule_id, max_replicas=5)
        assert req.max_replicas == 5

    def test_update_metric_source(self, rule_id: uuid.UUID) -> None:
        req = UpdateAutoScalingRuleInput(
            id=rule_id, metric_source=AutoScalingMetricSource.INFERENCE_FRAMEWORK
        )
        assert req.metric_source == AutoScalingMetricSource.INFERENCE_FRAMEWORK

    def test_update_step_size(self, rule_id: uuid.UUID) -> None:
        req = UpdateAutoScalingRuleInput(id=rule_id, step_size=3)
        assert req.step_size == 3

    def test_round_trip_with_none_values(self, rule_id: uuid.UUID) -> None:
        req = UpdateAutoScalingRuleInput(
            id=rule_id,
            metric_source=None,
            metric_name=None,
            min_threshold=None,
            max_threshold=None,
            step_size=None,
            time_window=None,
            min_replicas=None,
            max_replicas=None,
        )
        json_str = req.model_dump_json()
        restored = UpdateAutoScalingRuleInput.model_validate_json(json_str)
        assert restored.metric_source is None
        assert restored.min_threshold is None
        assert restored.max_threshold is None
        assert restored.min_replicas is None
        assert restored.max_replicas is None

    def test_round_trip_with_decimal_threshold(self, rule_id: uuid.UUID) -> None:
        req = UpdateAutoScalingRuleInput(
            id=rule_id,
            min_threshold=Decimal("0.25"),
            max_threshold=Decimal("0.75"),
            step_size=None,
            time_window=None,
            min_replicas=None,
            max_replicas=None,
        )
        json_str = req.model_dump_json()
        restored = UpdateAutoScalingRuleInput.model_validate_json(json_str)
        assert restored.min_threshold == Decimal("0.25")
        assert restored.max_threshold == Decimal("0.75")


class TestDeleteAutoScalingRuleInput:
    """Tests for DeleteAutoScalingRuleInput model."""

    def test_valid_creation(self) -> None:
        rule_id = uuid.uuid4()
        req = DeleteAutoScalingRuleInput(id=rule_id)
        assert req.id == rule_id

    def test_valid_from_uuid_string(self) -> None:
        rule_id = uuid.uuid4()
        req = DeleteAutoScalingRuleInput.model_validate({"id": str(rule_id)})
        assert req.id == rule_id

    def test_invalid_uuid_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteAutoScalingRuleInput.model_validate({"id": "not-a-uuid"})

    def test_missing_id_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteAutoScalingRuleInput.model_validate({})

    def test_id_is_uuid_instance(self) -> None:
        rule_id = uuid.uuid4()
        req = DeleteAutoScalingRuleInput(id=rule_id)
        assert isinstance(req.id, uuid.UUID)

    def test_round_trip_serialization(self) -> None:
        rule_id = uuid.uuid4()
        req = DeleteAutoScalingRuleInput(id=rule_id)
        json_str = req.model_dump_json()
        restored = DeleteAutoScalingRuleInput.model_validate_json(json_str)
        assert restored.id == rule_id


class TestAutoScalingRuleFilter:
    """Tests for AutoScalingRuleFilter model."""

    def test_default_creation(self) -> None:
        f = AutoScalingRuleFilter()
        assert f.model_deployment_id is None

    def test_with_deployment_id(self) -> None:
        dep_id = uuid.uuid4()
        f = AutoScalingRuleFilter(model_deployment_id=dep_id)
        assert f.model_deployment_id == dep_id


class TestAutoScalingRuleOrder:
    """Tests for AutoScalingRuleOrder model."""

    def test_default_direction_is_asc(self) -> None:
        order = AutoScalingRuleOrder(field=AutoScalingRuleOrderField.CREATED_AT)
        assert order.direction == OrderDirection.ASC

    def test_explicit_desc_direction(self) -> None:
        order = AutoScalingRuleOrder(
            field=AutoScalingRuleOrderField.CREATED_AT, direction=OrderDirection.DESC
        )
        assert order.direction == OrderDirection.DESC


class TestSearchAutoScalingRulesInput:
    """Tests for SearchAutoScalingRulesInput model."""

    def test_default_creation(self) -> None:
        req = SearchAutoScalingRulesInput()
        assert req.filter is None
        assert req.order is None
        assert req.limit == 50
        assert req.offset == 0

    def test_limit_below_minimum_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchAutoScalingRulesInput(limit=0)

    def test_limit_above_maximum_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchAutoScalingRulesInput(limit=1001)

    def test_negative_offset_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchAutoScalingRulesInput(offset=-1)

    def test_with_filter(self) -> None:
        dep_id = uuid.uuid4()
        f = AutoScalingRuleFilter(model_deployment_id=dep_id)
        req = SearchAutoScalingRulesInput(filter=f)
        assert req.filter is not None
        assert req.filter.model_deployment_id == dep_id

    def test_round_trip_serialization(self) -> None:
        req = SearchAutoScalingRulesInput(limit=25, offset=50)
        json_str = req.model_dump_json()
        restored = SearchAutoScalingRulesInput.model_validate_json(json_str)
        assert restored.limit == 25
        assert restored.offset == 50
