"""The node shapes a compute cluster's gateway reports, stored against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.db_source.db_source import AgentDBSource
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables

_CLUSTER = "k8s-a"
_SHAPES = [{"cpu": "8", "mem": "34359738368"}, {"cpu": "32", "mem": "137438953472"}]


async def _add_agent(
    db: ExtendedAsyncSAEngine, *, driver: str, driver_opts: dict[str, str]
) -> AgentId:
    group = ResourceGroupRow(
        id=ResourceGroupID(uuid.uuid4()),
        name=f"rg-{uuid.uuid4().hex[:8]}",
        driver=driver,
        driver_opts=driver_opts,
        scheduler="fifo",
        scheduler_opts=ResourceGroupOpts(),
    )
    agent_id = AgentId(f"i-{uuid.uuid4().hex[:12]}")
    async with db.begin_session() as db_sess:
        db_sess.add(group)
        await db_sess.flush()
        db_sess.add(
            AgentRow(
                id=agent_id,
                uuid=AgentUUID(uuid.uuid4()),
                status=AgentStatus.ALIVE,
                status_changed=datetime.now(UTC),
                region="local",
                scaling_group=group.name,
                resource_group_id=group.id,
                schedulable=True,
                addr="127.0.0.1:2001",
                architecture="x86_64",
                version="26.10.0",
            )
        )
    return agent_id


async def _stored(db: ExtendedAsyncSAEngine) -> tuple[list[dict[str, str]] | None, datetime]:
    async with db.begin_readonly_session() as db_sess:
        row = (
            await db_sess.execute(
                sa.select(ComputeClusterRow.node_shapes, ComputeClusterRow.updated_at).where(
                    ComputeClusterRow.name == _CLUSTER
                )
            )
        ).one()
        return row.node_shapes, row.updated_at


class TestStoreComputeClusterNodeShapes:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection, [ResourceGroupRow, AgentRow, ComputeClusterRow]
        ):
            async with database_connection.begin_session() as db_sess:
                db_sess.add(
                    ComputeClusterRow(
                        name=_CLUSTER,
                        api_server="https://10.0.0.1:6443",
                        kubeconfig=SecretValue("ciphertext"),
                        namespace_prefix="bai-",
                    )
                )
            yield database_connection

    @pytest.fixture
    def db_source(self, db: ExtendedAsyncSAEngine) -> AgentDBSource:
        return AgentDBSource(db, ShareOpsProvider(db))

    @pytest.fixture
    async def gateway(self, db: ExtendedAsyncSAEngine) -> AgentId:
        return await _add_agent(db, driver="kubernetes", driver_opts={"compute_cluster": _CLUSTER})

    @pytest.fixture
    async def docker_agent(self, db: ExtendedAsyncSAEngine) -> AgentId:
        """An agent of a Docker group whose options happen to name the cluster."""
        return await _add_agent(db, driver="static", driver_opts={"compute_cluster": _CLUSTER})

    async def test_gateway_shapes_are_stored_on_its_cluster(
        self, db: ExtendedAsyncSAEngine, db_source: AgentDBSource, gateway: AgentId
    ) -> None:
        _, updated_at = await _stored(db)

        changed = await db_source.store_compute_cluster_node_shapes(gateway, _SHAPES)

        assert changed is True
        stored, updated_at_after = await _stored(db)
        assert stored == _SHAPES
        # The registration the cached cluster client is built from did not change.
        assert updated_at_after == updated_at

    async def test_unchanged_shapes_write_nothing(
        self, db_source: AgentDBSource, gateway: AgentId
    ) -> None:
        await db_source.store_compute_cluster_node_shapes(gateway, _SHAPES)

        assert await db_source.store_compute_cluster_node_shapes(gateway, _SHAPES) is False

    async def test_a_docker_agent_stores_nothing(
        self, db: ExtendedAsyncSAEngine, db_source: AgentDBSource, docker_agent: AgentId
    ) -> None:
        changed = await db_source.store_compute_cluster_node_shapes(docker_agent, _SHAPES)

        assert changed is False
        stored, _ = await _stored(db)
        assert stored is None
