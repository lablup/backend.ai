"""graphene node(id:) on ComputeSessionNode reads a session only within the caller's role."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest
import sqlalchemy as sa
from graphql_relay import to_global_id

from ai.backend.manager.api.gql_legacy.session import ComputeSessionNode
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.user.row import UserRole

# Reachable only through string relationships of the session row's eager loads.
_ORM_CLUSTER = (EndpointRow,)


class TestComputeSessionNodeGetNode:
    @pytest.fixture
    def db_session(self) -> MagicMock:
        session = MagicMock()
        session.scalar = AsyncMock(return_value=None)
        return session

    @pytest.fixture
    def make_info(self, db_session: MagicMock) -> Callable[[UserRole], graphene.ResolveInfo]:
        def _make(role: UserRole) -> graphene.ResolveInfo:
            ctx = MagicMock()
            ctx.user = {"role": role, "domain_name": "default", "uuid": uuid.uuid4()}
            ctx.db.begin_readonly_session_read_committed = MagicMock(
                return_value=AsyncMock(
                    __aenter__=AsyncMock(return_value=db_session),
                    __aexit__=AsyncMock(return_value=None),
                )
            )
            info = MagicMock(spec=graphene.ResolveInfo)
            info.context = ctx
            return info

        return _make

    async def _read_condition(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        db_session: MagicMock,
        role: UserRole,
    ) -> str:
        node = await ComputeSessionNode.get_node(
            make_info(role), to_global_id("ComputeSessionNode", str(uuid.uuid4()))
        )
        assert node is None
        stmt: sa.Select[tuple[object]] = db_session.scalar.await_args.args[0]
        return str(stmt.whereclause)

    async def test_a_superadmin_reads_any_session(
        self, make_info: Callable[[UserRole], graphene.ResolveInfo], db_session: MagicMock
    ) -> None:
        where = await self._read_condition(make_info, db_session, UserRole.SUPERADMIN)
        assert "sessions.domain_name" not in where
        assert "sessions.user_uuid" not in where

    async def test_an_admin_reads_sessions_of_their_domain(
        self, make_info: Callable[[UserRole], graphene.ResolveInfo], db_session: MagicMock
    ) -> None:
        where = await self._read_condition(make_info, db_session, UserRole.ADMIN)
        assert "sessions.domain_name" in where

    async def test_a_user_reads_only_their_own_sessions(
        self, make_info: Callable[[UserRole], graphene.ResolveInfo], db_session: MagicMock
    ) -> None:
        where = await self._read_condition(make_info, db_session, UserRole.USER)
        assert "sessions.user_uuid" in where

    async def test_a_monitor_reads_no_session(
        self, make_info: Callable[[UserRole], graphene.ResolveInfo], db_session: MagicMock
    ) -> None:
        where = await self._read_condition(make_info, db_session, UserRole.MONITOR)
        assert "false" in where.lower()
