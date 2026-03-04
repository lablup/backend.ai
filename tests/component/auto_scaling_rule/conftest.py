from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.types import ModuleRegistrar
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.image import ImageRow


@dataclass
class KeypairFixtureData:
    access_key: str
    secret_key: str


@dataclass
class UserFixtureData:
    user_uuid: uuid.UUID
    keypair: KeypairFixtureData
    email: str = ""


@pytest.fixture()
def server_module_registrars() -> list[ModuleRegistrar]:
    """Load only the modules required for auto-scaling-rule-domain tests."""
    return [register_auth_routes, register_admin_routes]


@pytest.fixture()
async def model_deployment_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    scaling_group_fixture: str,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[uuid.UUID]:
    """Insert a minimal EndpointRow (model deployment) and yield its UUID.

    Creates required prerequisite rows (ContainerRegistryRow, ImageRow)
    since the database_fixture does not seed them.
    """
    registry_id = uuid.uuid4()
    image_id = uuid.uuid4()
    endpoint_id = uuid.uuid4()

    async with db_engine.begin() as conn:
        # Insert a minimal container registry
        await conn.execute(
            sa.insert(ContainerRegistryRow.__table__).values(
                id=registry_id,
                url="http://test-registry.local",
                registry_name="test-registry",
                type=ContainerRegistryType.DOCKER,
                project=None,
            )
        )
        # Insert a minimal image
        await conn.execute(
            sa.insert(ImageRow.__table__).values(
                id=image_id,
                name="test-image",
                project=None,
                image="test-image:latest",
                tag="latest",
                registry="test-registry",
                registry_id=registry_id,
                architecture="x86_64",
                config_digest="sha256:" + "0" * 64,
                size_bytes=1024,
                is_local=False,
                type=ImageType.COMPUTE,
                labels={},
                resources={"cpu": {"min": "1"}, "mem": {"min": "268435456"}},
            )
        )
        # Insert a minimal endpoint (model deployment)
        await conn.execute(
            sa.insert(EndpointRow.__table__).values(
                id=endpoint_id,
                name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                created_user=str(admin_user_fixture.user_uuid),
                session_owner=str(admin_user_fixture.user_uuid),
                domain=domain_fixture,
                project=str(group_fixture),
                resource_group=scaling_group_fixture,
                image=image_id,
                lifecycle_stage=EndpointLifecycle.CREATED,
                resource_slots=ResourceSlot({"cpu": "1", "mem": "1073741824"}),
                url=None,
            )
        )
    yield endpoint_id
    async with db_engine.begin() as conn:
        # Delete in reverse FK order
        await conn.execute(
            sa.delete(EndpointRow.__table__).where(EndpointRow.__table__.c.id == endpoint_id)
        )
        await conn.execute(sa.delete(ImageRow.__table__).where(ImageRow.__table__.c.id == image_id))
        await conn.execute(
            sa.delete(ContainerRegistryRow.__table__).where(
                ContainerRegistryRow.__table__.c.id == registry_id
            )
        )
