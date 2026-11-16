"""What a newly created user reads through the roles the declared presets give them."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupName
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.dto.manager.v2.deployment.request import AdminSearchDeploymentsInput
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.deployment.handler import V2DeploymentHandler
from ai.backend.manager.api.rest.v2.deployment.registry import register_v2_deployment_routes
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine
    from tests.component.conftest import (
        KeypairFixtureData,
        ProvisionedUserData,
        VirtualEntitySeeder,
    )

type ProvisionUser = Callable[[], Coroutine[Any, Any, ProvisionedUserData]]
type RegistryFor = Callable[[KeypairFixtureData], Coroutine[Any, Any, V2ClientRegistry]]


@pytest.fixture()
def processor_registry(rbac_processor_registry: ProcessorRegistry[Any]) -> ProcessorRegistry[Any]:
    return rbac_processor_registry


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    deployment_processors: DeploymentProcessors,
) -> list[RouteRegistry]:
    adapter = DeploymentAdapter(deployment_processors, deployment_coordinator=MagicMock())
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(
        register_v2_deployment_routes(V2DeploymentHandler(adapter=adapter), route_deps)
    )
    return [v2_reg]


@pytest.fixture()
async def owner(provision_user: ProvisionUser) -> ProvisionedUserData:
    return await provision_user()


@pytest.fixture()
async def owned_deployment(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    resource_group_name: ResourceGroupName,
    virtual_entity_seeder: VirtualEntitySeeder,
    owner: ProvisionedUserData,
) -> AsyncIterator[uuid.UUID]:
    """A deployment in the owner's personal project, with the graph rows creating it
    writes: the owner and the project each own and govern it."""
    deployment_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(EndpointRow.__table__).values(
                id=deployment_id,
                name=f"test-deployment-{deployment_id.hex[:8]}",
                created_user=str(owner.user_id),
                session_owner=str(owner.user_id),
                domain=domain_fixture.domain_name,
                project=str(owner.personal_project_id),
                resource_group=resource_group_name,
                lifecycle_stage=EndpointLifecycle.CREATED,
                url=None,
            )
        )
        await virtual_entity_seeder.place_entity(
            conn,
            DeploymentEntityType(),
            deployment_id,
            [
                (UserEntityType(), owner.user_id),
                (ProjectEntityType(), owner.personal_project_id),
            ],
        )
    yield deployment_id
    ve = VirtualEntityRow.__table__
    async with db_engine.begin() as conn:
        await conn.execute(
            ve.delete().where(
                ve.c.entity_type == DeploymentEntityType(), ve.c.entity_id == deployment_id
            )
        )
        await conn.execute(
            EndpointRow.__table__.delete().where(EndpointRow.__table__.c.id == deployment_id)
        )


class TestPersonalProjectOwnerReads:
    async def test_owner_searches_deployments_in_their_personal_project(
        self,
        v2_registry_for: RegistryFor,
        owner: ProvisionedUserData,
        owned_deployment: uuid.UUID,
    ) -> None:
        registry = await v2_registry_for(owner.keypair)
        payload = await registry.deployment.project_search(
            owner.personal_project_id, AdminSearchDeploymentsInput()
        )
        assert [str(node.id) for node in payload.items] == [str(owned_deployment)]
