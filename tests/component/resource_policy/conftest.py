"""Component test fixtures for resource policy v2 CRUD."""

from __future__ import annotations

import secrets
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
import yarl
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData
from ai.backend.common.dto.manager.v2.common import BinarySizeInput
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    CreateKeypairResourcePolicyInput,
    CreateProjectResourcePolicyInput,
    CreateUserResourcePolicyInput,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    CreateKeypairResourcePolicyPayload,
    CreateProjectResourcePolicyPayload,
    CreateUserResourcePolicyPayload,
)
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.adapters.resource_policy import ResourcePolicyAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.resource_policy.handler import V2ResourcePolicyHandler
from ai.backend.manager.api.rest.v2.resource_policy.registry import (
    register_v2_resource_policy_routes,
)
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.keypair_resource_policy.repository import (
    KeypairResourcePolicyRepository,
)
from ai.backend.manager.repositories.project_resource_policy.repository import (
    ProjectResourcePolicyRepository,
)
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.services.keypair_resource_policy.processors import (
    KeypairResourcePolicyProcessors,
)
from ai.backend.manager.services.keypair_resource_policy.service import (
    KeypairResourcePolicyService,
)
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.project_resource_policy.processors import (
    ProjectResourcePolicyProcessors,
)
from ai.backend.manager.services.project_resource_policy.service import (
    ProjectResourcePolicyService,
)
from ai.backend.manager.services.user_resource_policy.processors import (
    UserResourcePolicyProcessors,
)
from ai.backend.manager.services.user_resource_policy.service import (
    UserResourcePolicyService,
)

KeypairResourcePolicyFactory = Callable[
    ..., Coroutine[Any, Any, CreateKeypairResourcePolicyPayload]
]
UserResourcePolicyFactory = Callable[..., Coroutine[Any, Any, CreateUserResourcePolicyPayload]]
ProjectResourcePolicyFactory = Callable[
    ..., Coroutine[Any, Any, CreateProjectResourcePolicyPayload]
]


@pytest.fixture()
def resource_policy_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> tuple[
    KeypairResourcePolicyProcessors,
    UserResourcePolicyProcessors,
    ProjectResourcePolicyProcessors,
]:
    kp_repo = KeypairResourcePolicyRepository(database_engine)
    kp_service = KeypairResourcePolicyService(kp_repo)
    kp_processors = KeypairResourcePolicyProcessors(
        service=kp_service,
        action_monitors=[],
        validators=MagicMock(spec=ActionValidators),
    )

    up_repo = UserResourcePolicyRepository(database_engine)
    up_service = UserResourcePolicyService(up_repo)
    up_processors = UserResourcePolicyProcessors(
        service=up_service,
        action_monitors=[],
        validators=MagicMock(spec=ActionValidators),
    )

    pp_repo = ProjectResourcePolicyRepository(database_engine)
    pp_service = ProjectResourcePolicyService(pp_repo)
    pp_processors = ProjectResourcePolicyProcessors(
        service=pp_service,
        action_monitors=[],
        validators=MagicMock(spec=ActionValidators),
    )

    return kp_processors, up_processors, pp_processors


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    resource_policy_processors: tuple[
        KeypairResourcePolicyProcessors,
        UserResourcePolicyProcessors,
        ProjectResourcePolicyProcessors,
    ],
) -> list[RouteRegistry]:
    """Register v2 resource policy REST routes for testing."""
    kp_proc, up_proc, pp_proc = resource_policy_processors

    processors = MagicMock(spec=Processors)
    processors.keypair_resource_policy = kp_proc
    processors.user_resource_policy = up_proc
    processors.project_resource_policy = pp_proc

    adapter = ResourcePolicyAdapter(processors)
    handler = V2ResourcePolicyHandler(adapter=adapter)

    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_resource_policy_routes(handler, route_deps))
    return [v2_reg]


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """Create a V2ClientRegistry with superadmin keypair for v2 REST endpoints."""
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=admin_user_fixture.keypair.access_key,
            secret_key=admin_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def keypair_resource_policy_factory(
    admin_v2_registry: V2ClientRegistry,
    db_engine: SAEngine,
) -> AsyncIterator[KeypairResourcePolicyFactory]:
    """Factory fixture that creates keypair resource policies and cleans up."""
    created_names: list[str] = []

    async def _create(**overrides: Any) -> CreateKeypairResourcePolicyPayload:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "name": f"test-krp-{unique}",
            "default_for_unspecified": "LIMITED",
            "total_resource_slots": [
                {"resource_type": "cpu", "quantity": "4"},
                {"resource_type": "mem", "quantity": "4294967296"},
            ],
            "max_session_lifetime": 0,
            "max_concurrent_sessions": 10,
            "max_containers_per_session": 1,
            "idle_timeout": 3600,
            "max_concurrent_sftp_sessions": 1,
            "allowed_vfolder_hosts": [],
        }
        params.update(overrides)
        result = await admin_v2_registry.resource_policy.admin_create_keypair_resource_policy(
            CreateKeypairResourcePolicyInput(**params)
        )
        created_names.append(result.keypair_resource_policy.name)
        return result

    yield _create

    for name in reversed(created_names):
        try:
            await admin_v2_registry.resource_policy.admin_delete_keypair_resource_policy(name)
        except Exception:
            async with db_engine.begin() as conn:
                await conn.execute(
                    KeyPairResourcePolicyRow.__table__.delete().where(
                        KeyPairResourcePolicyRow.__table__.c.name == name
                    )
                )


