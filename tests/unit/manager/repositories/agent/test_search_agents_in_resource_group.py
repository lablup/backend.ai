from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.entity.agent import AgentEntityType, AgentUUID
from ai.backend.common.data.entity.resource_group import (
    ResourceGroupEntityType,
    ResourceGroupID,
    ResourceGroupName,
)
from ai.backend.common.data.filter_specs import UUIDInMatchSpec
from ai.backend.common.types import AgentId
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.errors.resource import ResourceGroupNotFound
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.agent.searchable_fields import AgentSearchableFields
from ai.backend.manager.models.agent.searchers import AgentSearcher
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder


async def _add_resource_group(db: ExtendedAsyncSAEngine) -> ResourceGroupRow:
    row = ResourceGroupRow(
        id=ResourceGroupID(uuid.uuid4()),
        name=f"rg-{uuid.uuid4().hex[:8]}",
        driver="static",
        scheduler="fifo",
        scheduler_opts=ResourceGroupOpts(),
    )
    async with db.begin_session() as db_sess:
        db_sess.add(row)
    return row


async def _add_agents(
    db: ExtendedAsyncSAEngine, resource_group: ResourceGroupRow, count: int
) -> list[AgentUUID]:
    agent_uuids = [AgentUUID(uuid.uuid4()) for _ in range(count)]
    async with db.begin_session() as db_sess:
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
        await db_sess.flush()
        for agent_uuid in agent_uuids:
            await VirtualEntitySeeder().create_in(
                db_sess,
                AgentEntityType(),
                agent_uuid,
                [(ResourceGroupEntityType(), resource_group.id)],
            )
    return agent_uuids


class TestSearchAgentsInResourceGroup:
    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                ResourceGroupRow,
                AgentRow,
                VirtualEntityRow,
                ScopeBindingRow,
                EntityMembershipRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def resource_group(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ResourceGroupRow:
        return await _add_resource_group(db_with_cleanup)

    @pytest.fixture
    async def other_resource_group(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> ResourceGroupRow:
        return await _add_resource_group(db_with_cleanup)

    @pytest.fixture
    async def inside_agents(
        self, db_with_cleanup: ExtendedAsyncSAEngine, resource_group: ResourceGroupRow
    ) -> list[AgentUUID]:
        """Three agents of the resource group."""
        return await _add_agents(db_with_cleanup, resource_group, 3)

    @pytest.fixture
    async def outside_agents(
        self, db_with_cleanup: ExtendedAsyncSAEngine, other_resource_group: ResourceGroupRow
    ) -> list[AgentUUID]:
        """One agent of another resource group."""
        return await _add_agents(db_with_cleanup, other_resource_group, 1)

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> AgentRepository:
        return AgentRepository(
            db=db_with_cleanup,
            valkey_image=MagicMock(),
            valkey_live=MagicMock(),
            valkey_stat=MagicMock(),
            config_provider=MagicMock(),
            v2_ops_provider=ShareOpsProvider(db_with_cleanup),
        )

    async def test_only_the_agents_of_the_resource_group_are_found(
        self,
        repository: AgentRepository,
        resource_group: ResourceGroupRow,
        inside_agents: list[AgentUUID],
        outside_agents: list[AgentUUID],
    ) -> None:
        agents = await repository.search_agents_in_resource_group(
            ResourceGroupName(resource_group.name),
            AgentSearcher(
                pagination=NoPagination(),
                conditions=[
                    AgentSearchableFields.own.uuid.filter.in_(
                        UUIDInMatchSpec(values=[*inside_agents, *outside_agents], negated=False)
                    ),
                ],
            ),
        )

        assert {agent.uuid for agent in agents} == set(inside_agents)

    async def test_searching_agents_of_an_unknown_resource_group_raises(
        self, repository: AgentRepository
    ) -> None:
        with pytest.raises(ResourceGroupNotFound):
            await repository.search_agents_in_resource_group(
                ResourceGroupName(f"rg-{uuid.uuid4().hex[:8]}"),
                AgentSearcher(pagination=NoPagination(), conditions=[]),
            )
