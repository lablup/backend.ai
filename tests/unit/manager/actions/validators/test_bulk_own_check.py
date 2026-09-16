"""``BulkOwnCheck.held`` answers for the user in context."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.v2.bulk.validator.rbac import BulkOwnCheck
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock(spec=RbacPermissionCheckRepository)


async def test_missing_user_raises(repository: AsyncMock) -> None:
    check = BulkOwnCheck(repository)

    with pytest.raises(UnreachableError):
        await check.held([AgentUUID(uuid.uuid4())])
    repository.held_permissions.assert_not_awaited()