@pytest.fixture()
async def user_resource_policy_factory(
    admin_v2_registry: V2ClientRegistry,
    db_engine: SAEngine,
) -> AsyncIterator[UserResourcePolicyFactory]:
    """Factory fixture that creates user resource policies and cleans up."""
    created_names: list[str] = []

    async def _create(**overrides: Any) -> CreateUserResourcePolicyPayload:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "name": f"test-urp-{unique}",
            "max_vfolder_count": 10,
            "max_quota_scope_size": BinarySizeInput(expr="0"),
            "max_session_count_per_model_session": 3,
            "max_customized_image_count": 5,
        }
        params.update(overrides)
        result = await admin_v2_registry.resource_policy.admin_create_user_resource_policy(
            CreateUserResourcePolicyInput(**params)
        )
        created_names.append(result.user_resource_policy.name)
        return result

    yield _create

    for name in reversed(created_names):
        try:
            await admin_v2_registry.resource_policy.admin_delete_user_resource_policy(name)
        except Exception:
            async with db_engine.begin() as conn:
                await conn.execute(
                    UserResourcePolicyRow.__table__.delete().where(
                        UserResourcePolicyRow.__table__.c.name == name
                    )
                )


@pytest.fixture()
async def project_resource_policy_factory(
    admin_v2_registry: V2ClientRegistry,
    db_engine: SAEngine,
) -> AsyncIterator[ProjectResourcePolicyFactory]:
    """Factory fixture that creates project resource policies and cleans up."""
    created_names: list[str] = []

    async def _create(**overrides: Any) -> CreateProjectResourcePolicyPayload:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "name": f"test-prp-{unique}",
            "max_vfolder_count": 10,
            "max_quota_scope_size": BinarySizeInput(expr="0"),
            "max_network_count": 5,
        }
        params.update(overrides)
        result = await admin_v2_registry.resource_policy.admin_create_project_resource_policy(
            CreateProjectResourcePolicyInput(**params)
        )
        created_names.append(result.project_resource_policy.name)
        return result

    yield _create

    for name in reversed(created_names):
        try:
            await admin_v2_registry.resource_policy.admin_delete_project_resource_policy(name)
        except Exception:
            async with db_engine.begin() as conn:
                await conn.execute(
                    ProjectResourcePolicyRow.__table__.delete().where(
                        ProjectResourcePolicyRow.__table__.c.name == name
                    )
                )
