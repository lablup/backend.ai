from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.manager.api.rest.artifact.handler import ArtifactHandler
from ai.backend.manager.api.rest.artifact.registry import register_artifact_routes
from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow


@dataclass
class ArtifactFixtureData:
    artifact_id: uuid.UUID
    artifact_revision_id: uuid.UUID
    registry_id: uuid.UUID


ArtifactFactory = Callable[..., Coroutine[Any, Any, ArtifactFixtureData]]


@pytest.fixture()
def server_module_registries(route_deps: RouteDeps) -> list[RouteRegistry]:
    """Load only the modules required for artifact-domain tests."""
    mock_processors = MagicMock()
    return [
        register_auth_routes(AuthHandler(auth=mock_processors.auth), route_deps),
        register_artifact_routes(
            ArtifactHandler(
                artifact=mock_processors.artifact,
                artifact_revision=mock_processors.artifact_revision,
            ),
            route_deps,
        ),
    ]


@pytest.fixture()
async def artifact_factory(
    db_engine: SAEngine,
) -> AsyncIterator[ArtifactFactory]:
    """Factory fixture that seeds ArtifactRow + ArtifactRevisionRow directly in the DB.

    Artifacts are normally created via import/scan from external registries, which is
    not feasible in component tests. Direct DB seeding provides the necessary test data
    for update, approve, reject, and other operations.
    """
    created_artifact_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> ArtifactFixtureData:
        artifact_id = uuid.uuid4()
        registry_id = uuid.uuid4()
        revision_id = uuid.uuid4()

        artifact_defaults: dict[str, Any] = {
            "id": artifact_id,
            "type": ArtifactType.MODEL,
            "name": f"test-artifact-{artifact_id.hex[:8]}",
            "registry_id": registry_id,
            "registry_type": "huggingface",
            "source_registry_id": registry_id,
            "source_registry_type": "huggingface",
            "description": "Test artifact for component tests",
            "readonly": False,
            "availability": ArtifactAvailability.ALIVE.value,
        }
        revision_defaults: dict[str, Any] = {
            "id": revision_id,
            "artifact_id": artifact_id,
            "version": "main",
            "status": ArtifactStatus.SCANNED.value,
        }

        artifact_overrides = {k: v for k, v in overrides.items() if k in artifact_defaults}
        revision_overrides = {
            k: v for k, v in overrides.items() if k in revision_defaults and k != "artifact_id"
        }
        artifact_defaults.update(artifact_overrides)
        revision_defaults.update(revision_overrides)

        async with db_engine.begin() as conn:
            await conn.execute(sa.insert(ArtifactRow.__table__).values(**artifact_defaults))
            await conn.execute(sa.insert(ArtifactRevisionRow.__table__).values(**revision_defaults))

        created_artifact_ids.append(artifact_defaults["id"])
        return ArtifactFixtureData(
            artifact_id=artifact_defaults["id"],
            artifact_revision_id=revision_defaults["id"],
            registry_id=registry_id,
        )

    yield _create

    # Cleanup: delete revisions first (referencing artifacts), then artifacts.
    for aid in reversed(created_artifact_ids):
        try:
            async with db_engine.begin() as conn:
                await conn.execute(
                    sa.delete(ArtifactRevisionRow.__table__).where(
                        ArtifactRevisionRow.__table__.c.artifact_id == aid
                    )
                )
                await conn.execute(
                    sa.delete(ArtifactRow.__table__).where(ArtifactRow.__table__.c.id == aid)
                )
        except Exception:
            pass


@pytest.fixture()
async def target_artifact(
    artifact_factory: ArtifactFactory,
) -> ArtifactFixtureData:
    """Pre-created artifact for tests that need an existing artifact."""
    return await artifact_factory()
