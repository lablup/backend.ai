"""Tests for ``ScheduleDBSource.update_session_error_info``."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
import sqlalchemy as sa

from ai.backend.common.types import AccessKey, KernelId, SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.exceptions import ErrorStatusInfo
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource

from .conftest import create_pending_session_with_kernels

_ERROR_INFO: ErrorStatusInfo = {
    "error": {
        "src": "other",
        "name": "KernelCreationFailedOnAgents",
        "repr": "<KernelCreationFailedOnAgents(500): bind source path does not exist>",
    },
}


class TestUpdateSessionErrorInfo:
    @pytest.fixture
    def db_source(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ScheduleDBSource:
        return ScheduleDBSource(db_with_cleanup)

    @pytest.fixture
    async def prepared_session(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> tuple[SessionId, KernelId]:
        session_id, kernel_ids = await create_pending_session_with_kernels(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            session_status=SessionStatus.PREPARED,
            kernel_status=KernelStatus.PREPARED,
            assign_agents=True,
        )
        return session_id, kernel_ids[0]

    async def test_status_data_holds_the_error_info_as_given(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        prepared_session: tuple[SessionId, KernelId],
    ) -> None:
        session_id, kernel_id = prepared_session

        await db_source.update_session_error_info(session_id, _ERROR_INFO)

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            session_status_data = await db_sess.scalar(
                sa.select(SessionRow.status_data).where(SessionRow.id == session_id)
            )
            kernel_status_data = await db_sess.scalar(
                sa.select(KernelRow.status_data).where(KernelRow.id == kernel_id)
            )
        assert session_status_data == _ERROR_INFO
        assert kernel_status_data == _ERROR_INFO
