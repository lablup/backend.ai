"""Unit tests for ModelDeploymentAutoScalingRuleModifier.

These tests cover the update-path 3-state semantics for the auto scaling rule:

- ``SENTINEL``/``NOP``  → field is omitted from the update dict
- ``NULLIFY``            → nullable field is cleared to ``None`` in the dict
- ``UPDATE(v)``          → field is assigned ``v`` in the dict

Only the nullable DB columns (``min_threshold``, ``max_threshold``,
``min_replicas``, ``max_replicas``, ``prometheus_query_preset_id``) use
``TriState`` and therefore support NULLIFY. The non-nullable columns keep the
narrower ``OptionalState`` (NOP/UPDATE) semantics.

``apply_model_deployment_modifier`` is a trivial ``for k, v: setattr(self, k, v)``
over this dict, so validating ``fields_to_update()`` fully covers the behaviour
observable at the Row level.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from ai.backend.common.types import AutoScalingMetricSource
from ai.backend.manager.data.deployment.scale_modifier import (
    ModelDeploymentAutoScalingRuleModifier,
)
from ai.backend.manager.types import OptionalState, TriState


class TestModifierFieldsToUpdate:
    """fields_to_update() should honour NOP / UPDATE / NULLIFY per state."""

    def test_empty_modifier_produces_empty_dict(self) -> None:
        modifier = ModelDeploymentAutoScalingRuleModifier()
        assert modifier.fields_to_update() == {}

    def test_update_values_populate_dict(self) -> None:
        preset_id = uuid4()
        modifier = ModelDeploymentAutoScalingRuleModifier(
            metric_source=OptionalState.update(AutoScalingMetricSource.KERNEL),
            metric_name=OptionalState.update("cpu_util"),
            min_threshold=TriState.update(Decimal("10")),
            max_threshold=TriState.update(Decimal("90")),
            step_size=OptionalState.update(2),
            time_window=OptionalState.update(600),
            min_replicas=TriState.update(1),
            max_replicas=TriState.update(10),
            prometheus_query_preset_id=TriState.update(preset_id),
        )
        assert modifier.fields_to_update() == {
            "metric_source": AutoScalingMetricSource.KERNEL,
            "metric_name": "cpu_util",
            "min_threshold": Decimal("10"),
            "max_threshold": Decimal("90"),
            "step_size": 2,
            "cooldown_seconds": 600,
            "min_replicas": 1,
            "max_replicas": 10,
            "prometheus_query_preset_id": preset_id,
        }

    def test_nullify_produces_none_entries(self) -> None:
        modifier = ModelDeploymentAutoScalingRuleModifier(
            min_threshold=TriState[Decimal].nullify(),
            max_threshold=TriState[Decimal].nullify(),
            min_replicas=TriState[int].nullify(),
            max_replicas=TriState[int].nullify(),
            prometheus_query_preset_id=TriState.nullify(),
        )
        assert modifier.fields_to_update() == {
            "min_threshold": None,
            "max_threshold": None,
            "min_replicas": None,
            "max_replicas": None,
            "prometheus_query_preset_id": None,
        }

    def test_time_window_maps_to_cooldown_seconds_column(self) -> None:
        modifier = ModelDeploymentAutoScalingRuleModifier(
            time_window=OptionalState.update(42),
        )
        assert modifier.fields_to_update() == {"cooldown_seconds": 42}


class TestNullifyIsolation:
    """NULLIFY on nullable fields must not affect the non-nullable fields."""

    def test_nullify_on_nullable_fields_alone(self) -> None:
        modifier = ModelDeploymentAutoScalingRuleModifier(
            min_threshold=TriState[Decimal].nullify(),
            prometheus_query_preset_id=TriState.nullify(),
        )
        update = modifier.fields_to_update()

        assert update == {"min_threshold": None, "prometheus_query_preset_id": None}
        assert "metric_source" not in update
        assert "metric_name" not in update
        assert "step_size" not in update
        assert "cooldown_seconds" not in update

    def test_mixed_update_and_nullify(self) -> None:
        modifier = ModelDeploymentAutoScalingRuleModifier(
            metric_name=OptionalState.update("gpu_util"),
            min_threshold=TriState.update(Decimal("20")),
            max_threshold=TriState[Decimal].nullify(),
            min_replicas=TriState.update(2),
            max_replicas=TriState[int].nullify(),
        )

        assert modifier.fields_to_update() == {
            "metric_name": "gpu_util",
            "min_threshold": Decimal("20"),
            "max_threshold": None,
            "min_replicas": 2,
            "max_replicas": None,
        }
