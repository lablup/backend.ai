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


class TestCreateRuntimeVariantPresetInputDefaultValueValidation:
    """Regression tests for value_type-aware default_value validation on create."""

    @pytest.mark.parametrize(
        "default_value",
        [pytest.param("42", id="valid"), pytest.param(None, id="omitted")],
    )
    def test_default_value_is_valid(self, default_value: str | None) -> None:
        result = CreateRuntimeVariantPresetInput(
            runtime_variant_id=uuid4(),
            name="test-preset",
            preset_target=PresetTarget.ENV,
            key="MY_VAR",
            value_type=PresetValueType.INT,
            default_value=default_value,
        )
        assert result.default_value == default_value

    def test_default_value_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="not a valid"):
            CreateRuntimeVariantPresetInput(
                runtime_variant_id=uuid4(),
                name="test-preset",
                preset_target=PresetTarget.ENV,
                key="MY_VAR",
                value_type=PresetValueType.INT,
                default_value="abc",
            )


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


class TestUpdateRuntimeVariantPresetInputDefaultValueValidation:
    """Tests for value_type-aware default_value validation on UpdateRuntimeVariantPresetInput."""

    @pytest.fixture
    def preset_id(self) -> UUID:
        return uuid4()

    def test_default_value_is_rejected(self, preset_id: UUID) -> None:
        with pytest.raises(ValidationError, match="not a valid"):
            UpdateRuntimeVariantPresetInput(
                id=preset_id, value_type=PresetValueType.INT, default_value="abc"
            )

    @pytest.mark.parametrize(
        ("value_type", "default_value"),
        [
            pytest.param(PresetValueType.INT, "42", id="matching"),
            pytest.param(None, "abc", id="value_type_missing"),
            pytest.param(PresetValueType.INT, None, id="default_value_missing"),
        ],
    )
    def test_default_value_is_valid(
        self, preset_id: UUID, value_type: PresetValueType | None, default_value: str | None
    ) -> None:
        """DTO can only statically validate when both fields are present in the same
        request; a partial update is left to the service, which has DB state."""
        result = UpdateRuntimeVariantPresetInput(
            id=preset_id, value_type=value_type, default_value=default_value
        )
        assert result.id == preset_id
