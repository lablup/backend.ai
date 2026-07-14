"""Regression for BA-5996: PERSISTENT network info must reach SessionDataForStart."""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    DefaultForUnspecified,
    ResourceSlot,
    SecretKey,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.session.conditions import SessionConditions
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.testutils.db import with_tables


class TestPersistentNetworkNotRecreated:
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
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ContainerRegistryRow,
                ImageRow,
                AgentRow,
                SessionRow,
                KernelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def seeded_environment(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Seed FK-required rows (domain, sgroup, policies, user, keypair, group, agent)."""
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        sg_id = ResourceGroupID(uuid.uuid4())
        sg_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        project_policy_name = f"test-project-policy-{uuid.uuid4().hex[:8]}"
        user_policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        keypair_policy_name = f"test-keypair-policy-{uuid.uuid4().hex[:8]}"
        user_uuid = uuid.uuid4()
        access_key = AccessKey(f"AKTEST{uuid.uuid4().hex[:14]}")
        group_id = uuid.uuid4()
        agent_id = AgentId(f"test-agent-{uuid.uuid4().hex[:8]}")

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    total_resource_slots=ResourceSlot({
                        "cpu": Decimal("1000"),
                        "mem": Decimal("1048576"),
                    }),
                )
            )
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
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=project_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name=user_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=3,
                )
            )
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name=keypair_policy_name,
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot({
                        "cpu": Decimal("100"),
                        "mem": Decimal("102400"),
                    }),
                    max_concurrent_sessions=10,
                    max_containers_per_session=1,
                    idle_timeout=600,
                    max_session_lifetime=0,
                    allowed_vfolder_hosts={},
                )
            )
            await db_sess.flush()

            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    email=f"net-test-{uuid.uuid4().hex[:8]}@test.com",
                    username=f"net-user-{uuid.uuid4().hex[:8]}",
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    domain_name=domain_name,
                    resource_policy=user_policy_name,
                )
            )
            db_sess.add(
                GroupRow(
                    id=group_id,
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=project_policy_name,
                    integration_id=None,
                )
            )
            db_sess.add(
                AgentRow(
                    id=agent_id,
                    status=AgentStatus.ALIVE,
                    region="local",
                    scaling_group=sg_name,
                    resource_group_id=sg_id,
                    available_slots=ResourceSlot({
                        "cpu": Decimal("10"),
                        "mem": Decimal("10240"),
                    }),
                    occupied_slots=ResourceSlot(),
                    addr="127.0.0.1:6001",
                    version="1.0.0",
                    architecture="x86_64",
                )
            )
            await db_sess.flush()

            db_sess.add(
                KeyPairRow(
                    user_id=f"net-test-{uuid.uuid4().hex[:8]}@test.com",
                    access_key=access_key,
                    secret_key=SecretKey(f"SK{uuid.uuid4().hex[:38]}"),
                    is_active=True,
                    is_admin=False,
                    resource_policy=keypair_policy_name,
                    rate_limit=1000,
                    num_queries=0,
                    user=user_uuid,
                )
            )
            await db_sess.flush()

        yield {
            "domain_id": domain_id,
            "domain_name": domain_name,
            "sg_id": sg_id,
            "sg_name": sg_name,
            "user_uuid": user_uuid,
            "access_key": access_key,
            "group_id": group_id,
            "agent_id": agent_id,
        }

    async def _add_multi_node_persistent_session(
        self,
        db: ExtendedAsyncSAEngine,
        env: dict[str, Any],
        *,
        network_id: str,
    ) -> SessionId:
        """Create a PREPARED multi-node session that explicitly references a PERSISTENT network."""
        session_id = SessionId(uuid.uuid4())
        kernel_id = uuid.uuid4()

        async with db.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    name=f"test-session-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INTERACTIVE,
                    domain_id=env["domain_id"],
                    domain_name=env["domain_name"],
                    group_id=env["group_id"],
                    user_uuid=env["user_uuid"],
                    access_key=env["access_key"],
                    resource_group_id=env["sg_id"],
                    scaling_group_name=env["sg_name"],
                    status=SessionStatus.PREPARED,
                    status_info="prepared",
                    cluster_mode=ClusterMode.MULTI_NODE,
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("2"),
                        "mem": Decimal("4096"),
                    }),
                    created_at=datetime.now(tzutc()),
                    images=["python:3.8"],
                    vfolder_mounts=[],
                    environ={},
                    result=SessionResult.UNDEFINED,
                    network_type=NetworkType.PERSISTENT,
                    network_id=network_id,
                )
            )
            await db_sess.flush()

            db_sess.add(
                KernelRow(
                    id=kernel_id,
                    session_id=session_id,
                    agent=env["agent_id"],
                    agent_addr="127.0.0.1:6001",
                    scaling_group=env["sg_name"],
                    resource_group_id=env["sg_id"],
                    cluster_idx=0,
                    cluster_role="main",
                    cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                    image="python:3.8",
                    architecture="x86_64",
                    registry="docker.io",
                    status=KernelStatus.PREPARED,
                    status_changed=datetime.now(tzutc()),
                    occupied_slots=ResourceSlot(),
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("2"),
                        "mem": Decimal("4096"),
                    }),
                    domain_name=env["domain_name"],
                    group_id=env["group_id"],
                    user_uuid=env["user_uuid"],
                    access_key=env["access_key"],
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

    async def test_persistent_network_not_recreated_on_session_start(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        seeded_environment: dict[str, Any],
    ) -> None:
        pre_created_network_id = "pre-created-overlay-net"
        session_id = await self._add_multi_node_persistent_session(
            db_with_cleanup,
            seeded_environment,
            network_id=pre_created_network_id,
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[SessionConditions.by_ids([session_id])],
        )
        result = await db_source.search_sessions_with_kernels_and_user(querier)

        assert len(result.sessions) == 1
        session = result.sessions[0]
        assert session.session_id == session_id
        assert session.network_type == NetworkType.PERSISTENT
        assert session.network_id == pre_created_network_id
