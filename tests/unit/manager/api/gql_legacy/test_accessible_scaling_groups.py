"""accessible_scaling_groups looks up the caller's keypair owner for every role (BA-8196)
and reads a project only within the caller's reach (BA-8902)."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import graphene
import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.api.gql_legacy.schema import Query
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.user.row import UserRole
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupKeypairOwnerByAccessKeyAction,
)

CALLER_ACCESS_KEY = AccessKey("AKIACALLER")


class TestAccessibleScalingGroups:
    @pytest.fixture
    def db_session(self) -> MagicMock:
        session = MagicMock()
        session.scalar = AsyncMock(return_value=True)
        return session

    @pytest.fixture
    def make_info(self, db_session: MagicMock) -> Callable[[UserRole], MagicMock]:
        def _make(role: UserRole) -> MagicMock:
            ctx = MagicMock()
            ctx.db.begin_readonly_session_read_committed = MagicMock(
                return_value=AsyncMock(
                    __aenter__=AsyncMock(return_value=db_session),
                    __aexit__=AsyncMock(return_value=None),
                )
            )
            ctx.user = {
                "role": role,
                "domain_name": "default",
                "uuid": uuid.uuid4(),
            }
            ctx.access_key = CALLER_ACCESS_KEY
            ctx.processors.user.lookup_keypair_owner.run = AsyncMock(
                return_value=MagicMock(owner_entity_id=uuid.uuid4())
            )
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

    async def test_a_superadmin_reads_without_a_reach_check(
        self, make_info: Callable[[UserRole], MagicMock]
    ) -> None:
        info = make_info(UserRole.SUPERADMIN)
        with patch.object(ResourceGroupRow, "list_by_condition", AsyncMock(return_value=[])):
            await Query.resolve_accessible_scaling_groups(None, info, project_id=uuid.uuid4())
        info.context.db.begin_readonly_session_read_committed.assert_not_called()

    async def test_a_user_outside_the_project_is_refused(
        self, make_info: Callable[[UserRole], MagicMock], db_session: MagicMock
    ) -> None:
        db_session.scalar.return_value = False
        with pytest.raises(InsufficientPrivilege):
            await Query.resolve_accessible_scaling_groups(
                None, make_info(UserRole.USER), project_id=uuid.uuid4()
            )

    async def test_an_admin_is_refused_a_project_of_another_domain(
        self, make_info: Callable[[UserRole], MagicMock], db_session: MagicMock
    ) -> None:
        db_session.scalar.return_value = None
        with pytest.raises(InsufficientPrivilege):
            await Query.resolve_accessible_scaling_groups(
                None, make_info(UserRole.ADMIN), project_id=uuid.uuid4()
            )

    async def test_another_role_is_refused(
        self, make_info: Callable[[UserRole], MagicMock]
    ) -> None:
        with pytest.raises(InvalidAPIParameters):
            await Query.resolve_accessible_scaling_groups.__wrapped__(
                None,
                make_info(UserRole.MONITOR),
                domain_name="default",
                project_id=uuid.uuid4(),
                group_id=uuid.uuid4(),
                access_key=CALLER_ACCESS_KEY,
            )
