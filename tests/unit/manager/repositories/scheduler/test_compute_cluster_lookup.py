"""Kubernetes resource groups against a real database: the batched compute cluster lookups of
the scheduler, the driver guards of a resource group update, and the compute cluster purge
conflict."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId, ClusterMode, SessionId, SessionResult, SessionTypes
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.compute_cluster.types import ComputeClusterStatus
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
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.resource_group.creators import ResourceGroupCreator
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.updaters import ResourceGroupUpdater
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.repositories.ops.v2.compute_cluster.provider import (
    ComputeClusterOpsProvider,
)
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
    # The purge tears the cluster's graph down: memberships, bindings, labels and shares.
    async with with_tables(
        db_with_cleanup,
        [
            ComputeClusterRow,
            EntityMembershipRow,
            EntityMembershipCapRow,
            EntityMembershipFieldRow,
            ScopeBindingRow,
            EntityLabelRow,
            EntityShareRow,
        ],
    ):
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


def _session_row(
    *,
    status: SessionStatus,
    resource_group: str,
    resource_group_id: ResourceGroupID,
    domain: DomainFixtureData,
    group_id: uuid.UUID,
    user_uuid: uuid.UUID,
) -> SessionRow:
    return SessionRow(
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
            _session_row(
                status=status,
                resource_group=resource_group,
                resource_group_id=resource_group_id,
                domain=domain,
                group_id=group_id,
                user_uuid=user_uuid,
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


class TestComputeClusterStatusUpdate:
    async def test_status_changes_without_touching_the_registration(
        self,
        db_source: ScheduleDBSource,
        cluster_db: ExtendedAsyncSAEngine,
        cluster_ids: dict[str, ComputeClusterID],
    ) -> None:
        cluster_id = cluster_ids[_CLUSTER]
        async with cluster_db.begin_readonly_session() as db_sess:
            before = await db_sess.scalar(
                sa.select(ComputeClusterRow.updated_at).where(ComputeClusterRow.id == cluster_id)
            )

        changed = await db_source.update_compute_cluster_status(
            cluster_id, ComputeClusterStatus.LOST
        )
        unchanged = await db_source.update_compute_cluster_status(
            cluster_id, ComputeClusterStatus.LOST
        )

        assert (changed, unchanged) == (True, False)
        async with cluster_db.begin_readonly_session() as db_sess:
            row = (
                await db_sess.execute(
                    sa.select(
                        ComputeClusterRow.status,
                        ComputeClusterRow.status_changed_at,
                        ComputeClusterRow.updated_at,
                    ).where(ComputeClusterRow.id == cluster_id)
                )
            ).one()
        assert row.status == ComputeClusterStatus.LOST
        assert row.status_changed_at is not None
        assert row.updated_at == before


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

    async def test_purge_through_the_repository_removes_an_unnamed_cluster(
        self,
        resource_group_repository: ResourceGroupRepository,
        cluster_ids: dict[str, ComputeClusterID],
        kubernetes_group: str,
    ) -> None:
        purged = await resource_group_repository.purge_compute_cluster(
            ComputeClusterPurger(compute_cluster_id=cluster_ids[_OTHER_CLUSTER])
        )

        assert purged.name == _OTHER_CLUSTER

    async def test_purge_of_a_missing_cluster_is_not_found(
        self, resource_group_repository: ResourceGroupRepository
    ) -> None:
        with pytest.raises(ComputeClusterNotFound):
            await resource_group_repository.purge_compute_cluster(
                ComputeClusterPurger(compute_cluster_id=ComputeClusterID(uuid.uuid4()))
            )


async def _blocked(task: asyncio.Task[Any]) -> bool:
    """Whether the task is still waiting a moment after it started."""
    done, _ = await asyncio.wait({task}, timeout=0.5)
    return not done


class TestConcurrentWrites:
    """A resource group write and a compute cluster purge, or a session enqueue and a driver
    change, take row locks in one order so neither acts on what the other has not
    committed yet."""

    async def test_purge_waits_for_a_group_starting_to_name_the_cluster(
        self,
        cluster_db: ExtendedAsyncSAEngine,
        resource_group_repository: ResourceGroupRepository,
        cluster_ids: dict[str, ComputeClusterID],
        test_scaling_group_name: str,
        test_scaling_group_id: ResourceGroupID,
    ) -> None:
        held = asyncio.Event()
        release = asyncio.Event()

        async def name_the_cluster() -> None:
            async with ComputeClusterOpsProvider(cluster_db).write_ops() as w:
                assert await w.share_lock_compute_cluster(_OTHER_CLUSTER)
                await w.lock_resource_group(test_scaling_group_id)
                assert await w.update_data(
                    ResourceGroupUpdater(
                        resource_group_id=test_scaling_group_id,
                        driver=OptionalState.update("kubernetes"),
                        driver_opts=OptionalState.update({"compute_cluster": _OTHER_CLUSTER}),
                    )
                )
                held.set()
                await release.wait()

        writer = asyncio.create_task(name_the_cluster())
        await held.wait()
        purge = asyncio.create_task(
            resource_group_repository.purge_compute_cluster(
                ComputeClusterPurger(compute_cluster_id=cluster_ids[_OTHER_CLUSTER])
            )
        )

        assert await _blocked(purge)
        release.set()
        await writer
        with pytest.raises(ComputeClusterInUse):
            await purge

    async def test_driver_change_waits_for_the_enqueue_lock(
        self,
        cluster_db: ExtendedAsyncSAEngine,
        resource_group_repository: ResourceGroupRepository,
        kubernetes_group: str,
        test_scaling_group_id: ResourceGroupID,
    ) -> None:
        held = asyncio.Event()
        release = asyncio.Event()

        async def enqueue() -> None:
            async with ReconcileOpsProvider(cluster_db).write_ops() as w:
                await w.share_lock_kubernetes_resource_group(test_scaling_group_id)
                held.set()
                await release.wait()

        writer = asyncio.create_task(enqueue())
        await held.wait()
        change = asyncio.create_task(
            resource_group_repository.update_resource_group(
                ResourceGroupUpdater(
                    resource_group_id=test_scaling_group_id,
                    driver_opts=OptionalState.update({"compute_cluster": _OTHER_CLUSTER}),
                )
            )
        )

        assert await _blocked(change)
        release.set()
        await writer
        updated = await change
        assert updated.driver.options["compute_cluster"] == _OTHER_CLUSTER

    async def test_driver_change_sees_a_session_committed_while_it_waited(
        self,
        cluster_db: ExtendedAsyncSAEngine,
        resource_group_repository: ResourceGroupRepository,
        kubernetes_group: str,
        test_scaling_group_id: ResourceGroupID,
        test_domain: DomainFixtureData,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> None:
        held = asyncio.Event()
        release = asyncio.Event()

        async def enqueue() -> None:
            async with cluster_db.begin_session() as db_sess:
                await db_sess.execute(
                    sa.select(ResourceGroupRow.id)
                    .where(ResourceGroupRow.id == test_scaling_group_id)
                    .with_for_update(read=True)
                )
                db_sess.add(
                    _session_row(
                        status=SessionStatus.PENDING,
                        resource_group=kubernetes_group,
                        resource_group_id=test_scaling_group_id,
                        domain=test_domain,
                        group_id=test_group_id,
                        user_uuid=test_user_uuid,
                    )
                )
                await db_sess.flush()
                held.set()
                await release.wait()

        writer = asyncio.create_task(enqueue())
        await held.wait()
        change = asyncio.create_task(
            resource_group_repository.update_resource_group(
                ResourceGroupUpdater(
                    resource_group_id=test_scaling_group_id,
                    driver_opts=OptionalState.update({"compute_cluster": _OTHER_CLUSTER}),
                )
            )
        )

        assert await _blocked(change)
        release.set()
        await writer
        with pytest.raises(ResourceGroupDriverChangeConflict):
            await change
