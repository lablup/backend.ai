"""Tests for ScalingGroupOpts Pydantic model serialization and validation."""

from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.types import (
    AgentSelectionStrategy,
    PreemptionMode,
    PreemptionOrder,
    SessionTypes,
)
from ai.backend.manager.models.scaling_group.row import PreemptionConfig, ScalingGroupOpts


class TestScalingGroupOptsDefaults:
    """Test default instantiation of ScalingGroupOpts."""

    def test_create_with_no_args(self) -> None:
        opts = ScalingGroupOpts()
        assert opts.allowed_session_types == [
            SessionTypes.INTERACTIVE,
            SessionTypes.BATCH,
            SessionTypes.INFERENCE,
        ]
        assert opts.pending_timeout == timedelta(seconds=0)
        assert opts.config == {}
        assert opts.agent_selection_strategy == AgentSelectionStrategy.DISPERSED
        assert opts.agent_selector_config == {}
        assert opts.enforce_spreading_endpoint_replica is False
        assert opts.allow_fractional_resource_fragmentation is True
        assert opts.route_cleanup_target_statuses == ["unhealthy"]

    def test_frozen_model_raises_on_mutation(self) -> None:
        opts = ScalingGroupOpts()
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            opts.pending_timeout = timedelta(seconds=30)  # type: ignore[misc]


class TestScalingGroupOptsRoundtrip:
    """Test roundtrip serialization: model_dump(mode='json') → model_validate()."""

    def test_roundtrip_defaults(self) -> None:
        original = ScalingGroupOpts()
        dumped = original.model_dump(mode="json")
        restored = ScalingGroupOpts.model_validate(dumped)
        assert restored == original

    def test_roundtrip_custom_values(self) -> None:
        original = ScalingGroupOpts(
            allowed_session_types=[SessionTypes.BATCH],
            pending_timeout=timedelta(seconds=120),
            config={"key": "value"},
            agent_selection_strategy=AgentSelectionStrategy.CONCENTRATED,
            agent_selector_config={"max_agents": 2},
            enforce_spreading_endpoint_replica=True,
            allow_fractional_resource_fragmentation=False,
            route_cleanup_target_statuses=["unhealthy", "degraded"],
        )
        dumped = original.model_dump(mode="json")
        restored = ScalingGroupOpts.model_validate(dumped)
        assert restored == original

    def test_model_dump_json_mode_types(self) -> None:
        """Verify model_dump(mode='json') produces JSON-compatible types."""
        opts = ScalingGroupOpts(
            allowed_session_types=[SessionTypes.INTERACTIVE, SessionTypes.BATCH],
            pending_timeout=timedelta(seconds=60),
            agent_selection_strategy=AgentSelectionStrategy.DISPERSED,
        )
        dumped = opts.model_dump(mode="json")

        # pending_timeout → float seconds
        assert isinstance(dumped["pending_timeout"], float)
        assert dumped["pending_timeout"] == 60.0

        # allowed_session_types → list of strings
        assert isinstance(dumped["allowed_session_types"], list)
        assert all(isinstance(v, str) for v in dumped["allowed_session_types"])
        assert "interactive" in dumped["allowed_session_types"]
        assert "batch" in dumped["allowed_session_types"]

        # agent_selection_strategy → string
        assert isinstance(dumped["agent_selection_strategy"], str)
        assert dumped["agent_selection_strategy"] == AgentSelectionStrategy.DISPERSED.value


