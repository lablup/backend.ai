"""Kubernetes resource groups against a real database: the batched compute cluster lookups of
the scheduler, the driver guards of a resource group update, and the compute cluster purge
conflict."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId, ClusterMode, SessionId, SessionResult, SessionTypes
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.compute_cluster import (
    ComputeClusterInUse,
    ComputeClusterNotFound,
    InvalidResourceGroupDriverOptions,
    ResourceGroupDriverChangeConflict,
)
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.compute_cluster.purgers import ComputeClusterPurger
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow
from ai.backend.manager.models.resource_group.creators import ResourceGroupCreator
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.updaters import ResourceGroupUpdater
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFixtureData

_CLUSTER = "k8s-a"
_OTHER_CLUSTER = "k8s-b"


@pytest.fixture
async def cluster_db(
    db_with_cleanup: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine]:
    async with with_tables(db_with_cleanup, [ComputeClusterRow]):
        yield db_with_cleanup


@pytest.fixture
async def cluster_ids(cluster_db: ExtendedAsyncSAEngine) -> dict[str, ComputeClusterID]:
    ids: dict[str, ComputeClusterID] = {}
    async with cluster_db.begin_session() as db_sess:
        for name in (_CLUSTER, _OTHER_CLUSTER):
            row = ComputeClusterRow(
                name=name,
                api_server="https://10.0.0.1:6443",
                kubeconfig=SecretValue("ciphertext"),
                namespace_prefix="bai-",
            )
            db_sess.add(row)
            await db_sess.flush()
            ids[name] = row.id
    return ids


@pytest.fixture
async def kubernetes_group(
    cluster_db: ExtendedAsyncSAEngine,
    cluster_ids: dict[str, ComputeClusterID],
    test_scaling_group_name: str,
) -> str:
    """The conftest's resource group, switched to the `kubernetes` driver on `k8s-a`."""
    async with cluster_db.begin_session() as db_sess:
        await db_sess.execute(
            sa.update(ResourceGroupRow)
            .where(ResourceGroupRow.name == test_scaling_group_name)
            .values(
                driver="kubernetes",
                driver_opts={"compute_cluster": _CLUSTER, "system_namespace": "bai-sys"},
            )
        )
    return test_scaling_group_name


@pytest.fixture
async def gateway_agent(
    cluster_db: ExtendedAsyncSAEngine,
    kubernetes_group: str,
    test_scaling_group_id: ResourceGroupID,
) -> AgentId:
    agent_id = AgentId(f"gateway-{uuid.uuid4().hex[:8]}")
    async with cluster_db.begin_session() as db_sess:
        db_sess.add(
            AgentRow(
                id=agent_id,
                status=AgentStatus.ALIVE,
                region="local",
                scaling_group=kubernetes_group,
                resource_group_id=test_scaling_group_id,
                addr="127.0.0.1:6001",
                version="1.0.0",
                architecture="x86_64",
            )
        )
    return agent_id


@pytest.fixture
def db_source(cluster_db: ExtendedAsyncSAEngine) -> ScheduleDBSource:
    return ScheduleDBSource(
        cluster_db,
        ReconcileOpsProvider(cluster_db),
        KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )


@pytest.fixture
def resource_group_repository(cluster_db: ExtendedAsyncSAEngine) -> ResourceGroupRepository:
    return ResourceGroupRepository(cluster_db, V2DBOpsProvider(cluster_db))


async def _add_session(
    db: ExtendedAsyncSAEngine,
    *,
    status: SessionStatus,
    resource_group: str,
    resource_group_id: ResourceGroupID,
    domain: DomainFixtureData,
    group_id: uuid.UUID,
    user_uuid: uuid.UUID,
) -> None:
    async with db.begin_session() as db_sess:
        db_sess.add(
            SessionRow(
                id=SessionId(uuid.uuid4()),
                name=f"s-{uuid.uuid4().hex[:8]}",
                session_type=SessionTypes.INTERACTIVE,
                domain_id=domain.domain_id,
                domain_name=domain.domain_name,
                group_id=group_id,
                user_uuid=user_uuid,
                resource_group_id=resource_group_id,
                scaling_group_name=resource_group,
                status=status,
                cluster_mode=ClusterMode.SINGLE_NODE,
                created_at=datetime.now(tzutc()),
                images=["python:3.8"],
                vfolder_mounts=[],
                environ={},
                result=SessionResult.UNDEFINED,
            )
        )


class TestComputeClusterLookups:
    async def test_agents_lookup_returns_only_kubernetes_gateways(
        self,
        db_source: ScheduleDBSource,
        gateway_agent: AgentId,
        cluster_ids: dict[str, ComputeClusterID],
        kubernetes_group: str,
    ) -> None:
        other = AgentId("agent-of-a-static-group")

        found = await db_source.get_compute_clusters_of_agents([gateway_agent, other])

        assert list(found) == [gateway_agent]
        entry = found[gateway_agent]
        assert entry.resource_group == kubernetes_group
        assert entry.cluster is not None
        assert entry.cluster.id == cluster_ids[_CLUSTER]
        assert entry.system_namespace == "bai-sys"

    async def test_resource_groups_lookup_skips_static_groups(
        self,
        db_source: ScheduleDBSource,
        cluster_db: ExtendedAsyncSAEngine,
        kubernetes_group: str,
    ) -> None:
        found = await db_source.get_compute_clusters_of_resource_groups([
            kubernetes_group,
            "no-such-group",
        ])

        assert list(found) == [kubernetes_group]

    async def test_an_unregistered_cluster_is_reported_as_none(
        self,
        db_source: ScheduleDBSource,
        cluster_db: ExtendedAsyncSAEngine,
        kubernetes_group: str,
    ) -> None:
        async with cluster_db.begin_session() as db_sess:
            await db_sess.execute(sa.delete(ComputeClusterRow))

        found = await db_source.get_compute_clusters_of_resource_groups([kubernetes_group])

        assert found[kubernetes_group].cluster is None
        assert found[kubernetes_group].cluster_name == _CLUSTER


