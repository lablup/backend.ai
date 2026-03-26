"""
Tests for SessionRepository.search_in_project() functionality.
Verifies that project-scoped session search returns only sessions belonging to the target project.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

import pytest
from dateutil.tz import tzutc

from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    DefaultForUnspecified,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel import KernelRow, KernelStatus
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot import ResourceAllocationRow, ResourceSlotTypeRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.repositories.session.types import ProjectSessionSearchScope
from ai.backend.testutils.db import with_tables


class TestSessionSearchInProject:
    """Tests for SessionRepository.search_in_project()"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                AgentRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                GroupRow,
                KeyPairRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def session_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> SessionRepository:
        return SessionRepository(db_with_cleanup)

    @pytest.fixture
    async def test_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[dict[str, uuid.UUID], None]:
        """Create two projects with sessions: project_a has 2 sessions, project_b has 1."""
        domain_name = "test-domain"
        user_id = uuid.uuid4()
        project_a_id = uuid.uuid4()
        project_b_id = uuid.uuid4()
        session_a1_id = SessionId(uuid.uuid4())
        session_a2_id = SessionId(uuid.uuid4())
        session_b1_id = SessionId(uuid.uuid4())
        access_key = AccessKey("TESTKEY12345678")

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                    integration_id=None,
                )
            )
            db_sess.add(
                ScalingGroupRow(
                    name="default",
                    is_active=True,
                    is_public=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name="default",
                    default_for_unspecified=DefaultForUnspecified.UNLIMITED,
                    total_resource_slots=ResourceSlot(),
                    max_session_lifetime=0,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=5,
                    max_containers_per_session=1,
                    idle_timeout=3600,
                )
            )
            await db_sess.flush()

            db_sess.add(
                UserRow(
                    uuid=user_id,
                    username="testuser",
                    email="test@example.com",
                    password=None,
                    need_password_change=False,
                    full_name="Test User",
                    description="Test user",
                    status=UserStatus.ACTIVE,
                    status_info="",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy="default",
                    allowed_client_ip=None,
                    totp_key=None,
                    main_access_key=None,
                )
            )
            await db_sess.flush()

            db_sess.add(
                KeyPairRow(
                    user_id="test@example.com",
                    user=user_id,
                    access_key=access_key,
                    secret_key="test-secret",
                    is_active=True,
                    is_admin=False,
                    resource_policy="default",
                    rate_limit=1000,
                )
            )
            await db_sess.flush()

            for gid, gname in [
                (project_a_id, "project-a"),
                (project_b_id, "project-b"),
            ]:
                db_sess.add(
                    GroupRow(
                        id=gid,
                        name=gname,
                        domain_name=domain_name,
                        description=f"Test {gname}",
                        is_active=True,
                        total_resource_slots=ResourceSlot(),
                        allowed_vfolder_hosts={},
                        resource_policy="default",
                        type=ProjectType.GENERAL,
                    )
                )
            await db_sess.flush()

            now = datetime.now(tzutc())
            for sid, group_id, name in [
                (session_a1_id, project_a_id, "session-a1"),
                (session_a2_id, project_a_id, "session-a2"),
                (session_b1_id, project_b_id, "session-b1"),
            ]:
                db_sess.add(
                    SessionRow(
                        id=sid,
                        creation_id=f"creation-{name}",
                        name=name,
                        session_type=SessionTypes.INTERACTIVE,
                        cluster_mode=ClusterMode.SINGLE_NODE,
                        cluster_size=1,
                        domain_name=domain_name,
                        group_id=group_id,
                        user_uuid=user_id,
                        access_key=access_key,
                        tag=None,
                        status=SessionStatus.RUNNING,
                        status_info=None,
                        status_data=None,
                        status_history={},
                        result=SessionResult.UNDEFINED,
                        created_at=now,
                        terminated_at=None,
                        starts_at=None,
                        startup_command=None,
                        callback_url=None,
                        occupying_slots=ResourceSlot({"cpu": "1", "mem": "1073741824"}),
                        requested_slots=ResourceSlot({"cpu": "1", "mem": "1073741824"}),
                        vfolder_mounts=[],
                        environ=None,
                        bootstrap_script=None,
                        use_host_network=False,
                        scaling_group_name="default",
                    )
                )
                kernel_id = KernelId(uuid.uuid4())
                db_sess.add(
                    KernelRow(
                        id=kernel_id,
                        session_id=sid,
                        session_type=SessionTypes.INTERACTIVE,
                        domain_name=domain_name,
                        group_id=group_id,
                        user_uuid=user_id,
                        access_key=access_key,
                        cluster_mode=ClusterMode.SINGLE_NODE.value,
                        cluster_size=1,
                        cluster_role="main",
                        cluster_idx=0,
                        local_rank=0,
                        cluster_hostname="main",
                        image="cr.backend.ai/stable/python:latest",
                        architecture="x86_64",
                        registry="cr.backend.ai",
                        agent=None,
                        agent_addr=None,
                        container_id=None,
                        repl_in_port=2000,
                        repl_out_port=2001,
                        stdin_port=2002,
                        stdout_port=2003,
                        use_host_network=False,
                        status=KernelStatus.RUNNING,
                        status_info=None,
                        status_data=None,
                        status_history={},
                        status_changed=now,
                        result=SessionResult.UNDEFINED,
                        created_at=now,
                        terminated_at=None,
                        starts_at=None,
                        occupied_slots=ResourceSlot({"cpu": "1", "mem": "1073741824"}),
                        requested_slots=ResourceSlot({"cpu": "1", "mem": "1073741824"}),
                        occupied_shares={},
                        environ=None,
                        vfolder_mounts=[],
                        attached_devices={},
                        resource_opts=None,
                        preopen_ports=None,
                        bootstrap_script=None,
                        startup_command=None,
                    )
                )
            await db_sess.flush()

        yield {
            "project_a_id": project_a_id,
            "project_b_id": project_b_id,
            "session_a1_id": session_a1_id,
            "session_a2_id": session_a2_id,
            "session_b1_id": session_b1_id,
        }

    async def test_returns_only_sessions_in_target_project(
        self,
        session_repository: SessionRepository,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        """search_in_project returns only sessions belonging to the specified project."""
        scope = ProjectSessionSearchScope(project_id=test_data["project_a_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await session_repository.search_in_project(querier, scope)

        assert result.total_count == 2
        assert len(result.items) == 2
        returned_ids = {item.id for item in result.items}
        assert returned_ids == {test_data["session_a1_id"], test_data["session_a2_id"]}

    async def test_does_not_return_sessions_from_other_project(
        self,
        session_repository: SessionRepository,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        """search_in_project for project_b returns only its session, not project_a's."""
        scope = ProjectSessionSearchScope(project_id=test_data["project_b_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await session_repository.search_in_project(querier, scope)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].id == test_data["session_b1_id"]

    async def test_pagination_fields(
        self,
        session_repository: SessionRepository,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        """search_in_project returns correct pagination fields."""
        scope = ProjectSessionSearchScope(project_id=test_data["project_a_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await session_repository.search_in_project(querier, scope)

        assert result.has_next_page is False
        assert result.has_previous_page is False
