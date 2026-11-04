"""group_node and the GroupNode federation reference go through the project RBAC context. (BA-8882)"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import graphene
import pytest
import sqlalchemy as sa
from graphql_relay import to_global_id

from ai.backend.common.exception import GroupNotFound
from ai.backend.manager.api.gql_legacy.group import GroupNode
from ai.backend.manager.models.user.row import UserRole


class TestGroupNodePermission:
    @pytest.fixture
    def make_info(self) -> Callable[[], graphene.ResolveInfo]:
        def _make() -> graphene.ResolveInfo:
            ctx = MagicMock()
            ctx.user = {"role": UserRole.USER, "domain_name": "default", "uuid": uuid.uuid4()}
            ctx.db.connect = MagicMock(
                return_value=AsyncMock(
                    __aenter__=AsyncMock(return_value=MagicMock()),
                    __aexit__=AsyncMock(return_value=None),
                )
            )
            ctx.db.begin_readonly_session = MagicMock(
                return_value=AsyncMock(
                    __aenter__=AsyncMock(
                        return_value=MagicMock(
                            scalars=AsyncMock(
                                return_value=MagicMock(first=MagicMock(return_value=None))
                            )
                        )
                    ),
                    __aexit__=AsyncMock(return_value=None),
                )
            )
            info = MagicMock(spec=graphene.ResolveInfo)
            info.context = ctx
            return info

        return _make

    @pytest.fixture
    def group_global_id(self) -> str:
        return to_global_id("GroupNode", str(uuid.uuid4()))

    async def test_a_caller_without_project_read_gets_null_without_a_db_read(
        self,
        make_info: Callable[[], graphene.ResolveInfo],
        group_global_id: str,
    ) -> None:
        info = make_info()
        permission_ctx = MagicMock(query_condition=None)
        with patch(
            "ai.backend.manager.api.gql_legacy.group.get_permission_ctx",
            AsyncMock(return_value=permission_ctx),
        ):
            assert await GroupNode.get_node(info, group_global_id) is None
        info.context.db.begin_readonly_session.assert_not_called()

    async def test_a_project_outside_the_permitted_condition_is_not_found(
        self,
        make_info: Callable[[], graphene.ResolveInfo],
        group_global_id: str,
    ) -> None:
        info = make_info()
        permission_ctx = MagicMock(query_condition=sa.false())
        with patch(
            "ai.backend.manager.api.gql_legacy.group.get_permission_ctx",
            AsyncMock(return_value=permission_ctx),
        ):
            with pytest.raises(GroupNotFound):
                await GroupNode.get_node(info, group_global_id)
        info.context.db.begin_readonly_session.assert_called_once()
