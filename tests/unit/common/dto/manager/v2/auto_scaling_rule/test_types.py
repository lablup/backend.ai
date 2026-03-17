"""Tests for ai.backend.common.dto.manager.v2.auto_scaling_rule.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.auto_scaling_rule.types import (
    AutoScalingMetricSource as ExportedAutoScalingMetricSource,
)
from ai.backend.common.dto.manager.v2.auto_scaling_rule.types import (
    AutoScalingRuleOrderField,
    OrderDirection,
)
from ai.backend.common.types import AutoScalingMetricSource


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_enum_members_count(self) -> None:
        assert len(list(OrderDirection)) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestAutoScalingRuleOrderField:
    """Tests for AutoScalingRuleOrderField enum."""

    def test_created_at_value(self) -> None:
        assert AutoScalingRuleOrderField.CREATED_AT.value == "created_at"

    def test_enum_members_count(self) -> None:
        assert len(list(AutoScalingRuleOrderField)) == 1

    def test_from_string_created_at(self) -> None:
        assert AutoScalingRuleOrderField("created_at") is AutoScalingRuleOrderField.CREATED_AT


class TestAutoScalingMetricSourceReExport:
    """Tests verifying AutoScalingMetricSource is properly re-exported."""

    def test_exported_is_same_object(self) -> None:
        assert ExportedAutoScalingMetricSource is AutoScalingMetricSource

    def test_kernel_value(self) -> None:
        assert ExportedAutoScalingMetricSource.KERNEL.value == "kernel"

    def test_inference_framework_value(self) -> None:
        assert ExportedAutoScalingMetricSource.INFERENCE_FRAMEWORK.value == "inference_framework"

    def test_enum_members_count(self) -> None:
        assert len(list(ExportedAutoScalingMetricSource)) == 2

    def test_case_insensitive_lookup_kernel(self) -> None:
        # CIStrEnum is case-insensitive
        assert ExportedAutoScalingMetricSource("KERNEL") is ExportedAutoScalingMetricSource.KERNEL

    def test_case_insensitive_lookup_inference_framework(self) -> None:
        assert (
            ExportedAutoScalingMetricSource("INFERENCE_FRAMEWORK")
            is ExportedAutoScalingMetricSource.INFERENCE_FRAMEWORK
        )
