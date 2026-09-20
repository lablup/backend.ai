"""Runs the public membership backfill against a real database and reads the graph rows
back."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.config import DefaultModelDefinition
from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import (
    ContainerRegistryEntityType,
    ContainerRegistryID,
)
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.image import ImageEntityType, ImageID
from ai.backend.common.data.entity.resource_preset import (
    ResourcePresetEntityType,
    ResourcePresetID,
)
from ai.backend.common.data.entity.runtime_variant import (
    RuntimeVariantEntityType,
    RuntimeVariantID,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.alembic.versions import (
    f1c47b92e3a6_backfill_public_membership as revision,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_revision_preset.row import (
    DeploymentRevisionPresetRow,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    ProjectRow,
    ContainerRegistryRow,
    ImageRow,
    ResourcePresetRow,
    ResourceSlotTypeRow,
    LoginClientTypeRow,
    PrometheusQueryPresetCategoryRow,
    PrometheusQueryPresetRow,
    RuntimeVariantRow,
    RuntimeVariantPresetRow,
    DeploymentRevisionPresetRow,
]


@dataclass
class _Seeded:
    """The nodes of the rows seeded, split by whether they belong in `public`."""

    public: set[VirtualEntityID] = field(default_factory=set)
    private: set[VirtualEntityID] = field(default_factory=set)


@pytest.fixture
async def db(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(global_entity_ids, _TABLES):
        yield global_entity_ids


async def _add_node(
    db: ExtendedAsyncSAEngine, entity_type: EntityType, entity_id: uuid.UUID
) -> VirtualEntityID:
    async with db.begin_session() as session:
        node = VirtualEntityRow(entity_type=entity_type, entity_id=entity_id)
        session.add(node)
        await session.flush()
        return node.id


async def _add_registry(
    db: ExtendedAsyncSAEngine, *, is_global: bool | None
) -> ContainerRegistryID:
    """``None`` writes the column NULL, which the row class no longer allows and rows
    written before this revision can hold."""
    registry_id = ContainerRegistryID(uuid.uuid4())
    name = f"registry-{registry_id.hex[:8]}"
    async with db.begin_session() as session:
        await session.execute(
            sa.insert(ContainerRegistryRow).values(
                id=registry_id,
                url=f"https://{name}",
                registry_name=name,
                type=ContainerRegistryType.DOCKER,
                project="stable",
                is_global=is_global,
            )
        )
    return registry_id


async def _add_image(db: ExtendedAsyncSAEngine, registry_id: ContainerRegistryID) -> ImageID:
    tag = uuid.uuid4().hex[:8]
    async with db.begin_session() as session:
        row = ImageRow(
            name=f"registry/stable/python:{tag}",
            image="python",
            tag=tag,
            registry="registry",
            registry_id=registry_id,
            project="stable",
            architecture="x86_64",
            config_digest=f"sha256:{uuid.uuid4().hex}",
            size_bytes=1000,
            type=ImageType.COMPUTE,
            status=ImageStatus.ALIVE,
            accelerators=None,
            labels={},
            resources={},
        )
        session.add(row)
        await session.flush()
        return ImageID(row.id)


async def _add_preset(
    db: ExtendedAsyncSAEngine, *, resource_group_name: str | None
) -> ResourcePresetID:
    preset_id = ResourcePresetID(uuid.uuid4())
    async with db.begin_session() as session:
        session.add(
            ResourcePresetRow(
                id=preset_id,
                name=f"preset-{preset_id.hex[:8]}",
                resource_slots=ResourceSlot({"cpu": "1", "mem": "1G"}),
                scaling_group_name=resource_group_name,
            )
        )
    return preset_id


async def _add_runtime_variant(db: ExtendedAsyncSAEngine) -> RuntimeVariantID:
    variant_id = RuntimeVariantID(uuid.uuid4())
    async with db.begin_session() as session:
        session.add(
            RuntimeVariantRow(
                id=variant_id,
                name=f"variant-{variant_id.hex[:8]}",
                default_model_definition=DefaultModelDefinition(),
            )
        )
    return variant_id


@pytest.fixture
async def seeded(db: ExtendedAsyncSAEngine) -> _Seeded:
    """One row of each shape the backfill reaches, and the counterpart it must leave
    alone: a registry that is not global, its image, and a preset bound to a resource
    group."""
    seeded = _Seeded()

    variant_id = await _add_runtime_variant(db)
    seeded.public.add(await _add_node(db, RuntimeVariantEntityType(), variant_id))

    global_registry = await _add_registry(db, is_global=True)
    seeded.public.add(await _add_node(db, ContainerRegistryEntityType(), global_registry))
    for _ in range(2):
        image_id = await _add_image(db, global_registry)
        seeded.public.add(await _add_node(db, ImageEntityType(), image_id))

    project_registry = await _add_registry(db, is_global=False)
    seeded.private.add(await _add_node(db, ContainerRegistryEntityType(), project_registry))
    private_image = await _add_image(db, project_registry)
    seeded.private.add(await _add_node(db, ImageEntityType(), private_image))

    open_preset = await _add_preset(db, resource_group_name=None)
    seeded.public.add(await _add_node(db, ResourcePresetEntityType(), open_preset))
    bound_preset = await _add_preset(db, resource_group_name="some-group")
    seeded.private.add(await _add_node(db, ResourcePresetEntityType(), bound_preset))

    return seeded


async def _public_members(db: ExtendedAsyncSAEngine) -> set[VirtualEntityID]:
    """The nodes `public` owns and governs, counted only where it does both."""
    public_node_id = sa.select(VirtualEntityRow.id).where(
        VirtualEntityRow.entity_type == "global",
        VirtualEntityRow.entity_id == global_entity_id(GlobalEntityName.PUBLIC),
    )
    async with db.begin_readonly_session() as session:
        public_node = (await session.scalars(public_node_id)).one()
        owned = set(
            (
                await session.scalars(
                    sa.select(EntityMembershipRow.member_entity_id).where(
                        EntityMembershipRow.virtual_entity_id == public_node,
                        EntityMembershipRow.capped.is_(False),
                    )
                )
            ).all()
        )
        governed = set(
            (
                await session.scalars(
                    sa.select(ScopeBindingRow.virtual_entity_id).where(
                        ScopeBindingRow.scope_entity_id == public_node,
                        ScopeBindingRow.permission_cap.is_(None),
                    )
                )
            ).all()
        )
    assert owned == governed
    return owned


async def _upgrade(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(revision.add_public_edges)


async def _downgrade(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(revision.remove_public_edges)


class TestSettleIsGlobal:
    """The column the registration reads is settled before the backfill: a row left
    NULL is not global."""

    @pytest.fixture
    async def nullable_is_global(self, db: ExtendedAsyncSAEngine) -> None:
        """The column as it stood before this revision. The ORM already declares it
        NOT NULL, so the pre-migration shape has to be restored to seed a NULL."""
        async with db.begin() as conn:
            await conn.execute(
                sa.text("ALTER TABLE container_registries ALTER COLUMN is_global DROP NOT NULL")
            )

    async def test_a_registry_left_null_becomes_not_global(
        self, db: ExtendedAsyncSAEngine, nullable_is_global: None
    ) -> None:
        registry_id = await _add_registry(db, is_global=None)

        async with db.begin() as conn:
            await conn.run_sync(revision.settle_is_global)

        async with db.begin_readonly_session() as session:
            settled = await session.scalar(
                sa.select(ContainerRegistryRow.is_global).where(
                    ContainerRegistryRow.id == registry_id
                )
            )
        assert settled is False

    async def test_the_values_already_written_are_left_alone(
        self, db: ExtendedAsyncSAEngine, nullable_is_global: None
    ) -> None:
        global_registry = await _add_registry(db, is_global=True)
        project_registry = await _add_registry(db, is_global=False)

        async with db.begin() as conn:
            await conn.run_sync(revision.settle_is_global)

        async with db.begin_readonly_session() as session:
            rows = (
                await session.execute(
                    sa.select(ContainerRegistryRow.id, ContainerRegistryRow.is_global).where(
                        ContainerRegistryRow.id.in_([global_registry, project_registry])
                    )
                )
            ).all()
        assert {row.id: row.is_global for row in rows} == {
            global_registry: True,
            project_registry: False,
        }


class TestBackfillPublicMembership:
    async def test_the_rows_that_read_as_public_gain_the_edges(
        self, db: ExtendedAsyncSAEngine, seeded: _Seeded
    ) -> None:
        await _upgrade(db)

        members = await _public_members(db)
        assert seeded.public <= members

    async def test_a_project_registry_its_image_and_a_bound_preset_stay_out(
        self, db: ExtendedAsyncSAEngine, seeded: _Seeded
    ) -> None:
        await _upgrade(db)

        members = await _public_members(db)
        assert not (seeded.private & members)

    async def test_running_it_twice_leaves_the_same_edges(
        self, db: ExtendedAsyncSAEngine, seeded: _Seeded
    ) -> None:
        await _upgrade(db)
        once = await _public_members(db)

        await _upgrade(db)

        assert await _public_members(db) == once

    async def test_the_downgrade_takes_back_what_it_wrote(
        self, db: ExtendedAsyncSAEngine, seeded: _Seeded
    ) -> None:
        before = await _public_members(db)
        await _upgrade(db)

        await _downgrade(db)

        assert await _public_members(db) == before
