"""
Tests for SessionRepository.search functionality.
Tests the repository layer with mocked database operations.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.session.types import SessionData, SessionStatus
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.session.repository import SessionRepository


class TestSessionRepositorySearch:
    """Test cases for SessionRepository.search"""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Create mocked database engine"""
        return MagicMock(spec=ExtendedAsyncSAEngine)

    @pytest.fixture
    def session_repository(self, mock_db: MagicMock) -> SessionRepository:
        """Create SessionRepository instance with mocked database"""
        return SessionRepository(db=mock_db)

    @pytest.fixture
    def sample_session_data(self) -> SessionData:
        """Create sample session data"""
        return SessionData(
            id=SessionId(uuid4()),
            creation_id="test-creation-id",
            name="test-session",
            session_type=SessionTypes.INTERACTIVE,
            priority=0,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            agent_ids=["i-ubuntu"],
            domain_name="default",
            group_id=uuid4(),
            user_uuid=uuid4(),
            access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
            images=["cr.backend.ai/stable/python:latest"],
            tag=None,
            occupying_slots=ResourceSlot({"cpu": 1, "mem": 1024}),
            requested_slots=ResourceSlot({"cpu": 1, "mem": 1024}),
            vfolder_mounts=[],
            environ={},
            bootstrap_script=None,
            use_host_network=False,
            timeout=None,
            batch_timeout=None,
            created_at=datetime.now(tzutc()),
            terminated_at=None,
            starts_at=None,
            status=SessionStatus.RUNNING,
            status_info=None,
            status_data=None,
            status_history={},
            startup_command=None,
            callback_url=None,
            result=SessionResult.UNDEFINED,
            num_queries=0,
            last_stat=None,
            scaling_group_name="default",
            target_sgroup_names=[],
            network_type=NetworkType.VOLATILE,
            network_id=None,
            owner=None,
            service_ports=None,
        )

    @pytest.mark.asyncio
    async def test_search_sessions(
        self,
        session_repository: SessionRepository,
        mock_db: MagicMock,
        sample_session_data: SessionData,
    ) -> None:
        """Test searching sessions with querier"""
        mock_row = MagicMock()
        mock_row.SessionRow.to_dataclass.return_value = sample_session_data

        mock_db_sess = MagicMock()
        mock_db_sess.__aenter__ = AsyncMock(return_value=mock_db_sess)
        mock_db_sess.__aexit__ = AsyncMock(return_value=None)
        mock_db.begin_readonly_session.return_value = mock_db_sess

        # Mock execute_batch_querier result
        with pytest.MonkeyPatch.context() as mp:
            mock_result = MagicMock()
            mock_result.rows = [mock_row]
            mock_result.total_count = 1
            mock_result.has_next_page = False
            mock_result.has_previous_page = False

            mp.setattr(
                "ai.backend.manager.repositories.session.repository.execute_batch_querier",
                AsyncMock(return_value=mock_result),
            )

            querier = BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[],
                orders=[],
            )

            result = await session_repository.search(querier=querier)

            assert result.items == [sample_session_data]
            assert result.total_count == 1
            assert result.has_next_page is False
            assert result.has_previous_page is False

    @pytest.mark.asyncio
    async def test_search_sessions_empty_result(
        self,
        session_repository: SessionRepository,
        mock_db: MagicMock,
    ) -> None:
        """Test searching sessions when no results are found"""
        mock_db_sess = MagicMock()
        mock_db_sess.__aenter__ = AsyncMock(return_value=mock_db_sess)
        mock_db_sess.__aexit__ = AsyncMock(return_value=None)
        mock_db.begin_readonly_session.return_value = mock_db_sess

        with pytest.MonkeyPatch.context() as mp:
            mock_result = MagicMock()
            mock_result.rows = []
            mock_result.total_count = 0
            mock_result.has_next_page = False
            mock_result.has_previous_page = False

            mp.setattr(
                "ai.backend.manager.repositories.session.repository.execute_batch_querier",
                AsyncMock(return_value=mock_result),
            )

            querier = BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[],
                orders=[],
            )

            result = await session_repository.search(querier=querier)

            assert result.items == []
            assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_search_sessions_with_pagination(
        self,
        session_repository: SessionRepository,
        mock_db: MagicMock,
        sample_session_data: SessionData,
    ) -> None:
        """Test searching sessions with pagination"""
        mock_row = MagicMock()
        mock_row.SessionRow.to_dataclass.return_value = sample_session_data

        mock_db_sess = MagicMock()
        mock_db_sess.__aenter__ = AsyncMock(return_value=mock_db_sess)
        mock_db_sess.__aexit__ = AsyncMock(return_value=None)
        mock_db.begin_readonly_session.return_value = mock_db_sess

        with pytest.MonkeyPatch.context() as mp:
            mock_result = MagicMock()
            mock_result.rows = [mock_row]
            mock_result.total_count = 25
            mock_result.has_next_page = True
            mock_result.has_previous_page = True

            mp.setattr(
                "ai.backend.manager.repositories.session.repository.execute_batch_querier",
                AsyncMock(return_value=mock_result),
            )

            querier = BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=10),
                conditions=[],
                orders=[],
            )

            result = await session_repository.search(querier=querier)

            assert result.total_count == 25
            assert result.has_next_page is True
            assert result.has_previous_page is True
