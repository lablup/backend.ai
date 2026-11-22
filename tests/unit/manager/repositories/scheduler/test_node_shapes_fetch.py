"""The node shapes a scheduling run reads for a `kubernetes` resource group, and only for one."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.fixtures import DomainFixtureData

from .conftest import create_pending_session_with_kernels

_CLUSTER = "k8s-a"


@pytest.fixture
async def cluster_with_shapes(db_with_cleanup: ExtendedAsyncSAEngine) -> str:
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(
            ComputeClusterRow(
                name=_CLUSTER,
                api_server="https://10.0.0.1:6443",
                kubeconfig=SecretValue("ciphertext"),
                namespace_prefix="bai-",
                node_shapes=[{"cpu": "8", "mem": "34359738368"}],
            )
        )
    return _CLUSTER


@pytest.fixture
async def pending_session(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_domain_id: DomainID,
    test_domain: DomainFixtureData,
    test_scaling_group_id: ResourceGroupID,
    test_scaling_group_name: str,
    test_group_id: uuid.UUID,
    test_user_uuid: uuid.UUID,
    test_access_key: AccessKey,
    test_agent_id: str,
    resource_slot_types: None,
) -> None:
    await create_pending_session_with_kernels(
        db_with_cleanup,
        domain_id=test_domain_id,
        domain_name=test_domain.domain_name,
        resource_group_id=test_scaling_group_id,
        resource_group_name=test_scaling_group_name,
        group_id=test_group_id,
        user_uuid=test_user_uuid,
        access_key=test_access_key,
        agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
    )


async def _set_driver(
    db: ExtendedAsyncSAEngine, resource_group: str, driver: str, cluster: str
) -> None:
    async with db.begin_session() as db_sess:
        await db_sess.execute(
            sa.update(ResourceGroupRow)
            .where(ResourceGroupRow.name == resource_group)
            .values(driver=driver, driver_opts={"compute_cluster": cluster})
        )


@pytest.fixture
def db_source(db_with_cleanup: ExtendedAsyncSAEngine) -> ScheduleDBSource:
    return ScheduleDBSource(
        db_with_cleanup,
        ReconcileOpsProvider(db_with_cleanup),
        KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )


class TestNodeShapesInSchedulingFetch:
    async def test_a_kubernetes_group_reads_its_cluster_shapes(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        cluster_with_shapes: str,
        pending_session: None,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
    ) -> None:
        await _set_driver(db_with_cleanup, test_scaling_group_name, "kubernetes", _CLUSTER)

        fetch = await db_source.fetch_scheduling_fetch(test_scaling_group_id)

        assert fetch is not None
        assert fetch.node_shapes == (
            {ResourceSlotName("cpu"): Decimal("8"), ResourceSlotName("mem"): Decimal(34359738368)},
        )

    async def test_a_docker_group_reads_no_shapes(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        cluster_with_shapes: str,
        pending_session: None,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
    ) -> None:
        """Even options naming the cluster do not make a Docker group read its shapes."""
        await _set_driver(db_with_cleanup, test_scaling_group_name, "static", _CLUSTER)

        fetch = await db_source.fetch_scheduling_fetch(test_scaling_group_id)

        assert fetch is not None
        assert fetch.node_shapes is None