class TestScalingGroupOptsPendingTimeout:
    """Test pending_timeout field validator and serializer."""

    def test_validate_from_int(self) -> None:
        opts = ScalingGroupOpts(pending_timeout=30)  # type: ignore[arg-type]
        assert opts.pending_timeout == timedelta(seconds=30)

    def test_validate_from_float(self) -> None:
        opts = ScalingGroupOpts(pending_timeout=45.5)  # type: ignore[arg-type]
        assert opts.pending_timeout == timedelta(seconds=45.5)

    def test_validate_from_timedelta(self) -> None:
        td = timedelta(minutes=2)
        opts = ScalingGroupOpts(pending_timeout=td)
        assert opts.pending_timeout == td

    def test_validate_from_zero(self) -> None:
        opts = ScalingGroupOpts(pending_timeout=0)  # type: ignore[arg-type]
        assert opts.pending_timeout == timedelta(seconds=0)

    def test_serialize_to_seconds(self) -> None:
        opts = ScalingGroupOpts(pending_timeout=timedelta(minutes=1, seconds=30))
        dumped = opts.model_dump(mode="json")
        assert dumped["pending_timeout"] == 90.0

    def test_validate_invalid_type_raises(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            ScalingGroupOpts(pending_timeout="not-a-number")  # type: ignore[arg-type]


class TestScalingGroupOptsAllowedSessionTypes:
    """Test allowed_session_types field validator and serializer."""

    def test_validate_from_string_list(self) -> None:
        opts = ScalingGroupOpts.model_validate({
            "allowed_session_types": ["interactive", "batch"],
        })
        assert opts.allowed_session_types == [SessionTypes.INTERACTIVE, SessionTypes.BATCH]

    def test_validate_from_enum_list(self) -> None:
        opts = ScalingGroupOpts(allowed_session_types=[SessionTypes.INFERENCE])
        assert opts.allowed_session_types == [SessionTypes.INFERENCE]

    def test_validate_invalid_session_type_raises(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ScalingGroupOpts.model_validate({"allowed_session_types": ["not_a_valid_type"]})

    def test_validate_non_list_raises(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ScalingGroupOpts.model_validate({"allowed_session_types": "interactive"})

    def test_serialize_to_string_list(self) -> None:
        opts = ScalingGroupOpts(
            allowed_session_types=[SessionTypes.INTERACTIVE, SessionTypes.INFERENCE]
        )
        dumped = opts.model_dump(mode="json")
        assert dumped["allowed_session_types"] == [
            SessionTypes.INTERACTIVE.value,
            SessionTypes.INFERENCE.value,
        ]


class TestScalingGroupOptsAgentSelectionStrategy:
    """Test agent_selection_strategy field serializer."""

    def test_serialize_to_string(self) -> None:
        opts = ScalingGroupOpts(agent_selection_strategy=AgentSelectionStrategy.CONCENTRATED)
        dumped = opts.model_dump(mode="json")
        assert dumped["agent_selection_strategy"] == AgentSelectionStrategy.CONCENTRATED.value

    def test_validate_from_string(self) -> None:
        opts = ScalingGroupOpts.model_validate({
            "agent_selection_strategy": AgentSelectionStrategy.CONCENTRATED.value,
        })
        assert opts.agent_selection_strategy == AgentSelectionStrategy.CONCENTRATED


class TestScalingGroupOptsBackwardCompatibility:
    """Test backward compatibility: existing JSON data (without new fields) loads correctly."""

    def test_empty_dict_uses_all_defaults(self) -> None:
        opts = ScalingGroupOpts.model_validate({})
        assert opts.allowed_session_types == [
            SessionTypes.INTERACTIVE,
            SessionTypes.BATCH,
            SessionTypes.INFERENCE,
        ]
        assert opts.pending_timeout == timedelta(seconds=0)
        assert opts.config == {}
        assert opts.agent_selection_strategy == AgentSelectionStrategy.DISPERSED
        assert opts.agent_selector_config == {}
        assert opts.enforce_spreading_endpoint_replica is False
        assert opts.allow_fractional_resource_fragmentation is True
        assert opts.route_cleanup_target_statuses == ["unhealthy"]

    def test_partial_legacy_data(self) -> None:
        """Legacy JSON with only some fields sets defaults for missing ones."""
        legacy_data = {
            "allowed_session_types": ["interactive", "batch"],
            "pending_timeout": 0,
        }
        opts = ScalingGroupOpts.model_validate(legacy_data)
        assert opts.allowed_session_types == [SessionTypes.INTERACTIVE, SessionTypes.BATCH]
        assert opts.pending_timeout == timedelta(seconds=0)
        # New fields get defaults
        assert opts.config == {}
        assert opts.agent_selection_strategy == AgentSelectionStrategy.DISPERSED
        assert opts.enforce_spreading_endpoint_replica is False
        assert opts.allow_fractional_resource_fragmentation is True


class TestPreemptionConfig:
    """Test PreemptionConfig defaults, serialization, and backward compatibility."""

    def test_defaults(self) -> None:
        config = PreemptionConfig()
        assert config.enabled is False
        assert config.preemptible_priority == 5
        assert config.order == PreemptionOrder.OLDEST
        assert config.mode == PreemptionMode.TERMINATE
        assert config.preemption_min_runtime == timedelta(seconds=0)

    def test_scaling_group_opts_default_preemption(self) -> None:
        opts = ScalingGroupOpts()
        assert opts.preemption == PreemptionConfig()
        assert opts.preemption.enabled is False
        assert opts.preemption.preemption_min_runtime == timedelta(seconds=0)

    def test_serialize_json_mode_types(self) -> None:
        config = PreemptionConfig(
            enabled=True,
            preemptible_priority=3,
            order=PreemptionOrder.NEWEST,
            mode=PreemptionMode.RESCHEDULE,
            preemption_min_runtime=timedelta(seconds=300),
        )
        dumped = config.model_dump(mode="json")
        assert dumped["enabled"] is True
        assert dumped["preemptible_priority"] == 3
        assert dumped["order"] == PreemptionOrder.NEWEST.value
        assert dumped["mode"] == PreemptionMode.RESCHEDULE.value
        # preemption_min_runtime → float seconds
        assert isinstance(dumped["preemption_min_runtime"], float)
        assert dumped["preemption_min_runtime"] == 300.0

    def test_validate_min_runtime_from_int(self) -> None:
        config = PreemptionConfig.model_validate({"preemption_min_runtime": 120})
        assert config.preemption_min_runtime == timedelta(seconds=120)

    def test_validate_min_runtime_from_float(self) -> None:
        config = PreemptionConfig.model_validate({"preemption_min_runtime": 90.5})
        assert config.preemption_min_runtime == timedelta(seconds=90.5)

    def test_roundtrip_custom_values(self) -> None:
        original = PreemptionConfig(
            enabled=True,
            preemptible_priority=1,
            order=PreemptionOrder.NEWEST,
            mode=PreemptionMode.RESCHEDULE,
            preemption_min_runtime=timedelta(minutes=5),
        )
        restored = PreemptionConfig.model_validate(original.model_dump(mode="json"))
        assert restored == original

    def test_backward_compat_missing_new_keys(self) -> None:
        """Legacy preemption JSON without enabled/preemption_min_runtime loads defaults."""
        legacy_data = {
            "preemptible_priority": 5,
            "order": "oldest",
            "mode": "terminate",
        }
        config = PreemptionConfig.model_validate(legacy_data)
        assert config.enabled is False
        assert config.preemption_min_runtime == timedelta(seconds=0)
        assert config.preemptible_priority == 5

    def test_backward_compat_via_scaling_group_opts(self) -> None:
        """A legacy scheduler_opts JSONB row without the new preemption keys loads defaults."""
        legacy_opts = {
            "preemption": {
                "preemptible_priority": 3,
                "order": "newest",
                "mode": "reschedule",
            },
        }
        opts = ScalingGroupOpts.model_validate(legacy_opts)
        assert opts.preemption.enabled is False
        assert opts.preemption.preemption_min_runtime == timedelta(seconds=0)
        assert opts.preemption.preemptible_priority == 3
        assert opts.preemption.order == PreemptionOrder.NEWEST
        assert opts.preemption.mode == PreemptionMode.RESCHEDULE

    def test_scaling_group_opts_roundtrip_with_preemption(self) -> None:
        original = ScalingGroupOpts(
            preemption=PreemptionConfig(
                enabled=True,
                preemption_min_runtime=timedelta(seconds=300),
            ),
        )
        restored = ScalingGroupOpts.model_validate(original.model_dump(mode="json"))
        assert restored.preemption.enabled is True
        assert restored.preemption.preemption_min_runtime == timedelta(seconds=300)
