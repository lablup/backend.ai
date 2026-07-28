"""BA-7039: session-group policy and per-agent member counts in the scheduling fetch.

The load sites are ``ScheduleDBSource._fetch_session_group_policies`` (the
policy carried on the pending workload) and
``ScheduleDBSource._fetch_session_group_members`` (the per-agent observation);
both are verified against a real database.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TypedDict

import pytest

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.session_group import SessionGroupID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import AccessKey, AgentId, ResourceSlot, SessionTypes
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.session_group.types import (
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource

from .conftest import create_pending_session_with_kernels


class SessionScope(TypedDict):
    """Ownership-scope arguments shared by every session in these tests."""

    domain_id: DomainID
    domain_name: str
    resource_group_id: ResourceGroupID
    scaling_group_name: str
    group_id: uuid.UUID
    user_uuid: uuid.UUID
    access_key: AccessKey


async def _create_session_group(
    db: ExtendedAsyncSAEngine,
    *,
    domain_id: DomainID,
    group_id: uuid.UUID,
    user_uuid: uuid.UUID,
    direction: SessionGroupPlacementDirection = SessionGroupPlacementDirection.SPREAD,
    enforcement: SessionGroupPlacementEnforcement = SessionGroupPlacementEnforcement.PREFERRED,
    deleted_at: datetime | None = None,
) -> SessionGroupID:
    session_group_id = SessionGroupID(uuid.uuid4())
    async with db.begin_session() as db_sess:
        db_sess.add(
            SessionGroupRow(
                id=session_group_id,
                domain_id=domain_id,
                project_id=ProjectID(group_id),
                owner_user_id=UserID(user_uuid),
                placement_direction=direction,
                placement_enforcement=enforcement,
                deleted_at=deleted_at,
            )
        )
        await db_sess.flush()
    return session_group_id


async def _create_extra_agent(
    db: ExtendedAsyncSAEngine,
    *,
    scaling_group_name: str,
    resource_group_id: ResourceGroupID,
) -> str:
    agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
    async with db.begin_session() as db_sess:
        db_sess.add(
            AgentRow(
                id=agent_id,
                status=AgentStatus.ALIVE,
                region="local",
                scaling_group=scaling_group_name,
                resource_group_id=resource_group_id,
                available_slots=ResourceSlot({"cpu": Decimal("10"), "mem": Decimal("10240")}),
                occupied_slots=ResourceSlot(),
                addr="127.0.0.1:6001",
                version="1.0.0",
                architecture="x86_64",
            )
        )
        await db_sess.flush()
    return agent_id


@pytest.fixture
def session_scope(
    test_domain_id: DomainID,
    test_domain_name: str,
    test_scaling_group_id: ResourceGroupID,
    test_scaling_group_name: str,
    test_group_id: uuid.UUID,
    test_user_uuid: uuid.UUID,
    test_access_key: AccessKey,
) -> SessionScope:
    return {
        "domain_id": test_domain_id,
        "domain_name": test_domain_name,
        "resource_group_id": test_scaling_group_id,
        "scaling_group_name": test_scaling_group_name,
        "group_id": test_group_id,
        "user_uuid": test_user_uuid,
        "access_key": test_access_key,
    }


class TestSessionGroupPolicyOnWorkload:
    async def test_pending_workload_carries_the_group_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_scaling_group_id: ResourceGroupID,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
    ) -> None:
        session_group_id = await _create_session_group(
            db_with_cleanup,
            domain_id=test_domain_id,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            direction=SessionGroupPlacementDirection.PACK,
            enforcement=SessionGroupPlacementEnforcement.STRICT,
        )
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            session_group_id=session_group_id,
            **session_scope,
        )

        fetch = await ScheduleDBSource(db_with_cleanup).fetch_scheduling_fetch(
            test_scaling_group_id
        )

        assert fetch is not None
        policy = fetch.workloads[0].placement.session_group
        assert policy is not None
        assert policy.group_id == session_group_id
        assert policy.direction is SessionGroupPlacementDirection.PACK
        assert policy.enforcement is SessionGroupPlacementEnforcement.STRICT

    async def test_ungrouped_workload_has_no_policy(
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

        fetch = await ScheduleDBSource(db_with_cleanup).fetch_scheduling_fetch(
            test_scaling_group_id
        )

        assert fetch is not None
        assert fetch.workloads[0].placement.session_group is None
        # No group in this pass: the observation query never runs.
        assert fetch.session_group_members == {}

    async def test_soft_deleted_group_leaves_the_session_unconstrained(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_scaling_group_id: ResourceGroupID,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
    ) -> None:
        session_group_id = await _create_session_group(
            db_with_cleanup,
            domain_id=test_domain_id,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            deleted_at=datetime.now(UTC),
        )
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            session_group_id=session_group_id,
            **session_scope,
        )

        fetch = await ScheduleDBSource(db_with_cleanup).fetch_scheduling_fetch(
            test_scaling_group_id
        )

        assert fetch is not None
        assert fetch.workloads[0].placement.session_group is None
        assert fetch.session_group_members == {}


class TestSessionGroupMemberObservation:
    async def test_counts_running_and_reserved_members_per_agent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
    ) -> None:
        """A member that only holds a reservation (SCHEDULED) counts too."""
        session_group_id = await _create_session_group(
            db_with_cleanup,
            domain_id=test_domain_id,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
        )
        other_agent_id = await _create_extra_agent(
            db_with_cleanup,
            scaling_group_name=test_scaling_group_name,
            resource_group_id=test_scaling_group_id,
        )
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            session_group_id=session_group_id,
            **session_scope,
        )
        # RUNNING member on the first agent
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            session_group_id=session_group_id,
            session_status=SessionStatus.RUNNING,
            kernel_status=KernelStatus.RUNNING,
            assign_agents=True,
            **session_scope,
        )
        # SCHEDULED member (reservation only) on the second agent
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(other_agent_id, Decimal("1"), Decimal("1024"))],
            session_group_id=session_group_id,
            session_status=SessionStatus.SCHEDULED,
            kernel_status=KernelStatus.SCHEDULED,
            assign_agents=True,
            **session_scope,
        )

        fetch = await ScheduleDBSource(db_with_cleanup).fetch_scheduling_fetch(
            test_scaling_group_id
        )

        assert fetch is not None
        assert fetch.session_group_members == {
            AgentId(test_agent_id): {session_group_id: 1},
            AgentId(other_agent_id): {session_group_id: 1},
        }

    async def test_multi_node_member_counts_once_on_each_agent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
    ) -> None:
        session_group_id = await _create_session_group(
            db_with_cleanup,
            domain_id=test_domain_id,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
        )
        other_agent_id = await _create_extra_agent(
            db_with_cleanup,
            scaling_group_name=test_scaling_group_name,
            resource_group_id=test_scaling_group_id,
        )
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            session_group_id=session_group_id,
            **session_scope,
        )
        # One cluster session with two kernels on the first agent and one on
        # the second: 1 on each, not 2 and 1.
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[
                (test_agent_id, Decimal("1"), Decimal("1024")),
                (test_agent_id, Decimal("1"), Decimal("1024")),
                (other_agent_id, Decimal("1"), Decimal("1024")),
            ],
            session_group_id=session_group_id,
            session_status=SessionStatus.RUNNING,
            kernel_status=KernelStatus.RUNNING,
            assign_agents=True,
            **session_scope,
        )

        fetch = await ScheduleDBSource(db_with_cleanup).fetch_scheduling_fetch(
            test_scaling_group_id
        )

        assert fetch is not None
        assert fetch.session_group_members == {
            AgentId(test_agent_id): {session_group_id: 1},
            AgentId(other_agent_id): {session_group_id: 1},
        }

    async def test_terminated_members_and_other_groups_are_excluded(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_scaling_group_id: ResourceGroupID,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
    ) -> None:
        session_group_id = await _create_session_group(
            db_with_cleanup,
            domain_id=test_domain_id,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
        )
        other_group_id = await _create_session_group(
            db_with_cleanup,
            domain_id=test_domain_id,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
        )
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            session_group_id=session_group_id,
            **session_scope,
        )
        # Terminated: holds nothing on the agent anymore
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            session_group_id=session_group_id,
            session_status=SessionStatus.TERMINATED,
            kernel_status=KernelStatus.TERMINATED,
            assign_agents=True,
            **session_scope,
        )
        # A live member of a group nobody is scheduling for
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            session_group_id=other_group_id,
            session_status=SessionStatus.RUNNING,
            kernel_status=KernelStatus.RUNNING,
            assign_agents=True,
            **session_scope,
        )

        fetch = await ScheduleDBSource(db_with_cleanup).fetch_scheduling_fetch(
            test_scaling_group_id
        )

        assert fetch is not None
        assert fetch.session_group_members == {}

    async def test_none_direction_group_loads_no_observation(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_scaling_group_id: ResourceGroupID,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
    ) -> None:
        session_group_id = await _create_session_group(
            db_with_cleanup,
            domain_id=test_domain_id,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            direction=SessionGroupPlacementDirection.NONE,
        )
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            session_group_id=session_group_id,
            session_type=SessionTypes.INTERACTIVE,
            **session_scope,
        )
        await create_pending_session_with_kernels(
            db_with_cleanup,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            session_group_id=session_group_id,
            session_status=SessionStatus.RUNNING,
            kernel_status=KernelStatus.RUNNING,
            assign_agents=True,
            **session_scope,
        )

        fetch = await ScheduleDBSource(db_with_cleanup).fetch_scheduling_fetch(
            test_scaling_group_id
        )

        assert fetch is not None
        assert fetch.session_group_members == {}
