from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto
from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest

from ai.backend.manager.api.gql_legacy.schema import Query
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.models.user import UserRole


class ExpectedResult(Enum):
    ALLOWED = auto()
    FORBIDDEN = auto()


class TestSessionPendingQueuePermission:
    @pytest.fixture
    def make_info(self) -> Callable[[UserRole], graphene.ResolveInfo]:
        def _make(role: UserRole) -> graphene.ResolveInfo:
            ctx = MagicMock()
            ctx.user = {"role": role}
            ctx.valkey_schedule = AsyncMock()
            ctx.valkey_schedule.get_pending_queue = AsyncMock(return_value=[])
            ctx.db = MagicMock()
            ctx.db.begin_readonly_session = MagicMock(
                return_value=AsyncMock(
                    __aenter__=AsyncMock(
                        return_value=MagicMock(
                            scalars=AsyncMock(
                                return_value=MagicMock(all=MagicMock(return_value=[]))
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

    @pytest.mark.parametrize(
        ("role", "expected_result"),
        [
            (UserRole.USER, ExpectedResult.FORBIDDEN),
            (UserRole.ADMIN, ExpectedResult.FORBIDDEN),
            (UserRole.SUPERADMIN, ExpectedResult.ALLOWED),
        ],
    )
    async def test_only_superadmin_can_access(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        role: UserRole,
        expected_result: ExpectedResult,
    ) -> None:
        info = make_info(role)
        if expected_result == ExpectedResult.FORBIDDEN:
            with pytest.raises(GenericForbidden):
                await Query.resolve_session_pending_queue(None, info, resource_group_id="default")
        else:
            result = await Query.resolve_session_pending_queue(
                None, info, resource_group_id="default"
            )
            assert result is not None
