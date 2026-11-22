"""The compute cluster resolver lends one client per cluster and closes it only when unused."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.manager.data.compute_cluster.types import (
    ComputeClusterData,
    ComputeClusterStatus,
    ResourceGroupComputeCluster,
)
from ai.backend.manager.errors.compute_cluster import (
    ComputeClusterLost,
    ComputeClusterNotFound,
    KubernetesResourceGroupDisabled,
)
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.sokovan.scheduler.compute_cluster import ComputeClusterResolver


@pytest.fixture
def cluster() -> ComputeClusterData:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return ComputeClusterData(
        id=ComputeClusterID(uuid4()),
        name="k8s-a",
        description=None,
        api_server="https://10.0.0.1:6443",
        kubeconfig=SecretValue("ciphertext"),
        namespace_prefix="bai-",
        gateway_addr=None,
        gateway_public_key=None,
        status=ComputeClusterStatus.ALIVE,
        status_changed_at=None,
        created_at=now,
        updated_at=now,
    )


def _found(cluster: ComputeClusterData | None) -> ResourceGroupComputeCluster:
    return ResourceGroupComputeCluster(
        resource_group="rg",
        cluster_name="k8s-a",
        cluster=cluster,
        scheduler="sokovan",
        system_namespace="bai-system",
    )


@pytest.fixture
def config_provider() -> MagicMock:
    provider = MagicMock()
    provider.config.kubernetes.enabled = True
    return provider


@pytest.fixture
def client_factory() -> AsyncMock:
    return AsyncMock(side_effect=lambda _kubeconfig: AsyncMock())


@pytest.fixture
def resolver(config_provider: MagicMock, client_factory: AsyncMock) -> ComputeClusterResolver:
    key_provider_pool = MagicMock()
    key_provider_pool.decrypt = AsyncMock(return_value="kubeconfig")
    return ComputeClusterResolver(
        AsyncMock(), key_provider_pool, config_provider, client_factory=client_factory
    )


class TestConnect:
    async def test_reuses_the_client_while_the_registration_is_unchanged(
        self,
        resolver: ComputeClusterResolver,
        client_factory: AsyncMock,
        cluster: ComputeClusterData,
    ) -> None:
        async with resolver.connect(_found(cluster), cluster) as first:
            pass
        async with resolver.connect(_found(cluster), cluster) as second:
            pass

        assert first.client is second.client
        assert second.system_namespace == "bai-system"
        client_factory.assert_awaited_once()

    async def test_a_replaced_client_is_closed_only_after_its_last_user(
        self,
        resolver: ComputeClusterResolver,
        cluster: ComputeClusterData,
    ) -> None:
        updated = replace(cluster, updated_at=cluster.updated_at + timedelta(seconds=1))
        released = asyncio.Event()

        async def hold() -> AsyncMock:
            async with resolver.connect(_found(cluster), cluster) as target:
                await released.wait()
                client = target.client
                assert isinstance(client, AsyncMock)
                client.close.assert_not_awaited()
                return client

        holder = asyncio.create_task(hold())
        await asyncio.sleep(0)
        async with resolver.connect(_found(updated), updated) as fresh:
            assert fresh.client is not None
        released.set()
        old_client = await holder

        old_client.close.assert_awaited_once()

    async def test_close_defers_a_lent_client(
        self,
        resolver: ComputeClusterResolver,
        cluster: ComputeClusterData,
    ) -> None:
        async with resolver.connect(_found(cluster), cluster) as target:
            await resolver.close()
            client = target.client
            assert isinstance(client, AsyncMock)
            client.close.assert_not_awaited()

        client.close.assert_awaited_once()


class TestCheckLaunchable:
    def test_returns_an_alive_cluster(
        self, resolver: ComputeClusterResolver, cluster: ComputeClusterData
    ) -> None:
        assert resolver.check_launchable(_found(cluster)) is cluster

    def test_refuses_a_lost_cluster(
        self, resolver: ComputeClusterResolver, cluster: ComputeClusterData
    ) -> None:
        lost = replace(cluster, status=ComputeClusterStatus.LOST)
        with pytest.raises(ComputeClusterLost):
            resolver.check_launchable(_found(lost))

    def test_refuses_an_unregistered_cluster(self, resolver: ComputeClusterResolver) -> None:
        with pytest.raises(ComputeClusterNotFound):
            resolver.check_launchable(_found(None))

    def test_refuses_when_kubernetes_is_disabled(
        self,
        resolver: ComputeClusterResolver,
        config_provider: MagicMock,
        cluster: ComputeClusterData,
    ) -> None:
        config_provider.config.kubernetes.enabled = False
        with pytest.raises(KubernetesResourceGroupDisabled):
            resolver.check_launchable(_found(cluster))
