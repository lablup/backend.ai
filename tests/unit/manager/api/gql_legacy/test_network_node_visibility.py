"""network_node and network_nodes share one role-based visibility condition."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest
import sqlalchemy as sa
from graphql_relay import to_global_id

from ai.backend.manager.api.gql_legacy.network import NetworkNode
from ai.backend.manager.models.network.row import NetworkRow
from ai.backend.manager.models.user.row import UserRole


class TestNetworkNodeVisibility:
    @pytest.fixture
    def make_ctx(self) -> Callable[[UserRole], MagicMock]:
        def _make(role: UserRole) -> MagicMock:
            ctx = MagicMock()
            ctx.user = {"role": role, "domain_name": "default", "uuid": uuid.uuid4()}
            return ctx

        return _make

    @pytest.fixture
    def db_session(self) -> MagicMock:
        session = MagicMock()
        session.execute = AsyncMock(
            return_value=MagicMock(
                scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
            )
        )
        session.scalar = AsyncMock(return_value=None)
        return session

    async def test_a_superadmin_sees_every_network(
        self, make_ctx: Callable[[UserRole], MagicMock], db_session: MagicMock
    ) -> None:
        cond = await NetworkNode._visible_networks_condition(
            db_session, make_ctx(UserRole.SUPERADMIN)
        )
        assert cond.compare(sa.true())
        db_session.execute.assert_not_called()

    async def test_an_admin_sees_the_networks_of_their_domain(
        self, make_ctx: Callable[[UserRole], MagicMock], db_session: MagicMock
    ) -> None:
        cond = await NetworkNode._visible_networks_condition(db_session, make_ctx(UserRole.ADMIN))
        assert cond.compare(NetworkRow.domain_name == "default")
        db_session.execute.assert_not_called()

    async def test_a_user_sees_the_networks_of_their_projects(
        self, make_ctx: Callable[[UserRole], MagicMock], db_session: MagicMock
    ) -> None:
        cond = await NetworkNode._visible_networks_condition(db_session, make_ctx(UserRole.USER))
        assert cond.compare(NetworkRow.project.in_([]))
        db_session.execute.assert_awaited_once()

    async def test_any_other_role_sees_no_network(
        self, make_ctx: Callable[[UserRole], MagicMock], db_session: MagicMock
    ) -> None:
        cond = await NetworkNode._visible_networks_condition(db_session, make_ctx(UserRole.MONITOR))
        assert cond.compare(sa.false())
        db_session.execute.assert_not_called()

    async def test_a_network_outside_the_visible_condition_is_not_found(
        self, make_ctx: Callable[[UserRole], MagicMock], db_session: MagicMock
    ) -> None:
        ctx = make_ctx(UserRole.ADMIN)
        ctx.db.begin_readonly_session = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=db_session),
                __aexit__=AsyncMock(return_value=None),
            )
        )
        info = MagicMock(spec=graphene.ResolveInfo)
        info.context = ctx
        with pytest.raises(ValueError):
            await NetworkNode.get_node(info, to_global_id("NetworkNode", str(uuid.uuid4())))
        db_session.scalar.assert_awaited_once()
