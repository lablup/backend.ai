from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
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
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.image import ImageRow
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
from ai.backend.manager.repositories.stream.repository import StreamRepository
from ai.backend.testutils.db import with_tables


@dataclass
class StreamSessionFixture:
    user_uuid: uuid.UUID
    other_user_uuid: uuid.UUID
    session_id: SessionId
    session_name: str
    active_access_key: AccessKey
    inactive_access_key: AccessKey
    main_kernel_id: KernelId


def _make_session_row(
    *,
    session_id: SessionId,
    name: str,
    user_uuid: uuid.UUID,
    access_key: AccessKey,
    status: SessionStatus,
    domain_name: str,
    group_id: uuid.UUID,
    created_at: datetime,
) -> SessionRow:
    return SessionRow(
        id=session_id,
        creation_id=uuid.uuid4().hex,
        name=name,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=1,
        domain_name=domain_name,
        group_id=group_id,
        user_uuid=user_uuid,
        access_key=access_key,
        tag=None,
        status=status,
        status_info=None,
        status_data=None,
        status_history={},
        result=SessionResult.UNDEFINED,
        created_at=created_at,
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


def _make_kernel_row(
    *,
    kernel_id: KernelId,
    session_id: SessionId,
    user_uuid: uuid.UUID,
    access_key: AccessKey,
    cluster_role: str,
    cluster_idx: int,
    domain_name: str,
    group_id: uuid.UUID,
    created_at: datetime,
) -> KernelRow:
    return KernelRow(
        id=kernel_id,
        session_id=session_id,
        session_type=SessionTypes.INTERACTIVE,
        domain_name=domain_name,
        group_id=group_id,
        user_uuid=user_uuid,
        access_key=access_key,
        cluster_mode=ClusterMode.SINGLE_NODE.value,
        cluster_size=2,
        cluster_role=cluster_role,
        cluster_idx=cluster_idx,
        local_rank=0,
        cluster_hostname=cluster_role,
        image="cr.backend.ai/stable/python:latest",
        architecture="x86_64",
        registry="cr.backend.ai",
        agent=None,
        agent_addr=None,
        container_id=None,
        repl_in_port=2000 + cluster_idx * 10,
        repl_out_port=2001 + cluster_idx * 10,
        stdin_port=2002 + cluster_idx * 10,
        stdout_port=2003 + cluster_idx * 10,
        use_host_network=False,
        status=KernelStatus.RUNNING,
        status_info=None,
        status_data=None,
        status_history={},
        status_changed=created_at,
        result=SessionResult.UNDEFINED,
        created_at=created_at,
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


class TestStreamRepository:
    """Tests for StreamRepository.get_streaming_session() using a real database."""

    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
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
                ContainerRegistryRow,
                ImageRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> StreamRepository:
        return StreamRepository(db_with_cleanup)

    @pytest.fixture
    async def stream_session(self, db_with_cleanup: ExtendedAsyncSAEngine) -> StreamSessionFixture:
        """
        Seed a RUNNING session with two kernels (main + sub) owned by a user
        who has both an active and an inactive keypair, plus an unrelated user
        with their own keypair and session.
        """
        domain_name = "test-domain"
        user_uuid = uuid.uuid4()
        other_user_uuid = uuid.uuid4()
        group_id = uuid.uuid4()
        session_id = SessionId(uuid.uuid4())
        other_session_id = SessionId(uuid.uuid4())
        terminated_session_id = SessionId(uuid.uuid4())
        main_kernel_id = KernelId(uuid.uuid4())
        sub_kernel_id = KernelId(uuid.uuid4())
        active_access_key = AccessKey("ACTIVEKEY1234567890")
        inactive_access_key = AccessKey("INACTIVEKEY12345678")
        other_user_access_key = AccessKey("OTHERUSERKEY1234567")
        session_name = "shared-session"

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
            user_resource_policy = UserResourcePolicyRow(
                name="default-user-policy",
                max_vfolder_count=100,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            db_sess.add(user_resource_policy)
            project_resource_policy = ProjectResourcePolicyRow(
                name="default-project-policy",
                max_vfolder_count=100,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(project_resource_policy)
            keypair_resource_policy = KeyPairResourcePolicyRow(
                name="default-keypair-policy",
                default_for_unspecified=DefaultForUnspecified.UNLIMITED,
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=5,
                max_containers_per_session=1,
                idle_timeout=3600,
            )
            db_sess.add(keypair_resource_policy)
            await db_sess.flush()

            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    username="owner",
                    email="owner@example.com",
                    password=None,
                    need_password_change=False,
                    full_name="Owner",
                    description="",
                    status=UserStatus.ACTIVE,
                    status_info="",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=user_resource_policy.name,
                    allowed_client_ip=None,
                    totp_key=None,
                    main_access_key=None,
                )
            )
            db_sess.add(
                UserRow(
                    uuid=other_user_uuid,
                    username="other",
                    email="other@example.com",
                    password=None,
                    need_password_change=False,
                    full_name="Other",
                    description="",
                    status=UserStatus.ACTIVE,
                    status_info="",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=user_resource_policy.name,
                    allowed_client_ip=None,
                    totp_key=None,
                    main_access_key=None,
                )
            )
            db_sess.add(
                GroupRow(
                    id=group_id,
                    name="test-group",
                    description="",
                    is_active=True,
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy=project_resource_policy.name,
                    type=ProjectType.GENERAL,
                )
            )
            await db_sess.flush()

            db_sess.add(
                KeyPairRow(
                    user_id="owner@example.com",
                    user=user_uuid,
                    access_key=active_access_key,
                    secret_key="active-secret",
                    is_active=True,
                    is_admin=False,
                    resource_policy=keypair_resource_policy.name,
                    rate_limit=1000,
                )
            )
            db_sess.add(
                KeyPairRow(
                    user_id="owner@example.com",
                    user=user_uuid,
                    access_key=inactive_access_key,
                    secret_key="inactive-secret",
                    is_active=False,
                    is_admin=False,
                    resource_policy=keypair_resource_policy.name,
                    rate_limit=1000,
                )
            )
            db_sess.add(
                KeyPairRow(
                    user_id="other@example.com",
                    user=other_user_uuid,
                    access_key=other_user_access_key,
                    secret_key="other-secret",
                    is_active=True,
                    is_admin=False,
                    resource_policy=keypair_resource_policy.name,
                    rate_limit=1000,
                )
            )
            await db_sess.flush()

            now = datetime.now(tzutc())
            # The target RUNNING session — created with the now-inactive keypair.
            db_sess.add(
                _make_session_row(
                    session_id=session_id,
                    name=session_name,
                    user_uuid=user_uuid,
                    access_key=inactive_access_key,
                    status=SessionStatus.RUNNING,
                    domain_name=domain_name,
                    group_id=group_id,
                    created_at=now,
                )
            )
            # A terminated session with the same name owned by the same user.
            db_sess.add(
                _make_session_row(
                    session_id=terminated_session_id,
                    name=session_name,
                    user_uuid=user_uuid,
                    access_key=active_access_key,
                    status=SessionStatus.TERMINATED,
                    domain_name=domain_name,
                    group_id=group_id,
                    created_at=now,
                )
            )
            # A different user's RUNNING session sharing the same name.
            db_sess.add(
                _make_session_row(
                    session_id=other_session_id,
                    name=session_name,
                    user_uuid=other_user_uuid,
                    access_key=other_user_access_key,
                    status=SessionStatus.RUNNING,
                    domain_name=domain_name,
                    group_id=group_id,
                    created_at=now,
                )
            )
            await db_sess.flush()

            db_sess.add(
                _make_kernel_row(
                    kernel_id=main_kernel_id,
                    session_id=session_id,
                    user_uuid=user_uuid,
                    access_key=inactive_access_key,
                    cluster_role="main",
                    cluster_idx=0,
                    domain_name=domain_name,
                    group_id=group_id,
                    created_at=now,
                )
            )
            db_sess.add(
                _make_kernel_row(
                    kernel_id=sub_kernel_id,
                    session_id=session_id,
                    user_uuid=user_uuid,
                    access_key=inactive_access_key,
                    cluster_role="sub",
                    cluster_idx=1,
                    domain_name=domain_name,
                    group_id=group_id,
                    created_at=now,
                )
            )
            await db_sess.commit()

        return StreamSessionFixture(
            user_uuid=user_uuid,
            other_user_uuid=other_user_uuid,
            session_id=session_id,
            session_name=session_name,
            active_access_key=active_access_key,
            inactive_access_key=inactive_access_key,
            main_kernel_id=main_kernel_id,
        )

    async def test_returns_running_session_owned_by_user(
        self,
        repository: StreamRepository,
        stream_session: StreamSessionFixture,
    ) -> None:
        session = await repository.get_streaming_session(
            stream_session.session_name, stream_session.user_uuid
        )

        assert session.id == stream_session.session_id
        assert session.status == SessionStatus.RUNNING
        assert session.user_uuid == stream_session.user_uuid

    async def test_main_kernel_is_loaded(
        self,
        repository: StreamRepository,
        stream_session: StreamSessionFixture,
    ) -> None:
        session = await repository.get_streaming_session(
            stream_session.session_name, stream_session.user_uuid
        )

        assert session.main_kernel.id == stream_session.main_kernel_id

    async def test_isolated_from_other_users_session(
        self,
        repository: StreamRepository,
        stream_session: StreamSessionFixture,
    ) -> None:
        with pytest.raises(SessionNotFound):
            await repository.get_streaming_session(stream_session.session_name, uuid.uuid4())

    async def test_ignores_terminated_session(
        self,
        repository: StreamRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        stream_session: StreamSessionFixture,
    ) -> None:
        # Terminate the only RUNNING session for the owner.
        async with db_with_cleanup.begin_session() as db_sess:
            session = await db_sess.get(SessionRow, stream_session.session_id)
            assert session is not None
            session.status = SessionStatus.TERMINATED

        with pytest.raises(SessionNotFound):
            await repository.get_streaming_session(
                stream_session.session_name, stream_session.user_uuid
            )

    async def test_session_not_found_for_unknown_name(
        self,
        repository: StreamRepository,
        stream_session: StreamSessionFixture,
    ) -> None:
        with pytest.raises(SessionNotFound):
            await repository.get_streaming_session("no-such-session", stream_session.user_uuid)
