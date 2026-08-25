"""Repository tests for RuntimeVariantPreset with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
)
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset.creators import (
    RANK_GAP,
    RuntimeVariantPresetCreator,
)
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.runtime_variant_preset.repository import (
    RuntimeVariantPresetRepository,
)
from ai.backend.testutils.db import with_tables


class TestRuntimeVariantPresetRepositoryFlag:
    """Tests for creating and retrieving presets with value_type='flag'."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                VirtualScopeRow,
                EntityMembershipRow,
                ScopeBindingRow,
                EntityLabelRow,
                RoleRow,
                PermissionRow,
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
    def preset_ops(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> OpsRepository[RuntimeVariantPresetData]:
        return OpsRepository(V2DBOpsProvider(db_with_cleanup))

    @pytest.fixture
    def repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> RuntimeVariantPresetRepository:
        return RuntimeVariantPresetRepository(db=db_with_cleanup)

    async def test_create_flag_preset_and_get_by_id(
        self,
        preset_ops: OpsRepository[RuntimeVariantPresetData],
        repository: RuntimeVariantPresetRepository,
        runtime_variant_id: uuid.UUID,
    ) -> None:
        creator = RuntimeVariantPresetCreator(
            runtime_variant_id=RuntimeVariantID(runtime_variant_id),
            name="enable-verbose",
            description="Enable verbose logging",
            preset_target=PresetTarget.ARGS,
            value_type=PresetValueType.FLAG,
            default_value="true",
            key="--verbose",
            required=False,
            category=None,
            display_name=None,
            ui_option=None,
        )
        created = await preset_ops.create_global_entity(creator)

        assert created.value_type == PresetValueType.FLAG
        assert created.preset_target == PresetTarget.ARGS
        assert created.key == "--verbose"

        fetched = await repository.get_by_id(created.id)
        assert fetched.value_type == PresetValueType.FLAG
        assert fetched.preset_target == PresetTarget.ARGS
        assert fetched.default_value == "true"

    async def test_rank_advances_by_gap_within_a_variant(
        self,
        preset_ops: OpsRepository[RuntimeVariantPresetData],
        runtime_variant_id: uuid.UUID,
    ) -> None:
        def creator_named(name: str) -> RuntimeVariantPresetCreator:
            return RuntimeVariantPresetCreator(
                runtime_variant_id=RuntimeVariantID(runtime_variant_id),
                name=name,
                description=None,
                preset_target=PresetTarget.ENV,
                value_type=PresetValueType.STR,
                default_value=None,
                key=name.upper(),
                required=False,
                category=None,
                display_name=None,
                ui_option=None,
            )

        first = await preset_ops.create_global_entity(creator_named("first"))
        second = await preset_ops.create_global_entity(creator_named("second"))

        assert first.rank == RANK_GAP
        assert second.rank == RANK_GAP * 2
