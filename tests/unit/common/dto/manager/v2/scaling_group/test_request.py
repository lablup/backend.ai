"""Tests for ai.backend.common.dto.manager.v2.scaling_group.request module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.dto.manager.v2.scaling_group.request import (
    PreemptionConfigInput,
    UpdateScalingGroupInput,
)
from ai.backend.common.dto.manager.v2.scaling_group.types import (
    PreemptionMode,
    PreemptionOrder,
    SchedulerType,
)


class TestPreemptionConfigInput:
    """Tests for PreemptionConfigInput model creation and validation."""

    def test_defaults_are_valid(self) -> None:
        req = PreemptionConfigInput()
        assert req.preemptible_priority == 5
        assert req.order == PreemptionOrder.OLDEST
        assert req.mode == PreemptionMode.TERMINATE

    def test_valid_creation_with_all_fields(self) -> None:
        req = PreemptionConfigInput(
            preemptible_priority=3,
            order=PreemptionOrder.NEWEST,
            mode=PreemptionMode.RESCHEDULE,
        )
        assert req.preemptible_priority == 3
        assert req.order == PreemptionOrder.NEWEST
        assert req.mode == PreemptionMode.RESCHEDULE

    def test_min_priority_is_valid(self) -> None:
        req = PreemptionConfigInput(preemptible_priority=1)
        assert req.preemptible_priority == 1

    def test_max_priority_is_valid(self) -> None:
        req = PreemptionConfigInput(preemptible_priority=10)
        assert req.preemptible_priority == 10

    def test_priority_below_min_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            PreemptionConfigInput(preemptible_priority=0)

    def test_priority_above_max_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            PreemptionConfigInput(preemptible_priority=11)

    def test_round_trip(self) -> None:
        req = PreemptionConfigInput(
            preemptible_priority=7,
            order=PreemptionOrder.NEWEST,
            mode=PreemptionMode.RESCHEDULE,
        )
        json_data = req.model_dump_json()
        restored = PreemptionConfigInput.model_validate_json(json_data)
        assert restored.preemptible_priority == req.preemptible_priority
        assert restored.order == req.order
        assert restored.mode == req.mode


class TestUpdateScalingGroupInput:
    """Tests for UpdateScalingGroupInput model creation and validation."""

    def test_all_none_fields_is_valid(self) -> None:
        req = UpdateScalingGroupInput(
            is_active=None,
            is_public=None,
            use_host_network=None,
            scheduler=None,
            preemption_config=None,
        )
        assert req.is_active is None
        assert req.is_public is None

    def test_default_sentinel_fields(self) -> None:
        req = UpdateScalingGroupInput()
        assert req.description is SENTINEL
        assert isinstance(req.description, Sentinel)
        assert req.wsproxy_addr is SENTINEL
        assert req.wsproxy_api_token is SENTINEL

    def test_sentinel_description_signals_clear(self) -> None:
        req = UpdateScalingGroupInput(description=SENTINEL)
        assert req.description is SENTINEL

    def test_none_description_means_no_change(self) -> None:
        req = UpdateScalingGroupInput(description=None)
        assert req.description is None

    def test_string_description_update(self) -> None:
        req = UpdateScalingGroupInput(description="New description")
        assert req.description == "New description"

    def test_is_active_update(self) -> None:
        req = UpdateScalingGroupInput(is_active=True)
        assert req.is_active is True

    def test_scheduler_update(self) -> None:
        req = UpdateScalingGroupInput(scheduler=SchedulerType.DRF)
        assert req.scheduler == SchedulerType.DRF

    def test_nested_preemption_config(self) -> None:
        preemption = PreemptionConfigInput(preemptible_priority=3)
        req = UpdateScalingGroupInput(preemption_config=preemption)
        assert req.preemption_config is not None
        assert req.preemption_config.preemptible_priority == 3

    def test_round_trip_with_all_none(self) -> None:
        req = UpdateScalingGroupInput(
            is_active=None,
            is_public=None,
            description=None,
            wsproxy_addr=None,
            wsproxy_api_token=None,
            use_host_network=None,
            scheduler=None,
            preemption_config=None,
        )
        json_data = req.model_dump_json()
        restored = UpdateScalingGroupInput.model_validate_json(json_data)
        assert restored.is_active is None
        assert restored.description is None
