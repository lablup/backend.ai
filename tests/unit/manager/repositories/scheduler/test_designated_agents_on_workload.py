"""The designated agents a pending workload carries, read from ``session_designated_agents``."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TypedDict

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import AccessKey, AgentId
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.session_designated_agent.row import SessionDesignatedAgentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.testutils.fixtures import DomainFixtureData

from .conftest import create_pending_session_with_kernels


class SessionScope(TypedDict):
    """Ownership-scope arguments shared by every session in these tests."""

    domain_id: DomainID
    domain_name: str
    resource_group_id: ResourceGroupID
    resource_group_name: str
    group_id: uuid.UUID
    user_uuid: uuid.UUID
    access_key: AccessKey


@pytest.fixture
def session_scope(
    test_domain_id: DomainID,
    test_domain: DomainFixtureData,
    test_scaling_group_id: ResourceGroupID,
    test_scaling_group_name: str,
    test_group_id: uuid.UUID,
    test_user_uuid: uuid.UUID,
    test_access_key: AccessKey,
) -> SessionScope:
    return {
        "domain_id": test_domain_id,
        "domain_name": test_domain.domain_name,
        "resource_group_id": test_scaling_group_id,
        "resource_group_name": test_scaling_group_name,
        "group_id": test_group_id,
        "user_uuid": test_user_uuid,
        "access_key": test_access_key,
    }


class TestDesignatedAgentsOnWorkload:
    async def test_a_pending_workload_carries_the_agents_its_session_designates(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_id: ResourceGroupID,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
    ) -> None:
        session_id, _ = await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            **session_scope,
        )
        async with db_with_cleanup.begin_session() as db_sess:
            agent_uuid = await db_sess.scalar(
                sa.select(AgentRow.uuid).where(AgentRow.id == test_agent_id)
            )
            db_sess.add(SessionDesignatedAgentRow(session_id=session_id, agent_uuid=agent_uuid))

        fetch = await ScheduleDBSource(
            db_with_cleanup, ReconcileOpsProvider(db_with_cleanup)
        ).fetch_scheduling_fetch(test_scaling_group_id)

        assert fetch is not None
        assert fetch.workloads[0].placement.designated_agent_ids == [AgentId(test_agent_id)]

    async def test_a_session_designating_no_agent_carries_none(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_id: ResourceGroupID,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
    ) -> None:
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            **session_scope,
        )

        fetch = await ScheduleDBSource(
            db_with_cleanup, ReconcileOpsProvider(db_with_cleanup)
        ).fetch_scheduling_fetch(test_scaling_group_id)

        assert fetch is not None
        assert fetch.workloads[0].placement.designated_agent_ids is None
