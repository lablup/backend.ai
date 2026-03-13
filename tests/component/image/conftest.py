from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.image.handler import ImageHandler
from ai.backend.manager.api.rest.image.registry import register_image_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService


@pytest.fixture()
def image_processors(
    database_engine: ExtendedAsyncSAEngine,
    valkey_clients: ValkeyClients,
    config_provider: ManagerConfigProvider,
    agent_registry: AgentRegistry,
) -> ImageProcessors:
    repo = ImageRepository(database_engine, valkey_clients.image, config_provider)
    service = ImageService(agent_registry, repo, config_provider)
    return ImageProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    image_processors: ImageProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for image-domain tests."""
    image_registry = register_image_routes(ImageHandler(image=image_processors), route_deps)
    return [
        register_admin_routes(
            AdminHandler(
                gql_schema=MagicMock(), gql_deps=MagicMock(), strawberry_schema=MagicMock()
            ),
            route_deps,
            sub_registries=[image_registry],
        ),
    ]


@pytest.fixture()
async def container_registry_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[uuid.UUID]:
    """Insert a test Docker container registry and yield its UUID.

    Images require a FK to ContainerRegistryRow, so this must be created first.
    """
    registry_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ContainerRegistryRow.__table__).values(
                id=registry_id,
                url="https://registry.test.local",
                registry_name=f"test-registry-{registry_id.hex[:8]}",
                type=ContainerRegistryType.DOCKER,
            )
        )
    yield registry_id
    async with db_engine.begin() as conn:
        await conn.execute(
            ContainerRegistryRow.__table__.delete().where(
                ContainerRegistryRow.__table__.c.id == registry_id
            )
        )


@pytest.fixture()
def image_factory(
    db_engine: SAEngine,
    container_registry_fixture: uuid.UUID,
) -> Callable[..., ImageFactoryHelper]:
    """Factory that creates ImageRow entries in the DB.

    Returns a callable factory helper. Each call inserts a new image.
    Created images are tracked and cleaned up after the test.
    """
    return lambda: ImageFactoryHelper(db_engine, container_registry_fixture)


class ImageFactoryHelper:
    """Helper to create and track test ImageRow entries."""

    def __init__(self, db_engine: SAEngine, registry_id: uuid.UUID) -> None:
        self._db_engine = db_engine
        self._registry_id = registry_id
        self._created_ids: list[uuid.UUID] = []

    async def create(
        self,
        *,
        name_suffix: str | None = None,
        architecture: str = "x86_64",
        image_type: ImageType = ImageType.COMPUTE,
        status: ImageStatus = ImageStatus.ALIVE,
    ) -> uuid.UUID:
        """Insert an ImageRow and return its UUID."""
        image_id = uuid.uuid4()
        suffix = name_suffix or image_id.hex[:8]
        image_name = f"test-image-{suffix}"
        canonical = f"registry.test.local/testproject/{image_name}:latest"
        async with self._db_engine.begin() as conn:
            await conn.execute(
                sa.insert(ImageRow.__table__).values(
                    id=image_id,
                    name=canonical,
                    project="testproject",
                    image=image_name,
                    tag="latest",
                    registry="registry.test.local",
                    registry_id=self._registry_id,
                    architecture=architecture,
                    config_digest=f"sha256:{image_id.hex * 2}",
                    size_bytes=1024000,
                    is_local=False,
                    type=image_type,
                    accelerators=None,
                    labels={},
                    resources={
                        "cpu": {"min": "1", "max": "4"},
                        "mem": {"min": "268435456", "max": "4294967296"},
                    },
                    status=status,
                )
            )
        self._created_ids.append(image_id)
        return image_id

    async def cleanup(self) -> None:
        """Remove all images created by this factory.

        Deletes ImageAliasRow entries first to avoid FK violations,
        since image_aliases.image references images.id.
        """
        if not self._created_ids:
            return
        async with self._db_engine.begin() as conn:
            await conn.execute(
                ImageAliasRow.__table__.delete().where(
                    ImageAliasRow.__table__.c.image.in_(self._created_ids)
                )
            )
            await conn.execute(
                ImageRow.__table__.delete().where(ImageRow.__table__.c.id.in_(self._created_ids))
            )


@pytest.fixture()
async def image_fixture(
    image_factory: Callable[..., ImageFactoryHelper],
) -> AsyncIterator[tuple[uuid.UUID, ImageFactoryHelper]]:
    """Create a single test image and yield (image_id, factory_helper).

    The factory helper can create additional images if needed.
    Cleans up all factory-created images after the test.
    """
    helper = image_factory()
    image_id = await helper.create()
    yield image_id, helper
    await helper.cleanup()
