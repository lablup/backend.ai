"""
Regression test: accessible_scaling_groups must look up the caller's keypair owner
for every role. (BA-8196)
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import graphene
import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.api.gql_legacy.schema import Query
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.user.row import UserRole
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
