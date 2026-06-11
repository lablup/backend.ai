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

import pytest
import sqlalchemy as sa
from pydantic import ValidationError
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.query import UUIDFilter
from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.deployment.request import DeploymentStrategyInput
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    CreateDeploymentRevisionPresetInput,
    DeploymentRevisionPresetFilter,
    PresetModelConfigInput,
    PresetModelDefinitionInput,
    PresetModelServiceConfigInput,
    SearchDeploymentRevisionPresetsInput,
    UpdateDeploymentRevisionPresetInput,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import ResourceOptsEntryDTO
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID


@pytest.fixture()
async def runtime_variant_id(
    db_engine: SAEngine, database_fixture: None
) -> AsyncIterator[RuntimeVariantID]:
    """Create a runtime variant for testing."""
    variant_id = RuntimeVariantID(uuid.uuid4())
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.text(
                "INSERT INTO runtime_variants (id, name, description, default_model_definition)"
                " VALUES (:id, :name, :desc, CAST(:default_model_definition AS jsonb))"
            ).bindparams(
                id=variant_id,
                name=f"test-variant-{variant_id.hex[:8]}",
                desc="Test variant",
                default_model_definition="{}",
            )
        )
    yield variant_id
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.text(
                "DELETE FROM deployment_revision_presets WHERE runtime_variant = :id"
            ).bindparams(id=variant_id)
        )
        await conn.execute(
            sa.text("DELETE FROM runtime_variants WHERE id = :id").bindparams(id=variant_id)
        )


