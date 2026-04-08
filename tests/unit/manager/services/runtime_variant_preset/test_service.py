"""Mock-based unit tests for RuntimeVariantPresetService update validation."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
)
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.runtime_variant_preset.repository import (
    RuntimeVariantPresetRepository,
)
from ai.backend.manager.repositories.runtime_variant_preset.updaters import (
    RuntimeVariantPresetUpdaterSpec,
)
from ai.backend.manager.services.runtime_variant_preset.actions.update import (
    UpdateRuntimeVariantPresetAction,
)
from ai.backend.manager.services.runtime_variant_preset.service import (
    RuntimeVariantPresetService,
)
from ai.backend.manager.types import OptionalState


class TestRuntimeVariantPresetServiceUpdateValidation:
    """Tests for flag + env cross-field validation in service update."""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=RuntimeVariantPresetRepository)

    @pytest.fixture
    def service(self, mock_repository: MagicMock) -> RuntimeVariantPresetService:
        return RuntimeVariantPresetService(repository=mock_repository)

    @pytest.fixture
    def preset_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def flaging_preset_env(self, preset_id: uuid.UUID) -> RuntimeVariantPresetData:
        """Existing preset with preset_target=env."""
        return RuntimeVariantPresetData(
            id=preset_id,
            runtime_variant_id=uuid.uuid4(),
            name="test",
            description=None,
            rank=0,
            preset_target=PresetTarget.ENV,
            value_type=PresetValueType.STR,
            default_value=None,
            key="MY_VAR",
            category=None,
            ui_type=None,
            display_name=None,
            ui_option=None,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=None,
        )

    @pytest.fixture
    def flaging_preset_args(self, preset_id: uuid.UUID) -> RuntimeVariantPresetData:
        """Existing preset with preset_target=args."""
        return RuntimeVariantPresetData(
            id=preset_id,
            runtime_variant_id=uuid.uuid4(),
            name="test",
            description=None,
            rank=0,
            preset_target=PresetTarget.ARGS,
            value_type=PresetValueType.STR,
            default_value=None,
            key="--flag",
            category=None,
            ui_type=None,
            display_name=None,
            ui_option=None,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=None,
        )

    async def test_change_value_type_to_flag_with_flaging_env_is_rejected(
        self,
        service: RuntimeVariantPresetService,
        mock_repository: MagicMock,
        preset_id: uuid.UUID,
        flaging_preset_env: RuntimeVariantPresetData,
    ) -> None:
        mock_repository.get_by_id = AsyncMock(return_value=flaging_preset_env)
        spec = RuntimeVariantPresetUpdaterSpec(
            value_type=OptionalState.update(PresetValueType.FLAG),
        )
        updater: Updater[RuntimeVariantPresetRow] = Updater(spec=spec, pk_value=preset_id)
        action = UpdateRuntimeVariantPresetAction(id=preset_id, updater=updater)

        with pytest.raises(InvalidAPIParameters, match="flag"):
            await service.update(action)

    async def test_change_value_type_to_flag_with_flaging_args_is_valid(
        self,
        service: RuntimeVariantPresetService,
        mock_repository: MagicMock,
        preset_id: uuid.UUID,
        flaging_preset_args: RuntimeVariantPresetData,
    ) -> None:
        updated_data = RuntimeVariantPresetData(
            id=preset_id,
            runtime_variant_id=flaging_preset_args.runtime_variant_id,
            name="test",
            description=None,
            rank=0,
            preset_target=PresetTarget.ARGS,
            value_type=PresetValueType.FLAG,
            default_value=None,
            key="--flag",
            category=None,
            ui_type=None,
            display_name=None,
            ui_option=None,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 2, tzinfo=UTC),
        )
        mock_repository.get_by_id = AsyncMock(return_value=flaging_preset_args)
        mock_repository.update = AsyncMock(return_value=updated_data)
        spec = RuntimeVariantPresetUpdaterSpec(
            value_type=OptionalState.update(PresetValueType.FLAG),
        )
        updater: Updater[RuntimeVariantPresetRow] = Updater(spec=spec, pk_value=preset_id)
        action = UpdateRuntimeVariantPresetAction(id=preset_id, updater=updater)

        result = await service.update(action)
        assert result.preset.value_type == PresetValueType.FLAG

    async def test_change_preset_target_to_env_with_flaging_flag_is_rejected(
        self,
        service: RuntimeVariantPresetService,
        mock_repository: MagicMock,
        preset_id: uuid.UUID,
    ) -> None:
        flaging = RuntimeVariantPresetData(
            id=preset_id,
            runtime_variant_id=uuid.uuid4(),
            name="test",
            description=None,
            rank=0,
            preset_target=PresetTarget.ARGS,
            value_type=PresetValueType.FLAG,
            default_value=None,
            key="--flag",
            category=None,
            ui_type=None,
            display_name=None,
            ui_option=None,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=None,
        )
        mock_repository.get_by_id = AsyncMock(return_value=flaging)
        spec = RuntimeVariantPresetUpdaterSpec(
            preset_target=OptionalState.update(PresetTarget.ENV),
        )
        updater: Updater[RuntimeVariantPresetRow] = Updater(spec=spec, pk_value=preset_id)
        action = UpdateRuntimeVariantPresetAction(id=preset_id, updater=updater)

        with pytest.raises(InvalidAPIParameters, match="flag"):
            await service.update(action)