class TestResourceGroupDriverGuards:
    async def test_empty_driver_opts_on_a_kubernetes_group_is_rejected(
        self,
        resource_group_repository: ResourceGroupRepository,
        kubernetes_group: str,
        test_scaling_group_id: ResourceGroupID,
    ) -> None:
        with pytest.raises(InvalidResourceGroupDriverOptions):
            await resource_group_repository.update_resource_group(
                ResourceGroupUpdater(
                    resource_group_id=test_scaling_group_id,
                    driver_opts=OptionalState.update({}),
                )
            )

    async def test_an_unregistered_cluster_is_rejected(
        self,
        resource_group_repository: ResourceGroupRepository,
        kubernetes_group: str,
        test_scaling_group_id: ResourceGroupID,
    ) -> None:
        with pytest.raises(ComputeClusterNotFound):
            await resource_group_repository.update_resource_group(
                ResourceGroupUpdater(
                    resource_group_id=test_scaling_group_id,
                    driver_opts=OptionalState.update({"compute_cluster": "missing"}),
                )
            )

    async def test_cluster_change_with_live_sessions_is_rejected(
        self,
        resource_group_repository: ResourceGroupRepository,
        cluster_db: ExtendedAsyncSAEngine,
        kubernetes_group: str,
        test_scaling_group_id: ResourceGroupID,
        test_domain: DomainFixtureData,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> None:
        await _add_session(
            cluster_db,
            status=SessionStatus.RUNNING,
            resource_group=kubernetes_group,
            resource_group_id=test_scaling_group_id,
            domain=test_domain,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
        )

        with pytest.raises(ResourceGroupDriverChangeConflict):
            await resource_group_repository.update_resource_group(
                ResourceGroupUpdater(
                    resource_group_id=test_scaling_group_id,
                    driver_opts=OptionalState.update({"compute_cluster": _OTHER_CLUSTER}),
                )
            )
        with pytest.raises(ResourceGroupDriverChangeConflict):
            await resource_group_repository.update_resource_group(
                ResourceGroupUpdater(
                    resource_group_id=test_scaling_group_id,
                    driver=OptionalState.update("static"),
                    driver_opts=OptionalState.update({}),
                )
            )

    async def test_other_fields_change_with_live_sessions(
        self,
        resource_group_repository: ResourceGroupRepository,
        cluster_db: ExtendedAsyncSAEngine,
        kubernetes_group: str,
        test_scaling_group_id: ResourceGroupID,
        test_domain: DomainFixtureData,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> None:
        await _add_session(
            cluster_db,
            status=SessionStatus.RUNNING,
            resource_group=kubernetes_group,
            resource_group_id=test_scaling_group_id,
            domain=test_domain,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
        )

        updated = await resource_group_repository.update_resource_group(
            ResourceGroupUpdater(
                resource_group_id=test_scaling_group_id,
                description=TriState.update("still here"),
                driver_opts=OptionalState.update({
                    "compute_cluster": _CLUSTER,
                    "system_namespace": "other-sys",
                }),
            )
        )

        assert updated.driver.options["system_namespace"] == "other-sys"

    async def test_cluster_change_after_sessions_ended(
        self,
        resource_group_repository: ResourceGroupRepository,
        cluster_db: ExtendedAsyncSAEngine,
        kubernetes_group: str,
        test_scaling_group_id: ResourceGroupID,
        test_domain: DomainFixtureData,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> None:
        await _add_session(
            cluster_db,
            status=SessionStatus.TERMINATED,
            resource_group=kubernetes_group,
            resource_group_id=test_scaling_group_id,
            domain=test_domain,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
        )

        updated = await resource_group_repository.update_resource_group(
            ResourceGroupUpdater(
                resource_group_id=test_scaling_group_id,
                driver_opts=OptionalState.update({"compute_cluster": _OTHER_CLUSTER}),
            )
        )

        assert updated.driver.options["compute_cluster"] == _OTHER_CLUSTER

    async def test_create_with_an_unregistered_cluster_is_rejected(
        self,
        resource_group_repository: ResourceGroupRepository,
        cluster_ids: dict[str, ComputeClusterID],
    ) -> None:
        with pytest.raises(ComputeClusterNotFound):
            await resource_group_repository.create_resource_group(
                ResourceGroupCreator(
                    name=f"rg-{uuid.uuid4().hex[:8]}",
                    driver="kubernetes",
                    scheduler="fifo",
                    driver_opts={"compute_cluster": "missing"},
                )
            )


class TestComputeClusterPurgeConflict:
    async def test_a_cluster_named_by_a_resource_group_is_not_purged(
        self,
        cluster_db: ExtendedAsyncSAEngine,
        cluster_ids: dict[str, ComputeClusterID],
        kubernetes_group: str,
    ) -> None:
        with pytest.raises(ComputeClusterInUse):
            async with V2DBOpsProvider(cluster_db).write_ops() as w:
                await w.purge_entity(ComputeClusterPurger(compute_cluster_id=cluster_ids[_CLUSTER]))