class TestDeploymentRevisionPresetCRUD:
    async def test_create_and_get(
        self,
        admin_v2_registry: V2ClientRegistry,
        runtime_variant_id: RuntimeVariantID,
    ) -> None:
        create_result = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="test-preset",
                description="Test preset",
                image_id=ImageID(uuid.uuid4()),
                resource_slots=[
                    ResourceSlotEntryInput(resource_type="cpu", quantity="4"),
                    ResourceSlotEntryInput(resource_type="mem", quantity="8g"),
                ],
                resource_opts=[ResourceOptsEntryDTO(name="shmem", value="1g")],
                cluster_mode="single-node",
                cluster_size=1,
                replica_count=1,
                deployment_strategy=DeploymentStrategyInput(type=DeploymentStrategy.ROLLING),
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
        runtime_variant_id: RuntimeVariantID,
    ) -> None:
        image_id = ImageID(uuid.uuid4())
        model_definition = PresetModelDefinitionInput(
            models=[
                PresetModelConfigInput(
                    name="llama",
                    model_path="/models/llama",
                    service=PresetModelServiceConfigInput(
                        port=8080,
                        start_command=["python", "server.py"],
                    ),
                ),
            ],
        )
        create_result = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="search-test-preset",
                image_id=image_id,
                model_definition=model_definition,
                resource_slots=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
                cluster_mode="single-node",
                cluster_size=1,
                replica_count=1,
                deployment_strategy=DeploymentStrategyInput(type=DeploymentStrategy.ROLLING),
            )
        )
        preset_id = create_result.preset.id

        result = await admin_v2_registry.deployment_revision_preset.search(
            SearchDeploymentRevisionPresetsInput(
                filter=DeploymentRevisionPresetFilter(
                    runtime_variant_id=UUIDFilter(equals=runtime_variant_id),
                ),
                limit=10,
            )
        )
        assert result.total_count >= 1
        matched = [item for item in result.items if item.id == preset_id]
        assert len(matched) == 1
        # BA-5931: nested execution.image_id and model_definition must round-trip.
        preset = matched[0]
        assert preset.execution.image_id == image_id
        assert preset.model_definition is not None
        assert len(preset.model_definition.models) == 1
        assert preset.model_definition.models[0].name == "llama"
        assert preset.model_definition.models[0].model_path == "/models/llama"

        await admin_v2_registry.deployment_revision_preset.delete(preset_id)

    async def test_create_with_empty_model_definition_models_rejected(
        self,
        runtime_variant_id: RuntimeVariantID,
    ) -> None:
        # An empty models list is rejected at the strict request-DTO boundary
        # (CREATE only) before any request is sent.
        with pytest.raises(ValidationError):
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="md-empty-preset",
                image_id=ImageID(uuid.uuid4()),
                model_definition=PresetModelDefinitionInput(models=[]),
                resource_slots=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
                cluster_mode="single-node",
                cluster_size=1,
                replica_count=1,
                deployment_strategy=DeploymentStrategyInput(type=DeploymentStrategy.ROLLING),
            )

    async def test_update(
        self,
        admin_v2_registry: V2ClientRegistry,
        runtime_variant_id: RuntimeVariantID,
    ) -> None:
        create_result = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="update-test-preset",
                description="Before",
                image_id=ImageID(uuid.uuid4()),
                resource_slots=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
                cluster_mode="single-node",
                cluster_size=1,
                replica_count=1,
                deployment_strategy=DeploymentStrategyInput(type=DeploymentStrategy.ROLLING),
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

    async def test_delete(
        self,
        admin_v2_registry: V2ClientRegistry,
        runtime_variant_id: RuntimeVariantID,
    ) -> None:
        create_result = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="delete-test-preset",
                image_id=ImageID(uuid.uuid4()),
                resource_slots=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
                cluster_mode="single-node",
                cluster_size=1,
                replica_count=1,
                deployment_strategy=DeploymentStrategyInput(type=DeploymentStrategy.ROLLING),
            )
        )
        preset_id = create_result.preset.id

        delete_result = await admin_v2_registry.deployment_revision_preset.delete(preset_id)
        assert delete_result.id == preset_id

    async def test_duplicate_name_conflict(
        self,
        admin_v2_registry: V2ClientRegistry,
        runtime_variant_id: RuntimeVariantID,
    ) -> None:
        create_result = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="dup-test-preset",
                image_id=ImageID(uuid.uuid4()),
                resource_slots=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
                cluster_mode="single-node",
                cluster_size=1,
                replica_count=1,
                deployment_strategy=DeploymentStrategyInput(type=DeploymentStrategy.ROLLING),
            )
        )
        preset_id = create_result.preset.id

        try:
            with pytest.raises(BackendAPIError) as exc_info:
                await admin_v2_registry.deployment_revision_preset.create(
                    CreateDeploymentRevisionPresetInput(
                        runtime_variant_id=runtime_variant_id,
                        name="dup-test-preset",
                        image_id=ImageID(uuid.uuid4()),
                        resource_slots=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
                        cluster_mode="single-node",
                        cluster_size=1,
                        replica_count=1,
                        deployment_strategy=DeploymentStrategyInput(
                            type=DeploymentStrategy.ROLLING
                        ),
                    )
                )
            assert exc_info.value.args[0] == 409
        finally:
            await admin_v2_registry.deployment_revision_preset.delete(preset_id)

    async def test_rank_auto_increment(
        self,
        admin_v2_registry: V2ClientRegistry,
        runtime_variant_id: RuntimeVariantID,
    ) -> None:
        r1 = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="rank-test-1",
                image_id=ImageID(uuid.uuid4()),
                resource_slots=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
                cluster_mode="single-node",
                cluster_size=1,
                replica_count=1,
                deployment_strategy=DeploymentStrategyInput(type=DeploymentStrategy.ROLLING),
            )
        )
        r2 = await admin_v2_registry.deployment_revision_preset.create(
            CreateDeploymentRevisionPresetInput(
                runtime_variant_id=runtime_variant_id,
                name="rank-test-2",
                image_id=ImageID(uuid.uuid4()),
                resource_slots=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
                cluster_mode="single-node",
                cluster_size=1,
                replica_count=1,
                deployment_strategy=DeploymentStrategyInput(type=DeploymentStrategy.ROLLING),
            )
        )
        assert r1.preset.rank == 100
        assert r2.preset.rank == 200

        await admin_v2_registry.deployment_revision_preset.delete(r2.preset.id)
        await admin_v2_registry.deployment_revision_preset.delete(r1.preset.id)
