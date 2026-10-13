from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.storage.backend.vast.check import (
    VASTBackendStatusCheck,
    VASTBackendStatusCheckArgs,
)
from ai.backend.common.storage.client.vast.client import VASTClient
from ai.backend.common.storage.client.vast.types import VASTCluster


class TestVASTBackendStatusCheck:
    @pytest.fixture
    def backend_id(self) -> StorageBackendID:
        return StorageBackendID(uuid.uuid4())

    @pytest.fixture
    def observed(self) -> VASTCluster:
        return VASTCluster(cluster_name="vast01", state="ONLINE", guid="guid-1")

    @pytest.fixture
    def client(self) -> MagicMock:
        return MagicMock(spec=VASTClient)

    @pytest.fixture
    def responding_client(self, client: MagicMock, observed: VASTCluster) -> MagicMock:
        client.get_cluster.return_value = observed
        return client

    @pytest.fixture
    def failing_client(self, client: MagicMock) -> MagicMock:
        client.get_cluster.side_effect = RuntimeError("connection refused")
        return client

    @pytest.fixture
    def client_failing_after_success(self, client: MagicMock, observed: VASTCluster) -> MagicMock:
        client.get_cluster.side_effect = [observed, RuntimeError("connection refused")]
        return client

    @pytest.fixture
    def check(self, backend_id: StorageBackendID, client: MagicMock) -> VASTBackendStatusCheck:
        return VASTBackendStatusCheck(
            VASTBackendStatusCheckArgs(backend_id=backend_id, client=client)
        )

    def test_id_is_backend_id(
        self, check: VASTBackendStatusCheck, backend_id: StorageBackendID
    ) -> None:
        assert check.id() == backend_id

    def test_latest_is_none_before_any_check(self, check: VASTBackendStatusCheck) -> None:
        assert check.latest() is None

    def test_records_what_the_client_observed(
        self,
        responding_client: MagicMock,
        check: VASTBackendStatusCheck,
        observed: VASTCluster,
    ) -> None:
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is None
        assert result.duration is not None
        assert result.cluster_name == observed.cluster_name
        assert result.state == observed.state
        assert result.guid == observed.guid

    def test_records_error_when_the_client_raises(
        self,
        failing_client: MagicMock,
        check: VASTBackendStatusCheck,
    ) -> None:
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg == "connection refused"
        assert result.duration is not None
        assert result.cluster_name is None
        assert result.state is None
        assert result.guid is None

    def test_failure_replaces_an_earlier_observation(
        self,
        client_failing_after_success: MagicMock,
        check: VASTBackendStatusCheck,
    ) -> None:
        check.check_status()
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg == "connection refused"
        assert result.cluster_name is None
        assert result.state is None
        assert result.guid is None
