from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.config import (
    CreateDomainDotfileRequest,
    CreateDotfileResponse,
    CreateGroupDotfileRequest,
    CreateUserDotfileRequest,
    DeleteDomainDotfileRequest,
    DeleteGroupDotfileRequest,
    DeleteUserDotfileRequest,
)
from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.domainconfig.handler import DomainConfigHandler
from ai.backend.manager.api.rest.domainconfig.registry import register_domainconfig_routes
from ai.backend.manager.api.rest.groupconfig.handler import GroupConfigHandler
from ai.backend.manager.api.rest.groupconfig.registry import register_groupconfig_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.userconfig.handler import UserConfigHandler
from ai.backend.manager.api.rest.userconfig.registry import register_userconfig_routes

UserDotfileFactory = Callable[..., Coroutine[Any, Any, CreateDotfileResponse]]
GroupDotfileFactory = Callable[..., Coroutine[Any, Any, CreateDotfileResponse]]
DomainDotfileFactory = Callable[..., Coroutine[Any, Any, CreateDotfileResponse]]


@pytest.fixture()
def server_module_registries(route_deps: RouteDeps) -> list[RouteRegistry]:
    """Load only the modules required for config-domain tests."""
    mock_processors = MagicMock()
    return [
        register_auth_routes(AuthHandler(auth=mock_processors.auth), route_deps),
        register_groupconfig_routes(
            GroupConfigHandler(dotfile=mock_processors.dotfile), route_deps
        ),
        register_userconfig_routes(
            UserConfigHandler(auth=mock_processors.auth, dotfile=mock_processors.dotfile),
            route_deps,
        ),
        register_domainconfig_routes(
            DomainConfigHandler(dotfile=mock_processors.dotfile), route_deps
        ),
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
    domain_fixture: str,
) -> AsyncIterator[DomainDotfileFactory]:
    """Factory fixture that creates domain dotfiles via SDK and deletes on teardown."""
    created_paths: list[str] = []

    async def _create(**overrides: Any) -> CreateDotfileResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "domain": domain_fixture,
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
                DeleteDomainDotfileRequest(domain=domain_fixture, path=path)
            )
        except Exception:
            pass
