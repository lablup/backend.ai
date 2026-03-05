from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.repositories.etcd_config.repository import EtcdConfigRepository


class TestEtcdConfigRepository:
    """Unit tests for EtcdConfigRepository with mocked DB engine."""

    @pytest.fixture()
    def mock_db_engine(self) -> MagicMock:
        engine = MagicMock()
        session = AsyncMock()
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=session)
        ctx.__aexit__ = AsyncMock(return_value=False)
        engine.begin_readonly_session.return_value = ctx
        return engine

    @pytest.fixture()
    def repository(self, mock_db_engine: MagicMock) -> EtcdConfigRepository:
        return EtcdConfigRepository(mock_db_engine)

    async def test_get_available_agent_slots_returns_slot_keys(
        self,
        repository: EtcdConfigRepository,
        mock_db_engine: MagicMock,
    ) -> None:
        """When agents exist with slots, returns the union of all slot keys."""
        agent1 = MagicMock()
        agent1.available_slots = MagicMock()
        agent1.available_slots.keys.return_value = ["cpu", "mem"]

        agent2 = MagicMock()
        agent2.available_slots = MagicMock()
        agent2.available_slots.keys.return_value = ["cpu", "cuda.device"]

        session = await mock_db_engine.begin_readonly_session().__aenter__()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [agent1, agent2]
        session.execute = AsyncMock(return_value=result_mock)

        result = await repository.get_available_agent_slots("default")
        assert result == {"cpu", "mem", "cuda.device"}

    async def test_get_available_agent_slots_empty_when_no_agents(
        self,
        repository: EtcdConfigRepository,
        mock_db_engine: MagicMock,
    ) -> None:
        """When no agents match, returns an empty set."""
        session = await mock_db_engine.begin_readonly_session().__aenter__()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        result = await repository.get_available_agent_slots("nonexistent-sgroup")
        assert result == set()
