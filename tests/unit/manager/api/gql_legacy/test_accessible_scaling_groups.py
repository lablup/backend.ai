"""accessible_scaling_groups reads only a project the caller may read."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import graphene
import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.api.gql_legacy.schema import Query
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
from ai.backend.manager.models.user.row import UserRole
from ai.backend.manager.services.group.actions.search_projects import GetProjectAction

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
            ctx.processors.group.get_project.wait_for_complete = AsyncMock()
            ctx.db.begin = MagicMock(
                return_value=AsyncMock(
                    __aenter__=AsyncMock(return_value=MagicMock()),
                    __aexit__=AsyncMock(return_value=None),
                )
            )
            info = MagicMock(spec=graphene.ResolveInfo)
            info.context = ctx
            return info

        return _make

    @pytest.fixture
    def query_allowed_sgroups(self) -> Generator[AsyncMock, None, None]:
        with (
            patch(
                "ai.backend.manager.api.gql_legacy.schema.query_allowed_sgroups",
                AsyncMock(return_value=[]),
            ) as mocked,
            patch.object(ScalingGroupRow, "list_by_condition", AsyncMock(return_value=[])),
        ):
            yield mocked

    async def test_the_named_project_is_read_before_its_resource_groups(
        self,
        make_info: Callable[[UserRole], MagicMock],
        query_allowed_sgroups: AsyncMock,
    ) -> None:
        info = make_info(UserRole.USER)
        project_id = uuid.uuid4()
        await Query.resolve_accessible_scaling_groups(None, info, project_id=project_id)

        info.context.processors.group.get_project.wait_for_complete.assert_awaited_once_with(
            GetProjectAction(project_id=project_id)
        )
        query_allowed_sgroups.assert_awaited_once()

    async def test_a_project_the_caller_may_not_read_is_refused(
        self,
        make_info: Callable[[UserRole], MagicMock],
        query_allowed_sgroups: AsyncMock,
    ) -> None:
        info = make_info(UserRole.USER)
        info.context.processors.group.get_project.wait_for_complete.side_effect = (
            NotEnoughPermission()
        )
        with pytest.raises(NotEnoughPermission):
            await Query.resolve_accessible_scaling_groups(None, info, project_id=uuid.uuid4())
        query_allowed_sgroups.assert_not_awaited()
