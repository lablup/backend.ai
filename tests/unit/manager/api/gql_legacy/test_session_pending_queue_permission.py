from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest

from ai.backend.manager.api.gql_legacy.base import GenericForbidden
from ai.backend.manager.api.gql_legacy.schema import Query
from ai.backend.manager.models.user import UserRole


def _make_info(role: UserRole) -> graphene.ResolveInfo:
    ctx = MagicMock()
    ctx.user = {"role": role}
    info = MagicMock(spec=graphene.ResolveInfo)
    info.context = ctx
    return info


class TestSessionPendingQueuePermission:
    async def test_regular_user_is_rejected(self) -> None:
        info = _make_info(UserRole.USER)
        with pytest.raises(GenericForbidden):
            await Query.resolve_session_pending_queue(None, info, resource_group_id="default")

    async def test_domain_admin_is_rejected(self) -> None:
        info = _make_info(UserRole.ADMIN)
        with pytest.raises(GenericForbidden):
            await Query.resolve_session_pending_queue(None, info, resource_group_id="default")

    async def test_superadmin_is_allowed(self) -> None:
        info = _make_info(UserRole.SUPERADMIN)
        info.context.valkey_schedule = AsyncMock()
        info.context.valkey_schedule.get_pending_queue = AsyncMock(return_value=[])
        info.context.db = MagicMock()
        info.context.db.begin_readonly_session = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(
                    return_value=MagicMock(
                        scalars=AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
                    )
                ),
                __aexit__=AsyncMock(return_value=None),
            )
        )
        result = await Query.resolve_session_pending_queue(None, info, resource_group_id="default")
        assert result is not None
