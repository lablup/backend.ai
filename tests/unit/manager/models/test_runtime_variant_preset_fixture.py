"""Tests for runtime variant preset fixture loading."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.manager.errors.resource import DataTransformationFailed
from ai.backend.manager.models.base import populate_fixture
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


class TestRuntimeVariantPresetFixture:
    """Regression tests for runtime_variant_presets fixture population."""

    @pytest.fixture
    async def db_engine(
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
    def preset_fixture_data(self) -> dict[str, list[dict[str, object]]]:
        return {
            "runtime_variants": [
                {
                    "name": "vllm",
                    "description": "vLLM",
                }
            ],
            "runtime_variant_presets": [
                {
                    "runtime_variant_name": "vllm",
                    "name": "dtype",
                    "description": "Model weight dtype.",
                    "rank": 100,
                    "preset_target": "args",
                    "value_type": "str",
                    "default_value": "auto",
                    "key": "--dtype",
                    "category": "model_loading",
                    "ui_type": "select",
                    "display_name": "DType",
                    "ui_option": {
                        "ui_type": "select",
                        "choices": {
                            "items": [
                                {"value": "auto", "label": "Auto"},
                                {"value": "float16", "label": "Float16"},
                            ]
                        },
                    },
                }
            ],
        }

    async def test_populate_preset_resolves_variant_name(
        self,
        db_engine: ExtendedAsyncSAEngine,
        preset_fixture_data: dict[str, list[dict[str, object]]],
    ) -> None:
        await populate_fixture(db_engine, preset_fixture_data)

        async with db_engine.begin_session() as db_sess:
            runtime_variant = await db_sess.scalar(
                sa.select(RuntimeVariantRow).where(RuntimeVariantRow.name == "vllm")
            )
            preset = await db_sess.scalar(
                sa.select(RuntimeVariantPresetRow).where(RuntimeVariantPresetRow.name == "dtype")
            )

        assert runtime_variant is not None
        assert preset is not None
        assert preset.runtime_variant == runtime_variant.id
        assert preset.ui_option is not None
        assert preset.ui_option.ui_type.value == "select"
        assert preset.ui_option.choices is not None
        assert preset.ui_option.choices.items[0].value == "auto"

    async def test_populate_preset_keeps_explicit_variant_id(
        self,
        db_engine: ExtendedAsyncSAEngine,
    ) -> None:
        variant_id = uuid.uuid4()
        fixture_data: dict[str, list[dict[str, object]]] = {
            "runtime_variants": [
                {
                    "id": variant_id,
                    "name": "vllm",
                    "description": "vLLM",
                }
            ],
            "runtime_variant_presets": [
                {
                    "runtime_variant": variant_id,
                    "runtime_variant_name": "nonexistent",
                    "name": "dtype",
                    "description": "Model weight dtype.",
                    "rank": 100,
                    "preset_target": "args",
                    "value_type": "str",
                    "default_value": "auto",
                    "key": "--dtype",
                }
            ],
        }

        await populate_fixture(db_engine, fixture_data)

        async with db_engine.begin_session() as db_sess:
            preset = await db_sess.scalar(
                sa.select(RuntimeVariantPresetRow).where(RuntimeVariantPresetRow.name == "dtype")
            )

        assert preset is not None
        assert preset.runtime_variant == variant_id

    @pytest.fixture
    def preset_fixture_data_with_unknown_variant(
        self,
    ) -> dict[str, list[dict[str, object]]]:
        return {
            "runtime_variant_presets": [
                {
                    "runtime_variant_name": "nonexistent",
                    "name": "dtype",
                    "description": "Model weight dtype.",
                    "rank": 100,
                    "preset_target": "args",
                    "value_type": "str",
                    "default_value": "auto",
                    "key": "--dtype",
                }
            ],
        }

    async def test_populate_preset_raises_for_unknown_variant_name(
        self,
        db_engine: ExtendedAsyncSAEngine,
        preset_fixture_data_with_unknown_variant: dict[str, list[dict[str, object]]],
    ) -> None:
        with pytest.raises(DataTransformationFailed):
            await populate_fixture(db_engine, preset_fixture_data_with_unknown_variant)
