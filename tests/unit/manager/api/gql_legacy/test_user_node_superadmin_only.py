"""user_node and the UserNode federation reference resolve only for a superadmin. (BA-8882)"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest
from graphql_relay import to_global_id

from ai.backend.common.exception import UserNotFound
from ai.backend.manager.api.gql_legacy.user import UserNode
from ai.backend.manager.models.user.row import UserRole


class TestUserNodeSuperadminOnly:
    @pytest.fixture
    def make_info(self) -> Callable[[UserRole], graphene.ResolveInfo]:
        def _make(role: UserRole) -> graphene.ResolveInfo:
            ctx = MagicMock()
            ctx.user = {"role": role, "domain_name": "default", "uuid": uuid.uuid4()}
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
    def user_global_id(self) -> str:
        return to_global_id("UserNode", str(uuid.uuid4()))

    @pytest.mark.parametrize(
        "role",
        [UserRole.USER, UserRole.ADMIN, UserRole.MONITOR],
        ids=["user", "admin", "monitor"],
    )
    async def test_a_non_superadmin_gets_null_without_a_db_read(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        user_global_id: str,
        role: UserRole,
    ) -> None:
        info = make_info(role)
        assert await UserNode.get_node(info, user_global_id) is None
        info.context.db.begin_readonly_session.assert_not_called()

    async def test_a_superadmin_reads_the_user_row(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        user_global_id: str,
    ) -> None:
        info = make_info(UserRole.SUPERADMIN)
        with pytest.raises(UserNotFound):
            await UserNode.get_node(info, user_global_id)
        info.context.db.begin_readonly_session.assert_called_once()
