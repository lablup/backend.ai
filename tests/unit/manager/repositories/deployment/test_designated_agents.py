from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.errors.service import EndpointNotFound
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.deployment_designated_agent.row import (
    DeploymentDesignatedAgentRow,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.testutils.db import with_tables


class TestDeploymentDesignatedAgents:
    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
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
                EndpointRow,
                DeploymentDesignatedAgentRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def resource_group(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ResourceGroupRow:
        row = ResourceGroupRow(
            id=ResourceGroupID(uuid.uuid4()),
            name=f"rg-{uuid.uuid4().hex[:8]}",
            driver="static",
            scheduler="fifo",
            scheduler_opts=ResourceGroupOpts(),
        )
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(row)
        return row

    @pytest.fixture
    async def deployment_ids(
        self, db_with_cleanup: ExtendedAsyncSAEngine, resource_group: ResourceGroupRow
    ) -> list[DeploymentID]:
        """Two deployments of the resource group."""
        suffix = uuid.uuid4().hex[:8]
        project_id = uuid.uuid4()
        deployment_ids = [DeploymentID(uuid.uuid4()), DeploymentID(uuid.uuid4())]
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=DomainID(uuid.uuid4()),
                    name=f"d-{suffix}",
                    total_resource_slots=ResourceSlot(),
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=f"pp-{suffix}",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            await db_sess.flush()
            db_sess.add(
                ProjectRow(
                    id=project_id,
                    name=f"p-{suffix}",
                    domain_name=f"d-{suffix}",
                    total_resource_slots=ResourceSlot(),
                    resource_policy=f"pp-{suffix}",
                )
            )
            await db_sess.flush()
            for deployment_id in deployment_ids:
                db_sess.add(
                    EndpointRow(
                        id=deployment_id,
                        name=f"ep-{deployment_id.hex[:8]}",
                        created_user=uuid.uuid4(),
                        session_owner=uuid.uuid4(),
                        domain=f"d-{suffix}",
                        project=project_id,
                        resource_group=resource_group.name,
                        lifecycle_stage=EndpointLifecycle.CREATED,
                        replicas=1,
                    )
                )
        return deployment_ids

    @pytest.fixture
    async def agent_uuids(
        self, db_with_cleanup: ExtendedAsyncSAEngine, resource_group: ResourceGroupRow
    ) -> list[AgentUUID]:
        """Three agents of the resource group."""
        agent_uuids = [AgentUUID(uuid.uuid4()) for _ in range(3)]
        async with db_with_cleanup.begin_session() as db_sess:
            for agent_uuid in agent_uuids:
                db_sess.add(
                    AgentRow(
                        id=AgentId(f"i-{agent_uuid.hex[:12]}"),
                        uuid=agent_uuid,
                        status=AgentStatus.ALIVE,
                        status_changed=datetime.now(UTC),
                        region="local",
                        scaling_group=resource_group.name,
                        resource_group_id=resource_group.id,
                        schedulable=True,
                        addr="127.0.0.1:2001",
                        architecture="x86_64",
                        version="26.10.0",
                    )
                )
        return agent_uuids

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> DeploymentRepository:
        return DeploymentRepository(
            db=db_with_cleanup,
            reconcile_ops_provider=ReconcileOpsProvider(db_with_cleanup),
            storage_manager=AsyncMock(),
            valkey_stat=AsyncMock(),
            valkey_live=AsyncMock(),
            valkey_schedule=AsyncMock(),
            permission_check=MagicMock(),
        )

    async def test_replacing_with_two_agents_designates_those_two(
        self,
        repository: DeploymentRepository,
        deployment_ids: list[DeploymentID],
        agent_uuids: list[AgentUUID],
    ) -> None:
        deployment_id = deployment_ids[0]

        await repository.replace_designated_agents(deployment_id, set(agent_uuids[:2]))

        designated = await repository.fetch_designated_agents_by_deployment_ids({deployment_id})
        assert set(designated[deployment_id]) == set(agent_uuids[:2])

    async def test_replacing_again_drops_the_agents_left_out(
        self,
        repository: DeploymentRepository,
        deployment_ids: list[DeploymentID],
        agent_uuids: list[AgentUUID],
    ) -> None:
        deployment_id = deployment_ids[0]
        await repository.replace_designated_agents(deployment_id, set(agent_uuids[:2]))

        await repository.replace_designated_agents(deployment_id, {agent_uuids[2]})

        designated = await repository.fetch_designated_agents_by_deployment_ids({deployment_id})
        assert designated[deployment_id] == [agent_uuids[2]]

    async def test_replacing_with_none_clears_the_designation(
        self,
        repository: DeploymentRepository,
        deployment_ids: list[DeploymentID],
        agent_uuids: list[AgentUUID],
    ) -> None:
        deployment_id = deployment_ids[0]
        await repository.replace_designated_agents(deployment_id, set(agent_uuids[:2]))

        await repository.replace_designated_agents(deployment_id, set())

        designated = await repository.fetch_designated_agents_by_deployment_ids({deployment_id})
        assert designated[deployment_id] == []

    @pytest.mark.parametrize(
        "agent_count",
        [pytest.param(0, id="no-agents"), pytest.param(1, id="one-agent")],
    )
    async def test_replacing_for_a_missing_deployment_raises_not_found(
        self,
        repository: DeploymentRepository,
        agent_uuids: list[AgentUUID],
        agent_count: int,
    ) -> None:
        with pytest.raises(EndpointNotFound):
            await repository.replace_designated_agents(
                DeploymentID(uuid.uuid4()), set(agent_uuids[:agent_count])
            )

    async def test_fetching_many_groups_by_deployment_with_an_empty_list_for_none(
        self,
        repository: DeploymentRepository,
        deployment_ids: list[DeploymentID],
        agent_uuids: list[AgentUUID],
    ) -> None:
        with_agents, without_agents = deployment_ids
        await repository.replace_designated_agents(with_agents, set(agent_uuids[:2]))

        designated = await repository.fetch_designated_agents_by_deployment_ids(set(deployment_ids))

        assert set(designated[with_agents]) == set(agent_uuids[:2])
        assert designated[without_agents] == []

    async def test_deleting_the_deployment_deletes_its_designation(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        repository: DeploymentRepository,
        deployment_ids: list[DeploymentID],
        agent_uuids: list[AgentUUID],
    ) -> None:
        deployment_id = deployment_ids[0]
        await repository.replace_designated_agents(deployment_id, set(agent_uuids[:2]))

        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(sa.delete(EndpointRow).where(EndpointRow.id == deployment_id))

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            remaining = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(DeploymentDesignatedAgentRow)
            )
        assert remaining == 0

    async def test_deleting_an_agent_deletes_only_its_designation(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        repository: DeploymentRepository,
        deployment_ids: list[DeploymentID],
        agent_uuids: list[AgentUUID],
    ) -> None:
        deployment_id = deployment_ids[0]
        await repository.replace_designated_agents(deployment_id, set(agent_uuids[:2]))

        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(sa.delete(AgentRow).where(AgentRow.uuid == agent_uuids[0]))

        designated = await repository.fetch_designated_agents_by_deployment_ids({deployment_id})
        assert designated[deployment_id] == [agent_uuids[1]]
