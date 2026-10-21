from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.dto.manager.v2.session_group.response import SessionGroupNode
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupPlacementDirectionEnum,
    SessionGroupPlacementEnforcementEnum,
)
from ai.backend.manager.api.gql.data_loader.data_loaders import DataLoaders
from ai.backend.manager.errors.permission import NotEnoughPermission


class TestSessionGroupLoader:
    @pytest.fixture
    def readable_id(self) -> SessionGroupID:
        return SessionGroupID(uuid.uuid4())

    @pytest.fixture
    def empty_id(self) -> SessionGroupID:
        return SessionGroupID(uuid.uuid4())

    @pytest.fixture
    def denied_id(self) -> SessionGroupID:
        return SessionGroupID(uuid.uuid4())

    @pytest.fixture
    def adapters(
        self, readable_id: SessionGroupID, empty_id: SessionGroupID, denied_id: SessionGroupID
    ) -> MagicMock:
        answers: dict[SessionGroupID, SessionGroupNode | Exception | None] = {
            readable_id: SessionGroupNode(
                id=readable_id,
                entity_id=readable_id,
                domain_id=uuid.uuid4(),
                project_id=uuid.uuid4(),
                owner_user_id=uuid.uuid4(),
                placement_direction=SessionGroupPlacementDirectionEnum.PACK,
                placement_enforcement=SessionGroupPlacementEnforcementEnum.STRICT,
                created_at=datetime(2026, 10, 15, tzinfo=UTC),
            ),
            empty_id: None,
            denied_id: NotEnoughPermission(),
        }
        adapters = MagicMock()
        adapters.session_group.bulk_get_ids = AsyncMock(
            side_effect=lambda ids: [answers[group_id] for group_id in ids]
        )
        return adapters

    async def test_loads_for_many_sessions_read_the_groups_in_one_call(
        self,
        adapters: MagicMock,
        readable_id: SessionGroupID,
        empty_id: SessionGroupID,
    ) -> None:
        loader = DataLoaders(adapters).session_group_loader

        await asyncio.gather(loader.load(readable_id), loader.load(empty_id))

        adapters.session_group.bulk_get_ids.assert_awaited_once()

    async def test_each_id_gets_its_own_answer(
        self,
        adapters: MagicMock,
        readable_id: SessionGroupID,
        empty_id: SessionGroupID,
        denied_id: SessionGroupID,
    ) -> None:
        loader = DataLoaders(adapters).session_group_loader

        readable, empty, denied = await asyncio.gather(
            loader.load(readable_id),
            loader.load(empty_id),
            loader.load(denied_id),
            return_exceptions=True,
        )

        assert readable is not None
        assert not isinstance(readable, BaseException)
        assert readable.entity_id == readable_id
        assert empty is None
        assert isinstance(denied, NotEnoughPermission)


class TestDeploymentDesignatedAgentsLoader:
    @pytest.fixture
    def designating_id(self) -> DeploymentID:
        return DeploymentID(uuid.uuid4())

    @pytest.fixture
    def plain_id(self) -> DeploymentID:
        return DeploymentID(uuid.uuid4())

    @pytest.fixture
    def denied_id(self) -> DeploymentID:
        return DeploymentID(uuid.uuid4())

    @pytest.fixture
    def agent_uuids(self) -> list[AgentUUID]:
        return [AgentUUID(uuid.uuid4()), AgentUUID(uuid.uuid4())]

    @pytest.fixture
    def adapters(
        self,
        designating_id: DeploymentID,
        plain_id: DeploymentID,
        denied_id: DeploymentID,
        agent_uuids: list[AgentUUID],
    ) -> MagicMock:
        answers: dict[DeploymentID, list[AgentUUID] | Exception] = {
            designating_id: agent_uuids,
            plain_id: [],
            denied_id: NotEnoughPermission(),
        }
        adapters = MagicMock()
        adapters.deployment.batch_load_designated_agents = AsyncMock(
            side_effect=lambda ids: [answers[deployment_id] for deployment_id in ids]
        )
        return adapters

    async def test_loads_for_many_deployments_read_the_agents_in_one_call(
        self, adapters: MagicMock, designating_id: DeploymentID, plain_id: DeploymentID
    ) -> None:
        loader = DataLoaders(adapters).deployment_designated_agents_loader

        await asyncio.gather(loader.load(designating_id), loader.load(plain_id))

        adapters.deployment.batch_load_designated_agents.assert_awaited_once()

    async def test_each_deployment_gets_its_own_agents(
        self,
        adapters: MagicMock,
        designating_id: DeploymentID,
        plain_id: DeploymentID,
        denied_id: DeploymentID,
        agent_uuids: list[AgentUUID],
    ) -> None:
        loader = DataLoaders(adapters).deployment_designated_agents_loader

        designating, plain, denied = await asyncio.gather(
            loader.load(designating_id),
            loader.load(plain_id),
            loader.load(denied_id),
            return_exceptions=True,
        )

        assert designating == agent_uuids
        assert plain == []
        assert isinstance(denied, NotEnoughPermission)
