"""Fixtures serving the real ``/admin/gql/strawberry`` endpoint backed by the
real image stack (adapter → service → repository → DB), so DataLoader caching
behaviour is observable end-to-end without mocking the data path.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.actions.validators.rbac.bulk import BulkActionRBACValidator
from ai.backend.manager.actions.validators.rbac.scope import ScopeActionRBACValidator
from ai.backend.manager.actions.validators.rbac.single_entity import (
    SingleEntityActionRBACValidator,
)
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.api.gql.schema import schema as strawberry_schema
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService


@pytest.fixture()
def image_adapter(
    database_engine: ExtendedAsyncSAEngine,
    valkey_clients: ValkeyClients,
    config_provider: ManagerConfigProvider,
    agent_registry: AgentRegistry,
) -> ImageAdapter:
    """Real ImageAdapter wired to the real DB; only RBAC validators are mocked."""
    repo = ImageRepository(database_engine, valkey_clients.image, config_provider)
    service = ImageService(agent_registry, repo, config_provider)
    mock_scope = MagicMock(spec=ScopeActionRBACValidator)
    mock_scope.validate = AsyncMock()
    mock_single_entity = MagicMock(spec=SingleEntityActionRBACValidator)
    mock_single_entity.validate = AsyncMock()
    mock_bulk = MagicMock(spec=BulkActionRBACValidator)
    mock_bulk.validate = AsyncMock()
    validators = ActionValidators(
        rbac=RBACValidators(scope=mock_scope, single_entity=mock_single_entity, bulk=mock_bulk),
    )
    processors = MagicMock()
    processors.image = ImageProcessors(service=service, action_monitors=[], validators=validators)
    return ImageAdapter(processors)


@pytest.fixture()
async def image_fixture(db_engine: SAEngine) -> AsyncIterator[uuid.UUID]:
    """Insert a container registry and an image row pair; yield the image id.

    Cleanup is idempotent so tests may delete the image row themselves.
    """
    registry_id = uuid.uuid4()
    image_id = uuid.uuid4()
    image_name = f"test-image-{image_id.hex[:8]}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ContainerRegistryRow.__table__).values(
                id=registry_id,
                url="https://registry.test.local",
                registry_name=f"test-registry-{registry_id.hex[:8]}",
                type=ContainerRegistryType.DOCKER,
            )
        )
        await conn.execute(
            sa.insert(ImageRow.__table__).values(
                id=image_id,
                name=f"registry.test.local/testproject/{image_name}:latest",
                project="testproject",
                image=image_name,
                tag="latest",
                registry="registry.test.local",
                registry_id=registry_id,
                architecture="x86_64",
                config_digest=f"sha256:{image_id.hex * 2}",
                size_bytes=1024000,
                is_local=False,
                type=ImageType.COMPUTE,
                accelerators=None,
                labels={},
                resources={
                    "cpu": {"min": "1", "max": "4"},
                    "mem": {"min": "268435456", "max": "4294967296"},
                },
                status=ImageStatus.ALIVE,
            )
        )
    yield image_id
    async with db_engine.begin() as conn:
        await conn.execute(ImageRow.__table__.delete().where(ImageRow.__table__.c.id == image_id))
        await conn.execute(
            ContainerRegistryRow.__table__.delete().where(
                ContainerRegistryRow.__table__.c.id == registry_id
            )
        )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    config_provider: ManagerConfigProvider,
    image_adapter: ImageAdapter,
) -> list[RouteRegistry]:
    """Serve the real strawberry schema backed by the real image adapter."""
    adapters = MagicMock()
    adapters.image = image_adapter
    gql_deps = MagicMock()
    # GQLValidationExtension reads introspection / max-depth from the config provider.
    gql_deps.config_provider = config_provider
    gql_deps.adapters = adapters
    return [
        register_admin_routes(
            AdminHandler(
                gql_schema=MagicMock(),
                gql_deps=gql_deps,
                strawberry_schema=strawberry_schema,
            ),
            route_deps,
            sub_registries=[],
            gql_ws_handler=MagicMock(),
        ),
    ]
