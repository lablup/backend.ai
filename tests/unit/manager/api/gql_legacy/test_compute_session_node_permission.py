"""node(id:) on ComputeSessionNode goes through the session RBAC lookup."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import graphene
from graphql_relay import to_global_id

from ai.backend.manager.api.gql_legacy.session import ComputeSessionNode
from ai.backend.manager.data.permission.permission_defs import ComputeSessionPermission
from ai.backend.manager.models.rbac import SystemScope


class TestComputeSessionNodePermission:
    async def test_get_node_reads_through_the_rbac_lookup_in_the_system_scope(self) -> None:
        info = MagicMock(spec=graphene.ResolveInfo)
        info.context = MagicMock()
        session_id = str(uuid.uuid4())
        accessible = AsyncMock(return_value=None)
        with patch.object(ComputeSessionNode, "get_accessible_node", accessible):
            result = await ComputeSessionNode.get_node(
                info, to_global_id("ComputeSessionNode", session_id)
            )
        assert result is None
        accessible.assert_awaited_once_with(
            info,
            ("ComputeSessionNode", session_id),
            SystemScope(),
            ComputeSessionPermission.READ_ATTRIBUTE,
        )
