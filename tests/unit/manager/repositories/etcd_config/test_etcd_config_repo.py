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
        """The distinct slot names the query answers with come back as a set."""
        session = await mock_db_engine.begin_readonly_session().__aenter__()
        result = MagicMock()
        result.all.return_value = ["cpu", "mem", "cuda.device"]
        session.scalars = AsyncMock(return_value=result)

        assert await repository.get_available_agent_slots("default") == {
            "cpu",
            "mem",
            "cuda.device",
        }

    async def test_get_available_agent_slots_empty_when_no_agents(
        self,
        repository: EtcdConfigRepository,
        mock_db_engine: MagicMock,
    ) -> None:
        """When no agent matches, the answer is an empty set."""
        session = await mock_db_engine.begin_readonly_session().__aenter__()
        result = MagicMock()
        result.all.return_value = []
        session.scalars = AsyncMock(return_value=result)

        assert await repository.get_available_agent_slots("nonexistent-sgroup") == set()
