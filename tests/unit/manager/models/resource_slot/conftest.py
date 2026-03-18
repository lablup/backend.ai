from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest

from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def database_with_resource_slot_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Set up tables required for resource slot normalization tests."""
    async with with_tables(
        database_connection,
        [
            # FK dependency order: parents before children
            DomainRow,
            ScalingGroupRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            UserRoleRow,
            UserRow,
            KeyPairRow,
            GroupRow,
            AgentRow,
            SessionRow,
            KernelRow,
            # Resource slot tables
            ResourceSlotTypeRow,
            AgentResourceRow,
            ResourceAllocationRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def domain_name(
    database_with_resource_slot_tables: ExtendedAsyncSAEngine,
) -> AsyncGenerator[str, None]:
    name = "test-domain"
    async with database_with_resource_slot_tables.begin_session() as db_sess:
        db_sess.add(DomainRow(name=name))
    yield name


@pytest.fixture
async def scaling_group(
    database_with_resource_slot_tables: ExtendedAsyncSAEngine,
) -> AsyncGenerator[str, None]:
    name = "default"
    async with database_with_resource_slot_tables.begin_session() as db_sess:
        db_sess.add(
            ScalingGroupRow(
                name=name,
                description="Test scaling group",
                is_active=True,
                is_public=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
                use_host_network=False,
            )
        )
    yield name


@pytest.fixture
async def user_resource_policy(
    database_with_resource_slot_tables: ExtendedAsyncSAEngine,
) -> AsyncGenerator[str, None]:
    name = "test-user-policy"
    async with database_with_resource_slot_tables.begin_session() as db_sess:
        db_sess.add(
            UserResourcePolicyRow(
                name=name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
        )
    yield name


@pytest.fixture
async def project_resource_policy(
    database_with_resource_slot_tables: ExtendedAsyncSAEngine,
) -> AsyncGenerator[str, None]:
    name = "test-project-policy"
    async with database_with_resource_slot_tables.begin_session() as db_sess:
        db_sess.add(
            ProjectResourcePolicyRow(
                name=name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_network_count=5,
            )
        )
    yield name


@pytest.fixture
async def user_uuid(
    database_with_resource_slot_tables: ExtendedAsyncSAEngine,
    domain_name: str,
    user_resource_policy: str,
) -> AsyncGenerator[uuid.UUID, None]:
    user_id = uuid.uuid4()
    password_info = PasswordInfo(
        password="test_password",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )
    async with database_with_resource_slot_tables.begin_session() as db_sess:
        db_sess.add(
            UserRow(
                uuid=user_id,
                username="testuser",
                email="test@example.com",
                password=password_info,
                domain_name=domain_name,
                resource_policy=user_resource_policy,
            )
        )
    yield user_id


@pytest.fixture
async def project_id(
    database_with_resource_slot_tables: ExtendedAsyncSAEngine,
    domain_name: str,
    project_resource_policy: str,
) -> AsyncGenerator[uuid.UUID, None]:
    group_id = uuid.uuid4()
    async with database_with_resource_slot_tables.begin_session() as db_sess:
        db_sess.add(
            GroupRow(
                id=group_id,
                name="test-project",
                domain_name=domain_name,
                resource_policy=project_resource_policy,
            )
        )
    yield group_id


@pytest.fixture
async def agent_id(
    database_with_resource_slot_tables: ExtendedAsyncSAEngine,
    scaling_group: str,
) -> AsyncGenerator[str, None]:
    aid = "i-test-agent-001"
    async with database_with_resource_slot_tables.begin_session() as db_sess:
        db_sess.add(
            AgentRow(
                id=aid,
                scaling_group=scaling_group,
                region="local",
                addr="tcp://127.0.0.1:6001",
                available_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("4294967296")}),
                occupied_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1073741824")}),
                first_contact=None,
                lost_at=None,
                version="test",
                architecture="x86_64",
                compute_plugins={},
            )
        )
    yield aid


@pytest.fixture
async def kernel_id(
    database_with_resource_slot_tables: ExtendedAsyncSAEngine,
    domain_name: str,
    project_id: uuid.UUID,
    user_uuid: uuid.UUID,
    scaling_group: str,
    agent_id: str,
) -> AsyncGenerator[uuid.UUID, None]:
    kid = uuid.uuid4()
    sid = uuid.uuid4()
    async with database_with_resource_slot_tables.begin_session() as db_sess:
        db_sess.add(
            SessionRow(
                id=sid,
                domain_name=domain_name,
                group_id=project_id,
                user_uuid=user_uuid,
                occupying_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1073741824")}),
                requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1073741824")}),
            )
        )
        await db_sess.flush()
        db_sess.add(
            KernelRow(
                id=kid,
                session_id=sid,
                domain_name=domain_name,
                group_id=project_id,
                user_uuid=user_uuid,
                occupied_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1073741824")}),
                requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1073741824")}),
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
                scaling_group=scaling_group,
                agent=agent_id,
            )
        )
    yield kid
