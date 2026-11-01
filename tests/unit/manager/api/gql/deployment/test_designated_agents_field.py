"""The deployment node's ``designatedAgents`` field."""

from __future__ import annotations

import uuid
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.manager.api.gql.deployment.types.deployment import ModelDeployment


def _agent(agent_uuid: AgentUUID) -> MagicMock:
    agent = MagicMock()
    agent.entity_id = agent_uuid
    return agent


class TestDesignatedAgentsField:
    @pytest.fixture
    def deployment(self) -> MagicMock:
        deployment = MagicMock()
        deployment.id = str(uuid.uuid4())
        return deployment

    def _info(self, agent_uuids: list[AgentUUID], agents: list[MagicMock | None]) -> MagicMock:
        info = MagicMock()
        info.context.data_loaders.deployment_designated_agents_loader.load = AsyncMock(
            return_value=agent_uuids
        )
        info.context.data_loaders.agent_by_uuid_loader.load_many = AsyncMock(return_value=agents)
        return info

    async def _resolve(self, deployment: MagicMock, info: MagicMock) -> Any:
        resolver = cast(Any, ModelDeployment.designated_agents)
        return await resolver(deployment, info)

    async def test_two_designated_agents_come_back_as_the_connection(
        self, deployment: MagicMock
    ) -> None:
        agent_uuids = [AgentUUID(uuid.uuid4()), AgentUUID(uuid.uuid4())]
        info = self._info(agent_uuids, [_agent(u) for u in agent_uuids])

        connection = await self._resolve(deployment, info)

        assert [edge.node.entity_id for edge in connection.edges] == agent_uuids
        assert connection.count == 2
        info.context.data_loaders.deployment_designated_agents_loader.load.assert_awaited_once_with(
            DeploymentID(uuid.UUID(deployment.id))
        )

    async def test_no_designated_agent_gives_an_empty_connection(
        self, deployment: MagicMock
    ) -> None:
        info = self._info([], [])

        connection = await self._resolve(deployment, info)

        assert connection.edges == []
        assert connection.count == 0

    async def test_an_agent_no_longer_found_is_left_out(self, deployment: MagicMock) -> None:
        kept, gone = AgentUUID(uuid.uuid4()), AgentUUID(uuid.uuid4())
        info = self._info([kept, gone], [_agent(kept), None])

        connection = await self._resolve(deployment, info)

        assert [edge.node.entity_id for edge in connection.edges] == [kept]
