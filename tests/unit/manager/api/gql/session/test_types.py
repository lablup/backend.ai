from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.dto.manager.v2.common import ResourceSlotInfo
from ai.backend.common.dto.manager.v2.kernel.response import ResourceAllocationGQLDTO
from ai.backend.common.dto.manager.v2.session.response import (
    SessionLifecycleInfoGQLDTO,
    SessionMetadataInfoGQLDTO,
    SessionNetworkInfo,
    SessionNode,
    SessionResourceInfoGQLDTO,
    SessionRuntimeInfoGQLDTO,
)
from ai.backend.manager.api.gql.session.types import SessionV2GQL
from ai.backend.manager.errors.permission import NotEnoughPermission


def _session(session_group_id: uuid.UUID | None) -> SessionV2GQL:
    session_id = uuid.uuid4()
    return SessionV2GQL.from_pydantic(
        SessionNode(
            id=session_id,
            entity_id=session_id,
            domain_name="default",
            user_id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            metadata=SessionMetadataInfoGQLDTO(
                session_type="interactive",
                cluster_mode="single-node",
                cluster_size=1,
                tier=0,
                priority=0,
                job_priority=0,
                is_preemptible=False,
            ),
            resource=SessionResourceInfoGQLDTO(
                allocation=ResourceAllocationGQLDTO(requested=ResourceSlotInfo(entries=[])),
                session_group_id=session_group_id,
            ),
            lifecycle=SessionLifecycleInfoGQLDTO(status="RUNNING", result="undefined"),
            runtime=SessionRuntimeInfoGQLDTO(),
            network=SessionNetworkInfo(use_host_network=False),
        )
    )


class TestSessionV2SessionGroup:
    @pytest.fixture
    def mock_info(self) -> MagicMock:
        info = MagicMock()
        info.context.data_loaders.session_group_loader.load = AsyncMock()
        return info

    async def test_a_session_in_a_group_loads_the_group_by_its_id(
        self, mock_info: MagicMock
    ) -> None:
        group_id = uuid.uuid4()
        group_node = MagicMock()
        loader = mock_info.context.data_loaders.session_group_loader
        loader.load.return_value = group_node

        result = await _session(group_id).session_group(info=mock_info)

        assert result is group_node
        loader.load.assert_awaited_once_with(SessionGroupID(group_id))

    async def test_a_session_in_no_group_resolves_to_none_without_loading(
        self, mock_info: MagicMock
    ) -> None:
        result = await _session(None).session_group(info=mock_info)

        assert result is None
        mock_info.context.data_loaders.session_group_loader.load.assert_not_awaited()

    async def test_a_group_the_loader_answers_empty_for_resolves_to_none(
        self, mock_info: MagicMock
    ) -> None:
        mock_info.context.data_loaders.session_group_loader.load.return_value = None

        result = await _session(uuid.uuid4()).session_group(info=mock_info)

        assert result is None

    async def test_a_group_the_caller_may_not_read_raises_the_permission_error(
        self, mock_info: MagicMock
    ) -> None:
        mock_info.context.data_loaders.session_group_loader.load.side_effect = NotEnoughPermission()

        with pytest.raises(NotEnoughPermission):
            await _session(uuid.uuid4()).session_group(info=mock_info)
