"""Gate tests for the manager-admin processor wiring."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.services.manager_admin.actions.get_announcement import (
    GetAnnouncementAction,
    GetAnnouncementActionResult,
)
from ai.backend.manager.services.manager_admin.actions.update_announcement import (
    UpdateAnnouncementAction,
)
from ai.backend.manager.services.manager_admin.processors import ManagerAdminProcessors


class TestAnnouncementProcessorGate:
    @pytest.fixture
    def service(self) -> MagicMock:
        service = MagicMock()
        service.get_announcement = AsyncMock(
            return_value=GetAnnouncementActionResult(enabled=True, message="hello")
        )
        service.update_announcement = AsyncMock()
        return service

    @pytest.fixture
    def processors(self, service: MagicMock) -> ManagerAdminProcessors:
        deps = MagicMock()
        deps.monitors.global_scope = ()
        deps.validators.global_scope = ()
        group: ProcessorGroup[Any] = ProcessorGroup(deps, [], "manager_admin", MagicMock())
        return ManagerAdminProcessors(group, service)

    @pytest.fixture
    def normal_user(self) -> UserData:
        return UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
            domain_id=DomainID(uuid.uuid4()),
        )

    async def test_get_allows_non_superadmin(
        self, processors: ManagerAdminProcessors, normal_user: UserData
    ) -> None:
        with with_user(normal_user):
            result = await processors.get_announcement.run(GetAnnouncementAction())

        assert result.message == "hello"

    async def test_update_rejects_non_superadmin(
        self, processors: ManagerAdminProcessors, normal_user: UserData
    ) -> None:
        with with_user(normal_user), pytest.raises(InsufficientPrivilege):
            await processors.update_announcement.run(
                UpdateAnnouncementAction(enabled=True, message="hello")
            )
