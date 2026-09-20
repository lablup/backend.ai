"""
Tests for the project scope over sessions.
Verifies that project-scoped session search returns only sessions belonging to the target project.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    DefaultForUnspecified,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow, KernelStatus
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.resource_group import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot import ResourceAllocationRow, ResourceSlotTypeRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.session.scopes import ProjectSessionTarget
from ai.backend.manager.models.session.searchable_fields import SessionSearchableFields
from ai.backend.manager.models.specs.search.usage import UsedBy
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder


class TestSessionSearchInProject:
    """Tests for ProjectSessionTarget."""

    @pytest.fixture
    def test_domain_id(self) -> DomainID:
        return DomainID(uuid.uuid4())

    @pytest.fixture
    def test_scaling_group_id(self) -> ResourceGroupID:
        return ResourceGroupID(uuid.uuid4())

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ResourceGroupRow,
                AgentRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                ProjectRow,
                KeyPairRow,
                ContainerRegistryRow,
                ImageRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
                VirtualEntityRow,
                EntityMembershipRow,
                ScopeBindingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_scaling_group_id: ResourceGroupID,
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
                    id=test_domain_id,
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
                ResourceGroupRow(
                    id=test_scaling_group_id,
                    name="default",
                    is_active=True,
                    is_public=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
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
                    domain_id=test_domain_id,
                )
            )
            await db_sess.flush()

            db_sess.add(
                KeyPairRow(
                    user=user_id,
                    access_key=access_key,
                    secret_key=SecretValue("test-secret"),
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
                    ProjectRow(
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

            agent_id = AgentId("test-agent-1")
            agent = AgentRow(
                id=agent_id,
                status=AgentStatus.ALIVE,
                scaling_group="default",
                resource_group_id=test_scaling_group_id,
                schedulable=True,
                addr="tcp://127.0.0.1:6001",
                region="local",
                first_contact=datetime.now(tzutc()),
                lost_at=None,
                version="1.0.0",
                architecture="x86_64",
                compute_plugins={},
            )
            db_sess.add(agent)
            await db_sess.flush()
            agent_uuid = agent.uuid

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
                        domain_id=test_domain_id,
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
                        vfolder_mounts=[],
                        environ=None,
                        bootstrap_script=None,
                        use_host_network=False,
                        resource_group_id=test_scaling_group_id,
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
                        scaling_group="default",
                        resource_group_id=test_scaling_group_id,
                        image="cr.backend.ai/stable/python:latest",
                        architecture="x86_64",
                        registry="cr.backend.ai",
                        agent=agent_id if sid == session_a1_id else None,
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

            seeder = VirtualEntitySeeder()
            for sid, project_id in [
                (session_a1_id, project_a_id),
                (session_a2_id, project_a_id),
                (session_b1_id, project_b_id),
            ]:
                await seeder.create_in(
                    db_sess, SessionEntityType(), sid, [(ProjectEntityType(), project_id)]
                )

        yield {
            "agent_uuid": agent_uuid,
            "project_a_id": project_a_id,
            "project_b_id": project_b_id,
            "session_a1_id": session_a1_id,
            "session_a2_id": session_a2_id,
            "session_b1_id": session_b1_id,
        }

    async def _scoped_ids(self, db: ExtendedAsyncSAEngine, project_id: uuid.UUID) -> set[uuid.UUID]:
        scope = ProjectSessionTarget(project_id=project_id)
        async with db.begin_readonly_session() as sess:
            rows = await sess.scalars(sa.select(SessionRow.id).where(scope.to_condition()()))
            return set(rows)

    async def test_returns_only_sessions_in_target_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        """The project scope narrows to the sessions that project holds."""
        assert await self._scoped_ids(db_with_cleanup, test_data["project_a_id"]) == {
            test_data["session_a1_id"],
            test_data["session_a2_id"],
        }

    async def test_does_not_return_sessions_from_other_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        """A sibling project reaches its own session and no other."""
        assert await self._scoped_ids(db_with_cleanup, test_data["project_b_id"]) == {
            test_data["session_b1_id"]
        }

    async def _used_by_ids(self, db: ExtendedAsyncSAEngine, used_by: UsedBy) -> set[uuid.UUID]:
        async with db.begin_readonly_session() as sess:
            rows = await sess.scalars(sa.select(SessionRow.id).where(used_by.condition()))
            return set(rows)

    async def test_used_by_agent_narrows_to_the_sessions_it_runs(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        """Only the session whose kernel sits on the agent comes back."""
        used_by = SessionSearchableFields.linked.agents.used_by(AgentUUID(test_data["agent_uuid"]))
        assert await self._used_by_ids(db_with_cleanup, used_by) == {test_data["session_a1_id"]}

    async def test_used_by_another_agent_returns_none(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        used_by = SessionSearchableFields.linked.agents.used_by(AgentUUID(uuid.uuid4()))
        assert await self._used_by_ids(db_with_cleanup, used_by) == set()

    async def test_used_by_resource_group_narrows_to_the_sessions_it_runs(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_data: dict[str, uuid.UUID],
        test_scaling_group_id: ResourceGroupID,
    ) -> None:
        used_by = SessionSearchableFields.linked.resource_groups.used_by(test_scaling_group_id)
        assert await self._used_by_ids(db_with_cleanup, used_by) == {
            test_data["session_a1_id"],
            test_data["session_a2_id"],
            test_data["session_b1_id"],
        }

    async def test_used_by_another_resource_group_returns_none(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        used_by = SessionSearchableFields.linked.resource_groups.used_by(
            ResourceGroupID(uuid.uuid4())
        )
        assert await self._used_by_ids(db_with_cleanup, used_by) == set()
