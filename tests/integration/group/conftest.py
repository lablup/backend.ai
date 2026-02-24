from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import pytest
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.group import (
    CreateGroupRequest,
    CreateGroupResponse,
)
from ai.backend.manager.models.group import association_groups_users, groups

GroupFactory = Callable[..., Coroutine[Any, Any, CreateGroupResponse]]


@pytest.fixture()
async def group_factory(
    admin_registry: BackendAIClientRegistry,
    db_engine: SAEngine,
    domain_fixture: str,
) -> AsyncIterator[GroupFactory]:
    """Factory fixture that creates groups via SDK and deletes them on teardown."""
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> CreateGroupResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "name": f"test-group-{unique}",
            "domain_name": domain_fixture,
            "description": f"Test group {unique}",
        }
        params.update(overrides)
        result = await admin_registry.group.create(CreateGroupRequest(**params))
        created_ids.append(result.group.id)
        return result

    yield _create

    for gid in reversed(created_ids):
        try:
            await admin_registry.group.delete(gid)
        except Exception:
            # Fallback: remove group rows directly when the API delete cannot complete.
            async with db_engine.begin() as conn:
                await conn.execute(
                    association_groups_users.delete().where(
                        association_groups_users.c.group_id == gid
                    )
                )
                await conn.execute(groups.delete().where(groups.c.id == gid))


@pytest.fixture()
async def target_group(
    group_factory: GroupFactory,
) -> CreateGroupResponse:
    """Pre-created group for tests that need an existing group."""
    return await group_factory()
