from __future__ import annotations

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.artifact.request import UpdateArtifactRequest
from ai.backend.common.dto.manager.artifact.response import UpdateArtifactResponse
from ai.backend.manager.models.artifact.row import ArtifactRow

from .conftest import ArtifactFactory, ArtifactFixtureData


@pytest.mark.integration
class TestArtifactUpdateLifecycle:
    async def test_update_artifact_readonly_and_description(
        self,
        admin_registry: BackendAIClientRegistry,
        target_artifact: ArtifactFixtureData,
        db_engine: SAEngine,
    ) -> None:
        """DB-seed artifact -> update_artifact (readonly + description) -> verify updated fields."""
        # 1. Verify initial state
        result = await admin_registry.artifact.update_artifact(
            target_artifact.artifact_id,
            UpdateArtifactRequest(description="Initial update"),
        )
        assert isinstance(result, UpdateArtifactResponse)
        assert result.artifact.readonly is False
        assert result.artifact.description == "Initial update"

        # 2. Update readonly to True
        result = await admin_registry.artifact.update_artifact(
            target_artifact.artifact_id,
            UpdateArtifactRequest(readonly=True),
        )
        assert result.artifact.readonly is True
        assert result.artifact.description == "Initial update"

        # 3. Update description only
        result = await admin_registry.artifact.update_artifact(
            target_artifact.artifact_id,
            UpdateArtifactRequest(description="Final description"),
        )
        assert result.artifact.readonly is True
        assert result.artifact.description == "Final description"

        # 4. Verify directly in DB
        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(
                        ArtifactRow.__table__.c.readonly,
                        ArtifactRow.__table__.c.description,
                    ).where(ArtifactRow.__table__.c.id == target_artifact.artifact_id)
                )
            ).one()
        assert row.readonly is True
        assert row.description == "Final description"

    async def test_update_artifact_with_multiple_seeds(
        self,
        admin_registry: BackendAIClientRegistry,
        artifact_factory: ArtifactFactory,
    ) -> None:
        """Create multiple artifacts and update each independently."""
        a1 = await artifact_factory(description="Artifact 1")
        a2 = await artifact_factory(description="Artifact 2")

        await admin_registry.artifact.update_artifact(
            a1.artifact_id,
            UpdateArtifactRequest(readonly=True),
        )
        await admin_registry.artifact.update_artifact(
            a2.artifact_id,
            UpdateArtifactRequest(description="Updated Artifact 2"),
        )

        r1 = await admin_registry.artifact.update_artifact(
            a1.artifact_id,
            UpdateArtifactRequest(),
        )
        r2 = await admin_registry.artifact.update_artifact(
            a2.artifact_id,
            UpdateArtifactRequest(),
        )

        assert r1.artifact.readonly is True
        assert r1.artifact.description == "Artifact 1"
        assert r2.artifact.readonly is False
        assert r2.artifact.description == "Updated Artifact 2"
