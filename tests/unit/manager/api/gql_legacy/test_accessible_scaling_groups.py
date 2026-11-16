"""accessible_scaling_groups looks up the caller's keypair owner for every role (BA-8196)
and reads only a project the caller may read."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import graphene
import pytest

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.types import AccessKey
from ai.backend.manager.api.gql_legacy.schema import Query
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.user.row import UserRole
from ai.backend.manager.services.project.actions.search_projects import GetProjectAction
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupKeypairOwnerByAccessKeyAction,
)

CALLER_ACCESS_KEY = AccessKey("AKIACALLER")


class TestAccessibleScalingGroups:
    @pytest.fixture
    def make_info(self) -> Callable[[UserRole], MagicMock]:
        def _make(role: UserRole) -> MagicMock:
            ctx = MagicMock()
            ctx.user = {
                "role": role,
                "domain_name": "default",
                "uuid": uuid.uuid4(),
            }
            ctx.access_key = CALLER_ACCESS_KEY
            ctx.processors.user.lookup_keypair_owner.run = AsyncMock(
                return_value=MagicMock(owner_entity_id=uuid.uuid4())
            )
            ctx.processors.project.get_project.run = AsyncMock()
            ctx.scheduler_repository.get_domain_id_by_name = AsyncMock(return_value=uuid.uuid4())
            ctx.scheduler_repository.query_allowed_resource_groups = AsyncMock(return_value=[])
            info = MagicMock(spec=graphene.ResolveInfo)
            info.context = ctx
            return info

        return _make

    @pytest.mark.parametrize("role", [UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN])
    async def test_looks_up_owner_by_caller_access_key(
        self,
        make_info: Callable[[UserRole], MagicMock],
        role: UserRole,
    ) -> None:
        info = make_info(role)
        with patch.object(ResourceGroupRow, "list_by_condition", AsyncMock(return_value=[])):
            await Query.resolve_accessible_scaling_groups(None, info, project_id=uuid.uuid4())

        info.context.processors.user.lookup_keypair_owner.run.assert_awaited_once_with(
            LookupKeypairOwnerByAccessKeyAction(access_key=CALLER_ACCESS_KEY)
        )

    async def test_the_named_project_is_read_before_its_resource_groups(
        self, make_info: Callable[[UserRole], MagicMock]
    ) -> None:
        info = make_info(UserRole.USER)
        project_id = uuid.uuid4()
        with patch.object(ResourceGroupRow, "list_by_condition", AsyncMock(return_value=[])):
            await Query.resolve_accessible_scaling_groups(None, info, project_id=project_id)

        info.context.processors.project.get_project.run.assert_awaited_once_with(
            GetProjectAction(project_id=ProjectID(project_id))
        )

    async def test_a_project_the_caller_may_not_read_is_refused(
        self, make_info: Callable[[UserRole], MagicMock]
    ) -> None:
        info = make_info(UserRole.USER)
        info.context.processors.project.get_project.run.side_effect = NotEnoughPermission()
        with pytest.raises(NotEnoughPermission):
            await Query.resolve_accessible_scaling_groups(None, info, project_id=uuid.uuid4())
        info.context.scheduler_repository.query_allowed_resource_groups.assert_not_awaited()
