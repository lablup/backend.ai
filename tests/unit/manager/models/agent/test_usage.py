"""The session usage narrowing the agent read.

The read keeps the agents a kernel of the named session runs on and leaves the rest out.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.agent.types import AgentData
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.agent.searchable_fields import AgentSearchableFields
from ai.backend.manager.models.agent.searchers import AgentSearcher
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.resource_group import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables


@dataclass
class UsageFixture:
    used_agent_uuid: AgentUUID
    unused_agent_uuid: AgentUUID
    session_id: SessionID


class TestAgentUsage:
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
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                SessionRow,
                KernelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def usage(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[UsageFixture, None]:
        """Two agents, one of which runs the session's only kernel."""
        suffix = uuid.uuid4().hex[:8]
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"test-domain-{suffix}"
        resource_group_id = ResourceGroupID(uuid.uuid4())
        resource_group_name = f"test-sgroup-{suffix}"
        user_policy_name = f"test-upolicy-{suffix}"
        project_policy_name = f"test-ppolicy-{suffix}"
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        session_id = SessionID(uuid.uuid4())
        agent_uuids = [AgentUUID(uuid.uuid4()) for _ in range(2)]

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(id=domain_id, name=domain_name, total_resource_slots=ResourceSlot())
            )
            db_sess.add(
                ResourceGroupRow(
                    id=resource_group_id,
                    name=resource_group_name,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name=user_policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=project_policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            await db_sess.flush()

            db_sess.add(
                UserRow(
                    uuid=user_id,
                    email=f"test-{suffix}@test.com",
                    username=f"testuser-{suffix}",
                    password=PasswordInfo(
                        password="test_password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1,
                        salt_size=16,
                    ),
                    domain_id=domain_id,
                    domain_name=domain_name,
                    resource_policy=user_policy_name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                )
            )
            db_sess.add(
                ProjectRow(
                    id=project_id,
                    name=f"project-{suffix}",
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=project_policy_name,
                )
            )
            for index, agent_uuid in enumerate(agent_uuids):
                db_sess.add(
                    AgentRow(
                        id=f"i-agent-{suffix}-{index}",
                        uuid=agent_uuid,
                        scaling_group=resource_group_name,
                        resource_group_id=resource_group_id,
                        region="local",
                        addr=f"tcp://127.0.0.1:600{index}",
                        version="test",
                        architecture="x86_64",
                        compute_plugins={},
                    )
                )
            await db_sess.flush()

            db_sess.add(
                SessionRow(
                    id=session_id,
                    domain_id=domain_id,
                    domain_name=domain_name,
                    group_id=project_id,
                    resource_group_id=resource_group_id,
                    scaling_group_name=resource_group_name,
                    user_uuid=user_id,
                )
            )
            await db_sess.flush()

            db_sess.add(
                KernelRow(
                    id=uuid.uuid4(),
                    session_id=session_id,
                    domain_name=domain_name,
                    group_id=project_id,
                    user_uuid=user_id,
                    repl_in_port=0,
                    repl_out_port=0,
                    stdin_port=0,
                    stdout_port=0,
                    scaling_group=resource_group_name,
                    resource_group_id=resource_group_id,
                    agent=f"i-agent-{suffix}-0",
                )
            )

        yield UsageFixture(
            used_agent_uuid=agent_uuids[0],
            unused_agent_uuid=agent_uuids[1],
            session_id=session_id,
        )

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> OpsRepository[AgentData]:
        return OpsRepository(V2DBOpsProvider(db_with_cleanup))

    async def test_usage_keeps_the_agent_the_session_runs_on(
        self,
        repository: OpsRepository[AgentData],
        usage: UsageFixture,
    ) -> None:
        result = await repository.global_search(
            GlobalSearcher(
                used_by=[AgentSearchableFields.linked.usage.sessions.used_by(usage.session_id)],
                searcher=AgentSearcher(pagination=OffsetPagination(limit=10)),
            )
        )

        assert [item.uuid for item in result.items] == [usage.used_agent_uuid]

    async def test_usage_leaves_out_an_agent_no_kernel_of_the_session_runs_on(
        self,
        repository: OpsRepository[AgentData],
        usage: UsageFixture,
    ) -> None:
        result = await repository.global_search(
            GlobalSearcher(
                used_by=[
                    AgentSearchableFields.linked.usage.sessions.used_by(SessionID(uuid.uuid4()))
                ],
                searcher=AgentSearcher(pagination=OffsetPagination(limit=10)),
            )
        )

        assert result.items == []
