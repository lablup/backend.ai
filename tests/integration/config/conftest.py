from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import pytest
import sqlalchemy as sa
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
from ai.backend.manager.models.dotfile.row import DotfileRow

UserDotfileFactory = Callable[..., Coroutine[Any, Any, CreateDotfileResponse]]
GroupDotfileFactory = Callable[..., Coroutine[Any, Any, CreateDotfileResponse]]
DomainDotfileFactory = Callable[..., Coroutine[Any, Any, CreateDotfileResponse]]


@pytest.fixture()
async def user_dotfile_factory(
    admin_registry: BackendAIClientRegistry,
    db_engine: SAEngine,
) -> AsyncIterator[UserDotfileFactory]:
    """Create through the SDK, mark the new file default, and delete on teardown."""
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
        # Creation adds a non-default variant; the default-file API reads defaults only.
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(DotfileRow)
                .where(DotfileRow.path == params["path"])
                .values(is_default=True)
            )
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
