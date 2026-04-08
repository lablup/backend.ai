"""Repository tests for RuntimeVariantPreset with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
)
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.runtime_variant_preset.creators import (
    RuntimeVariantPresetCreatorSpec,
)
from ai.backend.manager.repositories.runtime_variant_preset.repository import (
    RuntimeVariantPresetRepository,
)
from ai.backend.testutils.db import with_tables


class TestRuntimeVariantPresetRepositoryFlag:
    """Tests for creating and retrieving presets with value_type='exist'."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                RuntimeVariantRow,
                RuntimeVariantPresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def runtime_variant_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[uuid.UUID, None]:
        variant_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                RuntimeVariantRow(
                    id=variant_id,
                    name=f"test-variant-{variant_id.hex[:8]}",
                    description=None,
                )
            )
            await db_sess.flush()
        yield variant_id

    @pytest.fixture
    def repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> RuntimeVariantPresetRepository:
        return RuntimeVariantPresetRepository(db=db_with_cleanup)

    async def test_create_exist_preset_and_get_by_id(
        self,
        repository: RuntimeVariantPresetRepository,
        runtime_variant_id: uuid.UUID,
    ) -> None:
        spec = RuntimeVariantPresetCreatorSpec(
            runtime_variant_id=runtime_variant_id,
            name="enable-verbose",
            description="Enable verbose logging",
            rank=0,
            preset_target=PresetTarget.ARGS,
            value_type=PresetValueType.FLAG,
            default_value="true",
            key="--verbose",
            category=None,
            ui_type=None,
            display_name=None,
            ui_option=None,
        )
        creator: Creator[RuntimeVariantPresetRow] = Creator(spec=spec)
        created = await repository.create(creator)

        assert created.value_type == PresetValueType.FLAG
        assert created.preset_target == PresetTarget.ARGS
        assert created.key == "--verbose"

        fetched = await repository.get_by_id(created.id)
        assert fetched.value_type == PresetValueType.FLAG
        assert fetched.preset_target == PresetTarget.ARGS
        assert fetched.default_value == "true"
