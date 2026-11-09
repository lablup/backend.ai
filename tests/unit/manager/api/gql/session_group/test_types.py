from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.manager.api.gql.session_group.types import SessionGroupGQL


class TestSessionGroupResolveNodes:
    @pytest.fixture
    def readable_id(self) -> SessionGroupID:
        return SessionGroupID(uuid.uuid4())

    @pytest.fixture
    def empty_id(self) -> SessionGroupID:
        return SessionGroupID(uuid.uuid4())

    @pytest.fixture
    def group_node(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_info(
        self, readable_id: SessionGroupID, empty_id: SessionGroupID, group_node: MagicMock
    ) -> MagicMock:
        answers = {readable_id: group_node, empty_id: None}
        info = MagicMock()
        info.context.data_loaders.session_group_loader.load_many = AsyncMock(
            side_effect=lambda ids: [answers[group_id] for group_id in ids]
        )
        return info

    async def test_node_ids_resolve_in_order_with_an_empty_id_as_none(
        self,
        mock_info: MagicMock,
        readable_id: SessionGroupID,
        empty_id: SessionGroupID,
        group_node: MagicMock,
    ) -> None:
        result = await SessionGroupGQL.resolve_nodes(
            info=mock_info, node_ids=[str(empty_id), str(readable_id)]
        )

        assert list(result) == [None, group_node]
