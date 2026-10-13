from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.storage.backend.netapp.check import (
    NetAppBackendStatusCheck,
    NetAppBackendStatusCheckArgs,
)
from ai.backend.common.storage.client.netapp.client import NetAppClient
from ai.backend.common.storage.client.netapp.types import NetAppCluster


class TestNetAppBackendStatusCheck:
    @pytest.fixture
    def backend_id(self) -> StorageBackendID:
        return StorageBackendID(uuid.uuid4())

    @pytest.fixture
    def observed(self) -> NetAppCluster:
        return NetAppCluster(cluster_name="ontap01", cluster_uuid="uuid-1", version="9.13.1")

    @pytest.fixture
    def client(self) -> MagicMock:
        return MagicMock(spec=NetAppClient)

    @pytest.fixture
    def responding_client(self, client: MagicMock, observed: NetAppCluster) -> MagicMock:
        client.get_cluster.return_value = observed
        return client

    @pytest.fixture
    def failing_client(self, client: MagicMock) -> MagicMock:
        client.get_cluster.side_effect = RuntimeError("connection refused")
        return client

    @pytest.fixture
    def client_failing_after_success(self, client: MagicMock, observed: NetAppCluster) -> MagicMock:
        client.get_cluster.side_effect = [observed, RuntimeError("connection refused")]
        return client

    @pytest.fixture
    def check(self, backend_id: StorageBackendID, client: MagicMock) -> NetAppBackendStatusCheck:
        return NetAppBackendStatusCheck(
            NetAppBackendStatusCheckArgs(backend_id=backend_id, client=client)
        )

    def test_id_is_backend_id(
        self, check: NetAppBackendStatusCheck, backend_id: StorageBackendID
    ) -> None:
        assert check.id() == backend_id

    def test_latest_is_none_before_any_check(self, check: NetAppBackendStatusCheck) -> None:
        assert check.latest() is None

    def test_records_what_the_client_observed(
        self,
        responding_client: MagicMock,
        check: NetAppBackendStatusCheck,
        observed: NetAppCluster,
    ) -> None:
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is None
        assert result.duration is not None
        assert result.cluster_name == observed.cluster_name
        assert result.cluster_uuid == observed.cluster_uuid
        assert result.version == observed.version

    def test_records_error_when_the_client_raises(
        self,
        failing_client: MagicMock,
        check: NetAppBackendStatusCheck,
    ) -> None:
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg == "connection refused"
        assert result.duration is not None
        assert result.cluster_name is None
        assert result.cluster_uuid is None
        assert result.version is None

    def test_failure_replaces_an_earlier_observation(
        self,
        client_failing_after_success: MagicMock,
        check: NetAppBackendStatusCheck,
    ) -> None:
        check.check_status()
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg == "connection refused"
        assert result.cluster_name is None
        assert result.cluster_uuid is None
        assert result.version is None
