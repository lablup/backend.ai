from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.session_group.request import PurgeSessionGroupInput
from ai.backend.common.dto.manager.v2.session_group.response import (
    AdminSearchSessionGroupsPayload,
    PurgeSessionGroupPayload,
    SessionGroupNode,
)
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupPlacementDirectionEnum,
    SessionGroupPlacementEnforcementEnum,
    SessionGroupScope,
)
from ai.backend.manager.api.gql.base import UUIDScopeGQL
from ai.backend.manager.api.gql.session_group import resolver
from ai.backend.manager.api.gql.session_group.types import (
    PurgeSessionGroupInputGQL,
    SessionGroupScopeGQL,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege


def _node() -> SessionGroupNode:
    group_id = uuid.uuid4()
    return SessionGroupNode(
        id=group_id,
        entity_id=group_id,
        domain_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        owner_user_id=uuid.uuid4(),
        placement_direction=SessionGroupPlacementDirectionEnum.SPREAD,
        placement_enforcement=SessionGroupPlacementEnforcementEnum.PREFERRED,
        created_at=datetime(2026, 10, 16, tzinfo=UTC),
    )


def _caller(*, is_superadmin: bool) -> MagicMock:
    caller = MagicMock()
    caller.is_superadmin = is_superadmin
    return caller


class TestSessionGroup:
    async def test_reads_the_group_by_its_id(self) -> None:
        node = _node()
        info = MagicMock()
        info.context.adapters.session_group.get = AsyncMock(return_value=node)

        result = await resolver.session_group.base_resolver(info, node.id)

        info.context.adapters.session_group.get.assert_awaited_once_with(SessionGroupID(node.id))
        assert result is not None
        assert result.entity_id == node.entity_id


class TestAdminSessionGroups:
    @pytest.fixture
    def nodes(self) -> list[SessionGroupNode]:
        return [_node(), _node()]

    @pytest.fixture
    def info(self, nodes: list[SessionGroupNode]) -> MagicMock:
        info = MagicMock()
        info.context.adapters.session_group.global_search = AsyncMock(
            return_value=AdminSearchSessionGroupsPayload(
                items=nodes, total_count=5, has_next_page=True, has_previous_page=False
            )
        )
        return info

    @pytest.mark.parametrize(
        "caller",
        [
            pytest.param(None, id="anonymous"),
            pytest.param(_caller(is_superadmin=False), id="non-admin"),
        ],
    )
    async def test_everyone_but_a_superadmin_is_refused_before_the_read(
        self, info: MagicMock, caller: MagicMock | None
    ) -> None:
        with patch("ai.backend.manager.api.gql.utils.current_user", return_value=caller):
            with pytest.raises(InsufficientPrivilege):
                await resolver.admin_session_groups.base_resolver(info)

        info.context.adapters.session_group.global_search.assert_not_awaited()

    async def test_a_superadmin_gets_the_page_as_a_connection(
        self, info: MagicMock, nodes: list[SessionGroupNode]
    ) -> None:
        with patch(
            "ai.backend.manager.api.gql.utils.current_user",
            return_value=_caller(is_superadmin=True),
        ):
            result = await resolver.admin_session_groups.base_resolver(info, first=2)

        assert result is not None
        assert info.context.adapters.session_group.global_search.call_args.args[0].first == 2
        assert [edge.node.entity_id for edge in result.edges] == [n.entity_id for n in nodes]
        assert result.count == 5
        assert result.page_info.has_next_page is True
        assert result.page_info.start_cursor == result.edges[0].cursor
        assert result.page_info.end_cursor == result.edges[-1].cursor


class TestScopedSessionGroups:
    @pytest.fixture
    def info(self) -> MagicMock:
        info = MagicMock()
        info.context.adapters.session_group.scoped_search = AsyncMock(
            return_value=AdminSearchSessionGroupsPayload(
                items=[], total_count=0, has_next_page=False, has_previous_page=False
            )
        )
        return info

    async def test_the_scope_reaches_the_adapter(self, info: MagicMock) -> None:
        project_id = uuid.uuid4()

        await resolver.scoped_session_groups.base_resolver(
            info, SessionGroupScopeGQL(project=[UUIDScopeGQL(value=project_id)])
        )

        search_input = info.context.adapters.session_group.scoped_search.call_args.args[0]
        assert search_input.scope == SessionGroupScope(project=[UUIDScope(value=project_id)])

    async def test_an_empty_page_has_no_cursors(self, info: MagicMock) -> None:
        result = await resolver.scoped_session_groups.base_resolver(
            info, SessionGroupScopeGQL(project=[UUIDScopeGQL(value=uuid.uuid4())])
        )

        assert result is not None
        assert result.edges == []
        assert result.count == 0
        assert result.page_info.start_cursor is None
        assert result.page_info.end_cursor is None


class TestPurgeSessionGroup:
    @pytest.fixture
    def group_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def info(self, group_id: uuid.UUID) -> MagicMock:
        info = MagicMock()
        info.context.adapters.session_group.purge = AsyncMock(
            return_value=PurgeSessionGroupPayload(id=group_id)
        )
        return info

    async def test_the_group_id_reaches_the_adapter(
        self, info: MagicMock, group_id: uuid.UUID
    ) -> None:
        await cast(Any, resolver.purge_session_group).base_resolver(
            info, PurgeSessionGroupInputGQL(id=group_id)
        )

        info.context.adapters.session_group.purge.assert_awaited_once_with(
            PurgeSessionGroupInput(id=group_id)
        )

    async def test_the_payload_names_the_purged_group(
        self, info: MagicMock, group_id: uuid.UUID
    ) -> None:
        result = await cast(Any, resolver.purge_session_group).base_resolver(
            info, PurgeSessionGroupInputGQL(id=group_id)
        )

        assert result.id == group_id
