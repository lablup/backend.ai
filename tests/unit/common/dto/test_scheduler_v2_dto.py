"""Unit tests for v2 scheduler (compute-schedule) DTOs."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.dto.manager.v2.scheduler.request import (
    ComputeScheduleInput,
    ComputeScheduleKernelResourceInput,
)
from ai.backend.common.dto.manager.v2.scheduler.response import (
    ComputeSchedulePayload,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed


class TestComputeScheduleInput:
    def test_valid_input_round_trips_through_json(self) -> None:
        original = ComputeScheduleInput.model_validate({
            "kernels": [
                {
                    "image_id": str(uuid.uuid4()),
                    "resources": [
                        {"resource_type": "cpu", "quantity": "2"},
                        {"resource_type": "mem", "quantity": "1073741824"},
                    ],
                }
            ],
            "cluster_mode": "single-node",
            "resource_group_id": str(uuid.uuid4()),
        })
        restored = ComputeScheduleInput.model_validate(original.model_dump(mode="json"))
        assert restored == original

    def test_image_id_defaults_to_none(self) -> None:
        kernel = ComputeScheduleKernelResourceInput.model_validate({
            "resources": [{"resource_type": "cpu", "quantity": "1"}],
        })
        assert kernel.image_id is None

    def test_missing_resource_group_id_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ComputeScheduleInput.model_validate({
                "kernels": [],
                "cluster_mode": "single-node",
            })


class TestComputeSchedulePayload:
    def test_shortage_result_parses_reduction_as_decimal(self) -> None:
        payload = ComputeSchedulePayload.model_validate({
            "results": [
                {
                    "requested_slots": [{"resource_type": "cpu", "quantity": "10"}],
                    "requested_architecture": "x86_64",
                    "success": False,
                    "reason_hint": {
                        "required_reduction": [{"resource_type": "cpu", "quantity": "2"}],
                    },
                }
            ],
        })
        result = payload.results[0]
        assert result.success is False
        assert result.reason_hint is not None
        assert result.reason_hint.required_reduction is not None
        assert result.reason_hint.required_reduction[0].quantity == Decimal(2)

    def test_success_result_defaults_reason_hint_to_none(self) -> None:
        payload = ComputeSchedulePayload.model_validate({
            "results": [
                {
                    "requested_slots": [{"resource_type": "cpu", "quantity": "1"}],
                    "requested_architecture": "x86_64",
                    "success": True,
                }
            ],
        })
        assert payload.results[0].reason_hint is None
