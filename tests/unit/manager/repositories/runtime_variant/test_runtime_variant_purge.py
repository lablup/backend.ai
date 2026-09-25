"""Tests for the runtime variant purge that clears the variant's presets, against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantEntityType, RuntimeVariantID
from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetEntityType
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
)
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.models.runtime_variant.purgers import RuntimeVariantPurger
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset.creators import RuntimeVariantPresetCreator
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.runtime_variant.repository import RuntimeVariantRepository
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder


@pytest.fixture
async def database(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        global_entity_ids,
        [
            VirtualEntityRow,
            EntityMembershipRow,
            EntityMembershipCapRow,
            EntityMembershipFieldRow,
            ScopeBindingRow,
            EntityLabelRow,
            RoleRow,
            PermissionRow,
            DomainRow,
            UserResourcePolicyRow,
            UserRow,
            EntityShareRow,
            RuntimeVariantRow,
            RuntimeVariantPresetRow,
        ],
    ):
        yield global_entity_ids


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> RuntimeVariantRepository:
    return RuntimeVariantRepository(database, V2DBOpsProvider(database))


async def _add_variant(database: ExtendedAsyncSAEngine) -> RuntimeVariantID:
    variant_id = RuntimeVariantID(uuid.uuid4())
    async with database.begin_session() as sess:
        sess.add(
            RuntimeVariantRow(id=variant_id, name=f"variant-{variant_id.hex[:8]}", description=None)
        )
        await sess.flush()
        await VirtualEntitySeeder().provision(sess, RuntimeVariantEntityType(), variant_id)
    return variant_id


async def _add_preset(
    database: ExtendedAsyncSAEngine, variant_id: RuntimeVariantID, name: str
) -> RuntimeVariantPresetData:
    ops: OpsRepository[RuntimeVariantPresetData] = OpsRepository(V2DBOpsProvider(database))
    return await ops.create_entity(
        RuntimeVariantPresetCreator(
            runtime_variant_id=variant_id,
            name=name,
            description=None,
            preset_target=PresetTarget.ENV,
            value_type=PresetValueType.STR,
            default_value=None,
            key=name.upper(),
            required=False,
            added_version=None,
            deprecated_version=None,
            category=None,
            display_name=None,
            ui_option=None,
        )
    )


async def _preset_nodes(database: ExtendedAsyncSAEngine) -> set[uuid.UUID]:
    async with database.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(VirtualEntityRow.entity_id).where(
                VirtualEntityRow.entity_type == RuntimeVariantPresetEntityType()
            )
        )
        return set(rows.all())


async def _preset_ids(database: ExtendedAsyncSAEngine) -> set[uuid.UUID]:
    async with database.begin_readonly_session() as sess:
        return set((await sess.scalars(sa.select(RuntimeVariantPresetRow.id))).all())


class TestRuntimeVariantPurge:
    async def test_takes_its_presets_with_their_nodes_and_keeps_others(
        self, database: ExtendedAsyncSAEngine, repository: RuntimeVariantRepository
    ) -> None:
        purged_variant = await _add_variant(database)
        kept_variant = await _add_variant(database)
        await _add_preset(database, purged_variant, "purged")
        kept = await _add_preset(database, kept_variant, "kept")

        purged = await repository.purge(RuntimeVariantPurger(variant_id=purged_variant))

        assert purged.id == purged_variant
        assert await _preset_ids(database) == {kept.id}
        assert await _preset_nodes(database) == {kept.id}

    async def test_missing_variant_raises(self, repository: RuntimeVariantRepository) -> None:
        with pytest.raises(EntityNotFoundError):
            await repository.purge(RuntimeVariantPurger(variant_id=RuntimeVariantID(uuid.uuid4())))
