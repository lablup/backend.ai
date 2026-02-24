from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api import artifact as _artifact_api
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.models.base import SAEngine
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.server import (
    background_task_ctx,
    database_ctx,
    event_hub_ctx,
    event_producer_ctx,
    message_queue_ctx,
    monitoring_ctx,
    redis_ctx,
    storage_manager_ctx,
)
from ai.backend.manager.services.processors import ProcessorArgs, Processors, ServiceArgs

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
_ARTIFACT_SERVER_SUBAPP_MODULES = (_auth_api, _artifact_api)


@dataclass
class ArtifactFixtureData:
    artifact_id: uuid.UUID
    artifact_revision_id: uuid.UUID
    registry_id: uuid.UUID


ArtifactFactory = Callable[..., Coroutine[Any, Any, ArtifactFixtureData]]


@asynccontextmanager
async def _artifact_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for artifact-domain component tests."""
    _mock_loader = MagicMock()
    _mock_loader.get_manager_status = AsyncMock(return_value=ManagerStatus.RUNNING)
    root_ctx.config_provider._legacy_etcd_config_loader = _mock_loader
    root_ctx.repositories = Repositories.create(
        RepositoryArgs(
            db=root_ctx.db,
            storage_manager=root_ctx.storage_manager,
            config_provider=root_ctx.config_provider,
            valkey_stat_client=root_ctx.valkey_stat,
            valkey_schedule_client=root_ctx.valkey_schedule,
            valkey_image_client=root_ctx.valkey_image,
            valkey_live_client=root_ctx.valkey_live,
        )
    )
    root_ctx.processors = Processors.create(
        ProcessorArgs(
            service_args=ServiceArgs(
                db=root_ctx.db,
                repositories=root_ctx.repositories,
                etcd=root_ctx.etcd,
                config_provider=root_ctx.config_provider,
                storage_manager=root_ctx.storage_manager,
                valkey_stat_client=root_ctx.valkey_stat,
                valkey_live=root_ctx.valkey_live,
                valkey_artifact_client=root_ctx.valkey_artifact,
                error_monitor=root_ctx.error_monitor,
                event_fetcher=root_ctx.event_fetcher,
                background_task_manager=root_ctx.background_task_manager,
                event_hub=root_ctx.event_hub,
                event_producer=root_ctx.event_producer,
                agent_registry=MagicMock(),
                idle_checker_host=MagicMock(),
                event_dispatcher=MagicMock(),
                hook_plugin_ctx=MagicMock(),
                scheduling_controller=MagicMock(),
                deployment_controller=MagicMock(),
                revision_generator_registry=MagicMock(),
                agent_cache=MagicMock(),
                notification_center=MagicMock(),
                appproxy_client_pool=MagicMock(),
                prometheus_client=MagicMock(),
            ),
        ),
        [],
    )
    yield


@pytest.fixture()
def server_subapp_pkgs() -> list[str]:
    """Load only the subapps required for artifact-domain tests."""
    return [".auth", ".artifact"]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for artifact-domain component tests."""
    return [
        redis_ctx,
        database_ctx,
        monitoring_ctx,
        storage_manager_ctx,
        message_queue_ctx,
        event_producer_ctx,
        event_hub_ctx,
        background_task_ctx,
        _artifact_domain_ctx,
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
