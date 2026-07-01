"""Unit tests for runtime_variant_preset request DTO validation."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    CreateRuntimeVariantPresetInput,
    UpdateRuntimeVariantPresetInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
)


class TestCreateRuntimeVariantPresetInputFlagValidation:
    """Tests for flag + preset_target validation on CreateRuntimeVariantPresetInput."""

    @pytest.fixture
    def base_fields(self) -> dict[str, Any]:
        return {
            "runtime_variant_id": uuid4(),
            "name": "test-preset",
            "key": "--flag",
        }

    def test_flag_with_args_is_valid(self, base_fields: dict[str, Any]) -> None:
        result = CreateRuntimeVariantPresetInput(
            **base_fields,
            value_type=PresetValueType.FLAG,
            preset_target=PresetTarget.ARGS,
        )
        assert result.value_type == PresetValueType.FLAG
        assert result.preset_target == PresetTarget.ARGS

    def test_flag_with_env_is_rejected(self, base_fields: dict[str, Any]) -> None:
        with pytest.raises(ValidationError, match="flag"):
            CreateRuntimeVariantPresetInput(
                **base_fields,
                value_type=PresetValueType.FLAG,
                preset_target=PresetTarget.ENV,
            )

    def test_bool_with_env_is_valid(self, base_fields: dict[str, Any]) -> None:
        result = CreateRuntimeVariantPresetInput(
            **base_fields,
            value_type=PresetValueType.BOOL,
            preset_target=PresetTarget.ENV,
        )
        assert result.value_type == PresetValueType.BOOL
        assert result.preset_target == PresetTarget.ENV


class TestUpdateRuntimeVariantPresetInputFlagValidation:
    """Tests for flag + preset_target validation on UpdateRuntimeVariantPresetInput."""

    @pytest.fixture
    def preset_id(self) -> UUID:
        return uuid4()

    def test_flag_with_env_is_rejected(self, preset_id: UUID) -> None:
        with pytest.raises(ValidationError, match="flag"):
            UpdateRuntimeVariantPresetInput(
                id=preset_id,
                value_type=PresetValueType.FLAG,
                preset_target=PresetTarget.ENV,
            )

    def test_flag_without_preset_target_is_valid(self, preset_id: UUID) -> None:
        """When preset_target is not provided, DTO cannot validate (needs DB state)."""
        result = UpdateRuntimeVariantPresetInput(
            id=preset_id,
            value_type=PresetValueType.FLAG,
        )
        assert result.value_type == PresetValueType.FLAG
        assert result.preset_target is None

    def test_flag_with_args_is_valid(self, preset_id: UUID) -> None:
        result = UpdateRuntimeVariantPresetInput(
            id=preset_id,
            value_type=PresetValueType.FLAG,
            preset_target=PresetTarget.ARGS,
        )
        assert result.value_type == PresetValueType.FLAG
