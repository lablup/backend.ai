from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.common.dto.manager.config import (
    CreateDomainDotfileRequest,
    CreateDotfileResponse,
    CreateGroupDotfileRequest,
    CreateUserDotfileRequest,
    DeleteDomainDotfileRequest,
    DeleteGroupDotfileRequest,
    DeleteUserDotfileRequest,
)
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.api.rest.domainconfig.handler import DomainConfigHandler
from ai.backend.manager.api.rest.domainconfig.registry import register_domainconfig_routes
from ai.backend.manager.api.rest.groupconfig.handler import GroupConfigHandler
from ai.backend.manager.api.rest.groupconfig.registry import register_groupconfig_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.userconfig.handler import UserConfigHandler
from ai.backend.manager.api.rest.userconfig.registry import register_userconfig_routes
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.project.repository import ProjectRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.project.processors import ProjectProcessors
from ai.backend.manager.services.project.service import ProjectService
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.testutils.fixtures import DomainFixtureData

UserDotfileFactory = Callable[..., Coroutine[Any, Any, CreateDotfileResponse]]
GroupDotfileFactory = Callable[..., Coroutine[Any, Any, CreateDotfileResponse]]
DomainDotfileFactory = Callable[..., Coroutine[Any, Any, CreateDotfileResponse]]


@pytest.fixture()
def config_registry(database_engine: ExtendedAsyncSAEngine) -> ProcessorRegistry[Any]:
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(),
            repository=OpsRepository(V2DBOpsProvider(database_engine)),
        )
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    auth_processors: AuthProcessors,
    database_engine: ExtendedAsyncSAEngine,
    config_registry: ProcessorRegistry[Any],
) -> list[RouteRegistry]:
    """Load only the modules required for config-domain tests."""
    v2_ops = V2DBOpsProvider(database_engine)
    domain = DomainProcessors(
        config_registry.group(GroupMeta(DOMAIN_ENTITY_TYPE)),
        DomainService(DomainRepository(database_engine, v2_ops)),
        [],
    )
    project = ProjectProcessors(
        config_registry.group(GroupMeta(PROJECT_ENTITY_TYPE)),
        ProjectService(
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(
                repository=ProjectRepository(
                    database_engine, v2_ops, MagicMock(), MagicMock(), MagicMock()
                )
            ),
        ),
    )
    user = UserProcessors(
        config_registry.group(GroupMeta(USER_ENTITY_TYPE)),
        UserService(
            MagicMock(),
            MagicMock(),
            MagicMock(),
            UserRepository(
                database_engine,
                v2_ops,
                KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
            ),
            MagicMock(),
            MagicMock(),
        ),
    )
    return [
        register_groupconfig_routes(GroupConfigHandler(project=project), route_deps),
        register_userconfig_routes(
            UserConfigHandler(auth=auth_processors, user=user),
            route_deps,
        ),
        register_domainconfig_routes(DomainConfigHandler(domain=domain), route_deps),
    ]


@pytest.fixture()
async def user_dotfile_factory(
    admin_registry: BackendAIClientRegistry,
    db_engine: SAEngine,
) -> AsyncIterator[UserDotfileFactory]:
    """Factory fixture that creates user dotfiles via SDK and deletes on teardown."""
    created_paths: list[str] = []

    async def _create(**overrides: Any) -> CreateDotfileResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "path": f".test-dotfile-{unique}",
            "data": f"# test content {unique}",
            "permission": "644",
        }
        params.update(overrides)
        result = await admin_registry.config.create_user_dotfile(CreateUserDotfileRequest(**params))
        created_paths.append(params["path"])
        return result

    yield _create

    for path in reversed(created_paths):
        try:
            await admin_registry.config.delete_user_dotfile(DeleteUserDotfileRequest(path=path))
        except Exception:
            pass


@pytest.fixture()
async def group_dotfile_factory(
    admin_registry: BackendAIClientRegistry,
    group_fixture: uuid.UUID,
) -> AsyncIterator[GroupDotfileFactory]:
    """Factory fixture that creates group dotfiles via SDK and deletes on teardown."""
    created_paths: list[str] = []

    async def _create(**overrides: Any) -> CreateDotfileResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "group": str(group_fixture),
            "path": f".test-group-dotfile-{unique}",
            "data": f"# group test content {unique}",
            "permission": "644",
        }
        params.update(overrides)
        result = await admin_registry.config.create_group_dotfile(
            CreateGroupDotfileRequest(**params)
        )
        created_paths.append(params["path"])
        return result

    yield _create

    for path in reversed(created_paths):
        try:
            await admin_registry.config.delete_group_dotfile(
                DeleteGroupDotfileRequest(group=str(group_fixture), path=path)
            )
        except Exception:
            pass


@pytest.fixture()
async def domain_dotfile_factory(
    admin_registry: BackendAIClientRegistry,
    domain_fixture: DomainFixtureData,
) -> AsyncIterator[DomainDotfileFactory]:
    """Factory fixture that creates domain dotfiles via SDK and deletes on teardown."""
    created_paths: list[str] = []

    async def _create(**overrides: Any) -> CreateDotfileResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "domain": domain_fixture.domain_name,
            "path": f".test-domain-dotfile-{unique}",
            "data": f"# domain test content {unique}",
            "permission": "644",
        }
        params.update(overrides)
        result = await admin_registry.config.create_domain_dotfile(
            CreateDomainDotfileRequest(**params)
        )
        created_paths.append(params["path"])
        return result

    yield _create

    for path in reversed(created_paths):
        try:
            await admin_registry.config.delete_domain_dotfile(
                DeleteDomainDotfileRequest(domain=domain_fixture.domain_name, path=path)
            )
        except Exception:
            pass
