"""Component tests for deployment revision preset v2 CRUD.

Test matrix:
  - Search: returns results
  - Create: creates preset with resource_slots, resource_opts, environ
  - Get: retrieves by ID
  - Update: modifies description and rank
  - Delete: removes preset
  - Duplicate name: returns 409 conflict
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    CreateDeploymentRevisionPresetInput,
    DeploymentRevisionPresetFilter,
    ResourceOptsEntryInput,
    SearchDeploymentRevisionPresetsInput,
    UpdateDeploymentRevisionPresetInput,
)


@asynccontextmanager
async def _runtime_variant(db_engine: SAEngine) -> AsyncIterator[RuntimeVariantID]:
    """Insert a runtime variant and clean up its presets and itself on exit."""
    variant_id = RuntimeVariantID(uuid.uuid4())
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.text(
                "INSERT INTO runtime_variants (id, name, description) VALUES (:id, :name, :desc)"
            ).bindparams(
                id=variant_id, name=f"test-variant-{variant_id.hex[:8]}", desc="Test variant"
            )
        )
    try:
        yield variant_id
    finally:
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.text(
                    "DELETE FROM deployment_revision_presets WHERE runtime_variant = :id"
                ).bindparams(id=variant_id)
            )
            await conn.execute(
                sa.text("DELETE FROM runtime_variants WHERE id = :id").bindparams(id=variant_id)
            )


@pytest.fixture()
async def runtime_variant_id(
    db_engine: SAEngine, database_fixture: None
) -> AsyncIterator[RuntimeVariantID]:
    """Create a runtime variant for testing."""
    async with _runtime_variant(db_engine) as variant_id:
        yield variant_id


@pytest.fixture()
async def other_runtime_variant_id(
    db_engine: SAEngine, database_fixture: None
) -> AsyncIterator[RuntimeVariantID]:
    """Create a second runtime variant to move a preset into."""
    async with _runtime_variant(db_engine) as variant_id:
        yield variant_id


class TestDeploymentRevisionPresetCRUD:
    async def test_create_and_get(
        self,
        admin_v2_registry: V2ClientRegistry,
        runtime_variant_id: uuid.UUID,
    ) -> None:
        create_result = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="test-preset",
                description="Test preset",
                image_id=uuid.uuid4(),
                resource_slots=[
                    ResourceSlotEntryInput(resource_type="cpu", quantity="4"),
                    ResourceSlotEntryInput(resource_type="mem", quantity="8g"),
                ],
                resource_opts=[ResourceOptsEntryInput(name="shmem", value="1g")],
                cluster_mode="single-node",
                cluster_size=1,
            )
        )
        preset = create_result.preset
        assert preset.name == "test-preset"
        assert preset.rank == 100
        assert len(preset.resource.resource_opts) == 1

        get_result = await admin_v2_registry.deployment_revision_preset.get(preset.id)
        assert get_result.id == preset.id
        assert get_result.name == "test-preset"

        await admin_v2_registry.deployment_revision_preset.delete(preset.id)

    async def test_search_with_filter(
        self,
        admin_v2_registry: V2ClientRegistry,
        runtime_variant_id: uuid.UUID,
    ) -> None:
        create_result = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="search-test-preset",
                image_id=uuid.uuid4(),
            )
        )
        preset_id = create_result.preset.id

        result = await admin_v2_registry.deployment_revision_preset.search(
            SearchDeploymentRevisionPresetsInput(
                filter=DeploymentRevisionPresetFilter(
                    runtime_variant_id=runtime_variant_id,
                ),
                limit=10,
            )
        )
        assert result.total_count >= 1
        ids = [item.id for item in result.items]
        assert preset_id in ids

        await admin_v2_registry.deployment_revision_preset.delete(preset_id)

    async def test_update(
        self,
        admin_v2_registry: V2ClientRegistry,
        runtime_variant_id: uuid.UUID,
    ) -> None:
        create_result = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="update-test-preset",
                description="Before",
                image_id=uuid.uuid4(),
            )
        )
        preset_id = create_result.preset.id

        update_result = await admin_v2_registry.deployment_revision_preset.update(
            preset_id,
            UpdateDeploymentRevisionPresetInput(
                id=preset_id,
                description="After",
                rank=50,
            ),
        )
        assert update_result.preset.description == "After"
        assert update_result.preset.rank == 50

        await admin_v2_registry.deployment_revision_preset.delete(preset_id)

    async def test_update_runtime_variant(
        self,
        admin_v2_registry: V2ClientRegistry,
        runtime_variant_id: RuntimeVariantID,
        other_runtime_variant_id: RuntimeVariantID,
    ) -> None:
        create_result = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="variant-move-preset",
                image_id=ImageID(uuid.uuid4()),
                resource_slots=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
                cluster_mode="single-node",
                cluster_size=1,
                replica_count=1,
                deployment_strategy=DeploymentStrategyInput(type=DeploymentStrategy.ROLLING),
            )
        )
        preset_id = create_result.preset.id
        assert create_result.preset.runtime_variant_id == runtime_variant_id

        update_result = await admin_v2_registry.deployment_revision_preset.update(
            preset_id,
            UpdateDeploymentRevisionPresetInput(
                id=preset_id,
                runtime_variant_id=other_runtime_variant_id,
            ),
        )
        assert update_result.preset.runtime_variant_id == other_runtime_variant_id

        get_result = await admin_v2_registry.deployment_revision_preset.get(preset_id)
        assert get_result.runtime_variant_id == other_runtime_variant_id

    async def test_delete(
        self,
        admin_v2_registry: V2ClientRegistry,
        runtime_variant_id: uuid.UUID,
    ) -> None:
        create_result = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="delete-test-preset",
                image_id=uuid.uuid4(),
            )
        )
        preset_id = create_result.preset.id

        delete_result = await admin_v2_registry.deployment_revision_preset.delete(preset_id)
        assert delete_result.id == preset_id

    async def test_duplicate_name_conflict(
        self,
        admin_v2_registry: V2ClientRegistry,
        runtime_variant_id: uuid.UUID,
    ) -> None:
        create_result = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="dup-test-preset",
                image_id=uuid.uuid4(),
            )
        )
        preset_id = create_result.preset.id

        try:
            with pytest.raises(BackendAPIError) as exc_info:
                await admin_v2_registry.deployment_revision_preset.create(
                    CreateDeploymentRevisionPresetInput(
                        runtime_variant_id=runtime_variant_id,
                        name="dup-test-preset",
                        image_id=uuid.uuid4(),
                    )
                )
            assert exc_info.value.args[0] == 409
        finally:
            await admin_v2_registry.deployment_revision_preset.delete(preset_id)

    async def test_rank_auto_increment(
        self,
        admin_v2_registry: V2ClientRegistry,
        runtime_variant_id: uuid.UUID,
    ) -> None:
        r1 = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="rank-test-1",
                image_id=uuid.uuid4(),
            )
        )
        r2 = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="rank-test-2",
                image_id=uuid.uuid4(),
            )
        )
        assert r1.preset.rank == 100
        assert r2.preset.rank == 200

        await admin_v2_registry.deployment_revision_preset.delete(r2.preset.id)
        await admin_v2_registry.deployment_revision_preset.delete(r1.preset.id)
