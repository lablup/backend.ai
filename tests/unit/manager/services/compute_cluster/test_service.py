"""The compute cluster service stores only the kubeconfig the key provider pool returns."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.manager.data.compute_cluster.types import ComputeClusterData, ComputeClusterStatus
from ai.backend.manager.models.compute_cluster.creators import ComputeClusterCreator
from ai.backend.manager.models.compute_cluster.row import COMPUTE_CLUSTER_KUBECONFIG_CONTEXT
from ai.backend.manager.models.compute_cluster.updaters import ComputeClusterUpdater
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.services.compute_cluster.actions.create import (
    CreateComputeClusterAction,
)
from ai.backend.manager.services.compute_cluster.actions.update import (
    UpdateComputeClusterAction,
)
from ai.backend.manager.services.compute_cluster.service import ComputeClusterService
from ai.backend.manager.types import OptionalState

_PLAINTEXT = "apiVersion: v1\nkind: Config\n"
_ENCRYPTED = SecretValue("stands-in-for-ciphertext")


@pytest.fixture
def cluster_id() -> ComputeClusterID:
    return ComputeClusterID(uuid4())


@pytest.fixture
def cluster_data(cluster_id: ComputeClusterID) -> ComputeClusterData:
    now = datetime.now(UTC)
    return ComputeClusterData(
        id=cluster_id,
        name="k8s-a",
        description=None,
        api_server="https://10.0.0.1:6443",
        kubeconfig=_ENCRYPTED,
        namespace_prefix="bai-",
        gateway_addr=None,
        gateway_public_key=None,
        status=ComputeClusterStatus.UNKNOWN,
        status_changed_at=None,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def ops_repository(cluster_data: ComputeClusterData) -> MagicMock:
    repository = MagicMock()
    repository.create_entity = AsyncMock(return_value=cluster_data)
    repository.update = AsyncMock(return_value=cluster_data)
    return repository


@pytest.fixture
def key_provider_pool() -> MagicMock:
    pool = MagicMock()
    pool.encrypt = AsyncMock(return_value=_ENCRYPTED)
    return pool


@pytest.fixture
def service(ops_repository: MagicMock, key_provider_pool: MagicMock) -> ComputeClusterService:
    return ComputeClusterService(ops_repository, key_provider_pool)


class TestCreate:
    async def test_stores_the_encrypted_kubeconfig(
        self,
        service: ComputeClusterService,
        ops_repository: MagicMock,
        key_provider_pool: MagicMock,
    ) -> None:
        await service.create(
            CreateComputeClusterAction(
                name="k8s-a",
                description=None,
                api_server="https://10.0.0.1:6443",
                kubeconfig=_PLAINTEXT,
                namespace_prefix="bai-",
                gateway_addr=None,
                gateway_public_key=None,
            )
        )

        key_provider_pool.encrypt.assert_awaited_once_with(
            _PLAINTEXT, COMPUTE_CLUSTER_KUBECONFIG_CONTEXT
        )
        creator = ops_repository.create_entity.call_args.args[0]
        assert isinstance(creator, ComputeClusterCreator)
        assert creator.kubeconfig is _ENCRYPTED


class TestUpdate:
    async def test_stores_the_encrypted_replacement_kubeconfig(
        self,
        service: ComputeClusterService,
        ops_repository: MagicMock,
        key_provider_pool: MagicMock,
        cluster_id: ComputeClusterID,
    ) -> None:
        await service.update(
            UpdateComputeClusterAction(
                updater=ComputeClusterUpdater(compute_cluster_id=cluster_id),
                kubeconfig=OptionalState.update(_PLAINTEXT),
            )
        )

        key_provider_pool.encrypt.assert_awaited_once_with(
            _PLAINTEXT, COMPUTE_CLUSTER_KUBECONFIG_CONTEXT
        )
        updater = ops_repository.update.call_args.args[0]
        assert updater.build_values()["kubeconfig"] is _ENCRYPTED

    async def test_leaves_the_kubeconfig_alone_when_not_given(
        self,
        service: ComputeClusterService,
        ops_repository: MagicMock,
        key_provider_pool: MagicMock,
        cluster_id: ComputeClusterID,
    ) -> None:
        await service.update(
            UpdateComputeClusterAction(
                updater=ComputeClusterUpdater(
                    compute_cluster_id=cluster_id, api_server=OptionalState.update("https://x")
                ),
            )
        )

        key_provider_pool.encrypt.assert_not_awaited()
        updater = ops_repository.update.call_args.args[0]
        assert "kubeconfig" not in updater.build_values()
