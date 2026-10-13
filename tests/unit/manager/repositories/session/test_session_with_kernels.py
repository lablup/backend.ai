"""
Tests for the session reads and writes that pick the main kernel with a separate kernel query.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.auth import PublicKey
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
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
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.kernel import (
    MainKernelNotFound,
    SessionNotFound,
    TooManyKernelsFound,
)
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow, ProjectType
from ai.backend.manager.models.resource_group.row import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
)
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot.row import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.db_source import ContainerRegistryDBSource
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables

_DOMAIN_NAME = "test-domain"
_RESOURCE_GROUP_NAME = "default"
_ACCESS_KEY = AccessKey("TESTKEY12345678")
_AGENT_ID = AgentId("i-test-agent")
_AGENT_PUBLIC_HOST = "10.0.0.7"


@dataclass(frozen=True)
class _Owner:
    domain_id: DomainID
    resource_group_id: ResourceGroupID
    user_id: uuid.UUID
    project_id: uuid.UUID


@pytest.fixture
async def db_with_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [
            # FK dependency order: parents before children
            DomainRow,
            ResourceGroupRow,
            ResourceGroupForDomainRow,
            AgentRow,
            ResourceSlotTypeRow,
            AgentResourceRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            UserRow,
            ProjectRow,
            ResourceGroupForProjectRow,
            KeyPairRow,
            ResourceGroupForKeypairsRow,
            ContainerRegistryRow,
            AssociationContainerRegistriesGroupsRow,
            ImageRow,
            ImageAliasRow,
            SessionRow,
            KernelRow,
        ],
    ):
        yield database_connection


@pytest.fixture
def repository(db_with_tables: ExtendedAsyncSAEngine) -> SessionRepository:
    return SessionRepository(
        db_with_tables,
        V2DBOpsProvider(db_with_tables),
        registry_db_source=ContainerRegistryDBSource(V2DBOpsProvider(db_with_tables)),
    )


@pytest.fixture
async def owner(db_with_tables: ExtendedAsyncSAEngine) -> _Owner:
    """A domain, resource group, agent, user, project and keypair that sessions belong to."""
    owner = _Owner(
        domain_id=DomainID(uuid.uuid4()),
        resource_group_id=ResourceGroupID(uuid.uuid4()),
        user_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
    )
    now = datetime.now(tzutc())
    async with db_with_tables.begin_session() as db_sess:
        db_sess.add(
            DomainRow(
                id=owner.domain_id,
                name=_DOMAIN_NAME,
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
                id=owner.resource_group_id,
                name=_RESOURCE_GROUP_NAME,
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
                name="default-user-policy",
                max_vfolder_count=100,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        db_sess.add(
            ProjectResourcePolicyRow(
                name="default-project-policy",
                max_vfolder_count=100,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
        )
        db_sess.add(
            KeyPairResourcePolicyRow(
                name="default-keypair-policy",
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
            AgentRow(
                id=_AGENT_ID,
                status=AgentStatus.ALIVE,
                status_changed=now,
                region="local",
                scaling_group=_RESOURCE_GROUP_NAME,
                resource_group_id=owner.resource_group_id,
                addr="tcp://10.0.0.7:6001",
                first_contact=now,
                lost_at=None,
                public_host=_AGENT_PUBLIC_HOST,
                public_key=PublicKey(b"test-public-key"),
                version="24.12.0",
                architecture="x86_64",
                compute_plugins={},
                schedulable=True,
                auto_terminate_abusing_kernel=False,
            )
        )
        db_sess.add(
            UserRow(
                uuid=owner.user_id,
                username="testuser",
                email="test@example.com",
                password=None,
                need_password_change=False,
                full_name="Test User",
                description="Test user",
                status=UserStatus.ACTIVE,
                status_info="",
                domain_name=_DOMAIN_NAME,
                role=UserRole.USER,
                resource_policy="default-user-policy",
                allowed_client_ip=None,
                totp_key=None,
                domain_id=owner.domain_id,
            )
        )
        db_sess.add(
            ProjectRow(
                id=owner.project_id,
                name="test-project",
                description="Test project",
                is_active=True,
                domain_name=_DOMAIN_NAME,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy="default-project-policy",
                type=ProjectType.GENERAL,
            )
        )
        await db_sess.flush()
        db_sess.add(
            KeyPairRow(
                user=owner.user_id,
                access_key=_ACCESS_KEY,
                secret_key=SecretValue("test-secret-key"),
                is_active=True,
                is_admin=False,
                resource_policy="default-keypair-policy",
                rate_limit=1000,
            )
        )
        await db_sess.commit()
    return owner


async def _add_session(
    db: ExtendedAsyncSAEngine,
    owner: _Owner,
    *,
    name: str,
    kernel_roles: list[str],
    status: SessionStatus = SessionStatus.RUNNING,
) -> tuple[SessionId, list[KernelId]]:
    """Insert a session with one kernel per given cluster role."""
    session_id = SessionId(uuid.uuid4())
    kernel_ids = [KernelId(uuid.uuid4()) for _ in kernel_roles]
    now = datetime.now(tzutc())
    async with db.begin_session() as db_sess:
        db_sess.add(
            SessionRow(
                id=session_id,
                creation_id=session_id.hex,
                name=name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=max(len(kernel_roles), 1),
                domain_id=owner.domain_id,
                domain_name=_DOMAIN_NAME,
                group_id=owner.project_id,
                user_uuid=owner.user_id,
                access_key=_ACCESS_KEY,
                tag=None,
                status=status,
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
                resource_group_id=owner.resource_group_id,
                scaling_group_name=_RESOURCE_GROUP_NAME,
            )
        )
        await db_sess.flush()
        for idx, (kernel_id, role) in enumerate(zip(kernel_ids, kernel_roles, strict=True)):
            db_sess.add(
                KernelRow(
                    id=kernel_id,
                    session_id=session_id,
                    session_name=name,
                    session_type=SessionTypes.INTERACTIVE,
                    domain_name=_DOMAIN_NAME,
                    group_id=owner.project_id,
                    user_uuid=owner.user_id,
                    access_key=_ACCESS_KEY,
                    cluster_mode=ClusterMode.SINGLE_NODE.value,
                    cluster_size=len(kernel_roles),
                    cluster_role=role,
                    cluster_idx=idx,
                    local_rank=idx,
                    cluster_hostname=f"{role}{idx}",
                    scaling_group=_RESOURCE_GROUP_NAME,
                    resource_group_id=owner.resource_group_id,
                    image="cr.backend.ai/stable/python:latest",
                    architecture="x86_64",
                    registry="cr.backend.ai",
                    agent=_AGENT_ID,
                    agent_addr="tcp://10.0.0.7:6001",
                    container_id=None,
                    repl_in_port=2000,
                    repl_out_port=2001,
                    stdin_port=2002,
                    stdout_port=2003,
                    service_ports=[
                        {"name": "jupyter", "protocol": "http", "container_ports": [8080]}
                    ],
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
        await db_sess.commit()
    return session_id, kernel_ids


class TestGetSessionWithKernels:
    @pytest.fixture
    async def cluster_session(
        self, db_with_tables: ExtendedAsyncSAEngine, owner: _Owner
    ) -> tuple[SessionId, list[KernelId]]:
        """A session with a main kernel and one sub kernel."""
        return await _add_session(
            db_with_tables, owner, name="cluster", kernel_roles=[DEFAULT_ROLE, "sub"]
        )

    @pytest.fixture
    async def session_without_main_kernel(
        self, db_with_tables: ExtendedAsyncSAEngine, owner: _Owner
    ) -> SessionId:
        session_id, _ = await _add_session(
            db_with_tables, owner, name="no-main", kernel_roles=["sub"]
        )
        return session_id

    @pytest.fixture
    async def session_with_two_main_kernels(
        self, db_with_tables: ExtendedAsyncSAEngine, owner: _Owner
    ) -> SessionId:
        session_id, _ = await _add_session(
            db_with_tables, owner, name="two-main", kernel_roles=[DEFAULT_ROLE, DEFAULT_ROLE]
        )
        return session_id

    async def test_picks_the_main_kernel_and_lists_every_kernel(
        self,
        repository: SessionRepository,
        cluster_session: tuple[SessionId, list[KernelId]],
    ) -> None:
        session_id, (main_id, sub_id) = cluster_session

        result = await repository.get_session_with_kernels(session_id)

        assert result.session.id == session_id
        assert result.main_kernel.id == main_id
        assert {kernel.id for kernel in result.kernels} == {main_id, sub_id}

    async def test_leaves_service_ports_off_the_session(
        self,
        repository: SessionRepository,
        cluster_session: tuple[SessionId, list[KernelId]],
    ) -> None:
        session_id, _ = cluster_session

        result = await repository.get_session_with_kernels(session_id)

        assert result.session.service_ports is None
        assert result.main_kernel.network.service_ports

    async def test_without_main_kernel_raises(
        self,
        repository: SessionRepository,
        session_without_main_kernel: SessionId,
    ) -> None:
        with pytest.raises(MainKernelNotFound):
            await repository.get_session_with_kernels(session_without_main_kernel)

    async def test_with_two_main_kernels_raises(
        self,
        repository: SessionRepository,
        session_with_two_main_kernels: SessionId,
    ) -> None:
        with pytest.raises(TooManyKernelsFound):
            await repository.get_session_with_kernels(session_with_two_main_kernels)

    async def test_unknown_session_raises(
        self,
        repository: SessionRepository,
        owner: _Owner,
    ) -> None:
        with pytest.raises(SessionNotFound):
            await repository.get_session_with_kernels(SessionId(uuid.uuid4()))


class TestGetAgentPublicHost:
    async def test_returns_the_agent_public_host(
        self,
        repository: SessionRepository,
        owner: _Owner,
    ) -> None:
        assert await repository.get_agent_public_host(_AGENT_ID) == _AGENT_PUBLIC_HOST

    async def test_unknown_agent_returns_none(
        self,
        repository: SessionRepository,
        owner: _Owner,
    ) -> None:
        assert await repository.get_agent_public_host(AgentId("i-unknown")) is None


class TestUpdateSessionName:
    @pytest.fixture
    async def cluster_session(
        self, db_with_tables: ExtendedAsyncSAEngine, owner: _Owner
    ) -> tuple[SessionId, list[KernelId]]:
        return await _add_session(
            db_with_tables, owner, name="before", kernel_roles=[DEFAULT_ROLE, "sub"]
        )

    async def test_renames_the_session_and_its_kernels(
        self,
        repository: SessionRepository,
        db_with_tables: ExtendedAsyncSAEngine,
        cluster_session: tuple[SessionId, list[KernelId]],
    ) -> None:
        session_id, kernel_ids = cluster_session

        result = await repository.update_session_name(session_id, "after")

        assert result.name == "after"
        async with db_with_tables.begin_readonly_session() as db_sess:
            kernel_names = set(
                await db_sess.scalars(
                    sa.select(KernelRow.session_name).where(KernelRow.id.in_(kernel_ids))
                )
            )
            session_name = await db_sess.scalar(
                sa.select(SessionRow.name).where(SessionRow.id == session_id)
            )
        assert kernel_names == {"after"}
        assert session_name == "after"
