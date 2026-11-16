"""
Tests for the session reads and the endpoint ownership delegation of UserDBSource,
run against a real database.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
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
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy.row import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow, EndpointTokenRow
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import AssocGroupUserRow, ProjectRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
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
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.user.db_source.db_source import UserDBSource
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables

_RESOURCE_GROUP = "default"


@dataclass(frozen=True)
class _Owner:
    user_uuid: uuid.UUID
    access_key: AccessKey


@dataclass(frozen=True)
class _Scope:
    domain_id: DomainID
    domain_name: str
    project_id: uuid.UUID
    resource_group_id: ResourceGroupID
    owner: _Owner
    other: _Owner


class TestUserSessionOwnership:
    @pytest.fixture
    async def db_with_tables(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                AssocGroupUserRow,
                ResourceGroupForDomainRow,
                ResourceGroupForProjectRow,
                ResourceGroupForKeypairsRow,
                ContainerRegistryRow,
                AssociationContainerRegistriesGroupsRow,
                ImageRow,
                ImageAliasRow,
                VFolderRow,
                SessionGroupRow,
                EndpointRow,
                EndpointTokenRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                RuntimeVariantRow,
                DeploymentRevisionPresetRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                ReplicaGroupRow,
                RoutingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def db_source(self, db_with_tables: ExtendedAsyncSAEngine) -> UserDBSource:
        return UserDBSource(
            db=db_with_tables,
            v2_ops_provider=V2DBOpsProvider(db_with_tables),
            share_ops_provider=ShareOpsProvider(db_with_tables),
            policy_ops_provider=ResourcePolicyOpsProvider(db_with_tables),
            key_provider_pool=KeyProviderPool(
                providers=[], write_provider_type=KeyProviderType.PLAIN
            ),
        )

    @pytest.fixture
    async def scope(self, db_with_tables: ExtendedAsyncSAEngine) -> _Scope:
        """A domain, a project and two users, each with a default keypair."""
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"domain-{uuid.uuid4().hex[:8]}"
        project_id = uuid.uuid4()
        resource_group_id = ResourceGroupID(uuid.uuid4())
        owner = _Owner(uuid.uuid4(), AccessKey(f"AKOWNER{uuid.uuid4().hex[:12].upper()}"))
        other = _Owner(uuid.uuid4(), AccessKey(f"AKOTHER{uuid.uuid4().hex[:12].upper()}"))
        async with db_with_tables.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                    integration_id=None,
                )
            )
            db_sess.add(
                ResourceGroupRow(
                    id=resource_group_id,
                    name=_RESOURCE_GROUP,
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
                    name="user-policy",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="project-policy",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name="keypair-policy",
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
            for user in (owner, other):
                db_sess.add(
                    UserRow(
                        uuid=user.user_uuid,
                        username=f"user-{user.user_uuid.hex[:8]}",
                        email=f"user-{user.user_uuid.hex[:8]}@example.com",
                        password=None,
                        need_password_change=False,
                        full_name="",
                        description="",
                        status=UserStatus.ACTIVE,
                        status_info="",
                        domain_name=domain_name,
                        role=UserRole.USER,
                        resource_policy="user-policy",
                        allowed_client_ip=None,
                        totp_key=None,
                        domain_id=domain_id,
                    )
                )
            db_sess.add(
                ProjectRow(
                    id=project_id,
                    name=f"project-{project_id.hex[:8]}",
                    description="",
                    is_active=True,
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy="project-policy",
                    type=ProjectType.GENERAL,
                )
            )
            await db_sess.flush()
            for user in (owner, other):
                db_sess.add(
                    KeyPairRow(
                        user=user.user_uuid,
                        access_key=user.access_key,
                        secret_key=SecretValue("test-secret-key"),
                        is_active=True,
                        is_admin=False,
                        is_default=True,
                        resource_policy="keypair-policy",
                        rate_limit=1000,
                    )
                )
        return _Scope(
            domain_id=domain_id,
            domain_name=domain_name,
            project_id=project_id,
            resource_group_id=resource_group_id,
            owner=owner,
            other=other,
        )

    async def _add_session(
        self,
        db: ExtendedAsyncSAEngine,
        scope: _Scope,
        user: _Owner,
        status: SessionStatus,
    ) -> SessionId:
        """A session of the given status owned by ``user``, with one kernel."""
        session_id = SessionId(uuid.uuid4())
        now = datetime.now(tzutc())
        async with db.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    creation_id=uuid.uuid4().hex,
                    name=f"session-{session_id.hex[:8]}",
                    session_type=SessionTypes.INTERACTIVE,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    domain_id=scope.domain_id,
                    domain_name=scope.domain_name,
                    group_id=scope.project_id,
                    user_uuid=user.user_uuid,
                    access_key=user.access_key,
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
                    resource_group_id=scope.resource_group_id,
                    scaling_group_name=_RESOURCE_GROUP,
                )
            )
            await db_sess.flush()
            db_sess.add(
                KernelRow(
                    id=KernelId(uuid.uuid4()),
                    session_id=session_id,
                    session_type=SessionTypes.INTERACTIVE,
                    domain_name=scope.domain_name,
                    group_id=scope.project_id,
                    user_uuid=user.user_uuid,
                    access_key=user.access_key,
                    cluster_mode=ClusterMode.SINGLE_NODE.value,
                    cluster_size=1,
                    cluster_role="main",
                    cluster_idx=0,
                    local_rank=0,
                    cluster_hostname="main",
                    scaling_group=_RESOURCE_GROUP,
                    resource_group_id=scope.resource_group_id,
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
        return session_id

    async def _owners_of(
        self, db: ExtendedAsyncSAEngine, session_id: SessionId
    ) -> tuple[_Owner, list[_Owner]]:
        """The owner recorded on the session and on each of its kernels."""
        async with db.begin_readonly_session() as db_sess:
            session_row = (
                await db_sess.execute(
                    sa.select(SessionRow.user_uuid, SessionRow.access_key).where(
                        SessionRow.id == session_id
                    )
                )
            ).one()
            kernel_rows = (
                await db_sess.execute(
                    sa.select(KernelRow.user_uuid, KernelRow.access_key).where(
                        KernelRow.session_id == session_id
                    )
                )
            ).all()
        return (
            _Owner(session_row.user_uuid, AccessKey(session_row.access_key)),
            [_Owner(row.user_uuid, AccessKey(row.access_key)) for row in kernel_rows],
        )

    async def test_active_sessions_are_the_occupying_ones_of_the_user(
        self, db_with_tables: ExtendedAsyncSAEngine, db_source: UserDBSource, scope: _Scope
    ) -> None:
        running = await self._add_session(db_with_tables, scope, scope.owner, SessionStatus.RUNNING)
        preparing = await self._add_session(
            db_with_tables, scope, scope.owner, SessionStatus.PREPARING
        )
        await self._add_session(db_with_tables, scope, scope.owner, SessionStatus.PENDING)
        await self._add_session(db_with_tables, scope, scope.owner, SessionStatus.TERMINATED)
        await self._add_session(db_with_tables, scope, scope.other, SessionStatus.RUNNING)

        sessions = await db_source.retrieve_active_sessions(scope.owner.user_uuid)

        assert {session.id for session in sessions} == {running, preparing}

    async def test_active_sessions_empty_without_occupying_sessions(
        self, db_with_tables: ExtendedAsyncSAEngine, db_source: UserDBSource, scope: _Scope
    ) -> None:
        await self._add_session(db_with_tables, scope, scope.owner, SessionStatus.PENDING)
        await self._add_session(db_with_tables, scope, scope.owner, SessionStatus.CANCELLED)

        sessions = await db_source.retrieve_active_sessions(scope.owner.user_uuid)

        assert sessions == []

    async def test_delegation_moves_the_endpoint_and_its_live_sessions(
        self, db_with_tables: ExtendedAsyncSAEngine, db_source: UserDBSource, scope: _Scope
    ) -> None:
        live = await self._add_session(db_with_tables, scope, scope.owner, SessionStatus.RUNNING)
        dead = await self._add_session(db_with_tables, scope, scope.owner, SessionStatus.TERMINATED)
        endpoint_id = uuid.uuid4()
        async with db_with_tables.begin_session() as db_sess:
            db_sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name=f"endpoint-{endpoint_id.hex[:8]}",
                    created_user=scope.owner.user_uuid,
                    session_owner=scope.owner.user_uuid,
                    domain=scope.domain_name,
                    project=scope.project_id,
                    resource_group=_RESOURCE_GROUP,
                    desired_replicas=1,
                    url="http://test.example.com",
                    open_to_public=False,
                    lifecycle_stage=EndpointLifecycle.CREATED,
                )
            )
            await db_sess.flush()
            for session_id in (live, dead):
                db_sess.add(
                    RoutingRow(
                        id=uuid.uuid4(),
                        endpoint=endpoint_id,
                        session=session_id,
                        session_owner=scope.owner.user_uuid,
                        domain=scope.domain_name,
                        project=scope.project_id,
                        traffic_ratio=1.0,
                        revision=uuid.uuid4(),
                    )
                )

        await db_source.delegate_endpoint_ownership(scope.owner.user_uuid, scope.other.user_uuid)

        async with db_with_tables.begin_readonly_session() as db_sess:
            endpoint_owner = await db_sess.scalar(
                sa.select(EndpointRow.session_owner).where(EndpointRow.id == endpoint_id)
            )
            routing_owners = set(
                await db_sess.scalars(
                    sa.select(RoutingRow.session_owner).where(RoutingRow.endpoint == endpoint_id)
                )
            )
        assert endpoint_owner == scope.other.user_uuid
        assert routing_owners == {scope.other.user_uuid}
        live_session_owner, live_kernel_owners = await self._owners_of(db_with_tables, live)
        assert live_session_owner == scope.other
        assert live_kernel_owners == [scope.other]
        dead_session_owner, dead_kernel_owners = await self._owners_of(db_with_tables, dead)
        assert dead_session_owner == scope.owner
        assert dead_kernel_owners == [scope.owner]

    async def test_delegation_leaves_other_users_endpoints(
        self, db_with_tables: ExtendedAsyncSAEngine, db_source: UserDBSource, scope: _Scope
    ) -> None:
        endpoint_id = uuid.uuid4()
        async with db_with_tables.begin_session() as db_sess:
            db_sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name=f"endpoint-{endpoint_id.hex[:8]}",
                    created_user=scope.other.user_uuid,
                    session_owner=scope.other.user_uuid,
                    domain=scope.domain_name,
                    project=scope.project_id,
                    resource_group=_RESOURCE_GROUP,
                    desired_replicas=1,
                    url="http://test.example.com",
                    open_to_public=False,
                    lifecycle_stage=EndpointLifecycle.CREATED,
                )
            )

        await db_source.delegate_endpoint_ownership(scope.owner.user_uuid, scope.owner.user_uuid)

        async with db_with_tables.begin_readonly_session() as db_sess:
            endpoint_owner = await db_sess.scalar(
                sa.select(EndpointRow.session_owner).where(EndpointRow.id == endpoint_id)
            )
        assert endpoint_owner == scope.other.user_uuid
