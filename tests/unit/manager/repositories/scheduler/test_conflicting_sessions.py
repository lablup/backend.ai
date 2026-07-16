"""
Tests for the conflicting-session detection query (ScheduleDBSource.search_kernels
filtered by agent + active kernel statuses) against a real DB.

When an agent's resource group changes, every session with an active kernel on the
agent is a cleanup target, so detection is "active kernels on this agent".
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from dateutil.tz import tzutc

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.kernel.conditions import KernelConditions
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource


def _conflicting_session_ids(items: list[KernelInfo]) -> set[SessionId]:
    return {SessionId(uuid.UUID(kernel.session.session_id)) for kernel in items}


def _active_kernels_querier(agent_id: AgentId) -> BatchQuerier:
    conflicting_statuses = (
        KernelStatus.resource_occupied_statuses() | KernelStatus.resource_requested_statuses()
    )
    return BatchQuerier(
        pagination=NoPagination(),
        conditions=[
            KernelConditions.by_agent_id(agent_id),
            KernelConditions.by_statuses(conflicting_statuses),
        ],
    )


class TestConflictingSessionDetection:
    @pytest.fixture
    async def other_scaling_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[tuple[str, ResourceGroupID], None]:
        """A second scaling group that differs from the agent's current group."""
        sg_id = ResourceGroupID(uuid.uuid4())
        sg_name = f"other-sgroup-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    id=sg_id,
                    name=sg_name,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(
                        allowed_session_types=[],
                        pending_timeout=timedelta(hours=1),
                        config={},
                    ),
                    driver_opts={},
                    is_active=True,
                )
            )
            await db_sess.flush()
        yield sg_name, sg_id

    async def _create_session_with_kernel(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain_id: DomainID,
        domain_name: str,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        access_key: AccessKey,
        agent_id: AgentId,
        scaling_group_name: str,
        resource_group_id: ResourceGroupID,
        kernel_status: KernelStatus,
    ) -> SessionId:
        """Create a single-kernel session whose kernel runs on ``agent_id`` under
        the given (session/kernel) resource group and kernel status."""
        session_id = SessionId(uuid.uuid4())
        kernel_id = uuid.uuid4()
        async with db.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    name=f"test-session-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INTERACTIVE,
                    domain_id=domain_id,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    access_key=access_key,
                    resource_group_id=resource_group_id,
                    scaling_group_name=scaling_group_name,
                    status=SessionStatus.RUNNING,
                    status_info="test",
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                    created_at=datetime.now(tzutc()),
                    images=["python:3.8"],
                    vfolder_mounts=[],
                    environ={},
                    result=SessionResult.UNDEFINED,
                )
            )
            await db_sess.flush()
            db_sess.add(
                KernelRow(
                    id=kernel_id,
                    session_id=session_id,
                    agent=agent_id,
                    agent_addr="127.0.0.1:6001",
                    scaling_group=scaling_group_name,
                    resource_group_id=resource_group_id,
                    cluster_idx=0,
                    cluster_role="main",
                    cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                    image="python:3.8",
                    architecture="x86_64",
                    registry="docker.io",
                    container_id=f"container-{uuid.uuid4().hex[:8]}",
                    status=kernel_status,
                    status_changed=datetime.now(tzutc()),
                    occupied_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                    requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    access_key=access_key,
                    mounts=[],
                    environ={},
                    vfolder_mounts=[],
                    preopen_ports=[],
                    repl_in_port=2001,
                    repl_out_port=2002,
                    stdin_port=2003,
                    stdout_port=2004,
                )
            )
            await db_sess.flush()
        return session_id

    async def test_returns_all_active_sessions_on_agent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_agent_id: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        other_scaling_group: tuple[str, ResourceGroupID],
    ) -> None:
        # Every active kernel on the agent is a cleanup target regardless of group.
        other_sg_name, other_sg_id = other_scaling_group
        agent_id = AgentId(test_agent_id)

        # An active kernel scheduled under the agent's own group
        own_group_session_id = await self._create_session_with_kernel(
            db_with_cleanup,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=agent_id,
            scaling_group_name=test_scaling_group_name,
            resource_group_id=test_scaling_group_id,
            kernel_status=KernelStatus.RUNNING,
        )
        # An active kernel scheduled under a different group
        other_group_session_id = await self._create_session_with_kernel(
            db_with_cleanup,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=agent_id,
            scaling_group_name=other_sg_name,
            resource_group_id=other_sg_id,
            kernel_status=KernelStatus.RUNNING,
        )

        # When
        db_source = ScheduleDBSource(db_with_cleanup)
        result = await db_source.search_kernels(_active_kernels_querier(agent_id))

        # Then both active sessions on the agent are returned
        assert _conflicting_session_ids(result.items) == {
            own_group_session_id,
            other_group_session_id,
        }

    async def test_ignores_kernels_not_occupying_resources(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain_name: str,
        test_agent_id: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        other_scaling_group: tuple[str, ResourceGroupID],
    ) -> None:
        # Given a conflicting-group kernel that is already TERMINATED (not occupying)
        other_sg_name, other_sg_id = other_scaling_group
        agent_id = AgentId(test_agent_id)
        await self._create_session_with_kernel(
            db_with_cleanup,
            domain_id=test_domain_id,
            domain_name=test_domain_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=agent_id,
            scaling_group_name=other_sg_name,
            resource_group_id=other_sg_id,
            kernel_status=KernelStatus.TERMINATED,
        )

        # When
        db_source = ScheduleDBSource(db_with_cleanup)
        result = await db_source.search_kernels(_active_kernels_querier(agent_id))

        # Then a terminated kernel is not treated as a conflict
        assert result.items == []
