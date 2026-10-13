from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.storage.backend.purestorage.check import (
    PureStorageBackendStatusCheck,
    PureStorageBackendStatusCheckArgs,
)
from ai.backend.common.storage.client.purestorage.client import PureStorageClient
from ai.backend.common.storage.client.purestorage.types import PureStorageArray


class TestPureStorageBackendStatusCheck:
    @pytest.fixture
    def backend_id(self) -> StorageBackendID:
        return StorageBackendID(uuid.uuid4())

    @pytest.fixture
    def observed(self) -> PureStorageArray:
        return PureStorageArray(
            array_id="arr-1",
            array_name="fb01",
            os="Purity//FB",
            version="4.1.0",
        )

    @pytest.fixture
    def client(self) -> MagicMock:
        return MagicMock(spec=PureStorageClient)

    @pytest.fixture
    def responding_client(self, client: MagicMock, observed: PureStorageArray) -> MagicMock:
        client.get_array.return_value = observed
        return client

    @pytest.fixture
    def failing_client(self, client: MagicMock) -> MagicMock:
        client.get_array.side_effect = RuntimeError("connection refused")
        return client

    @pytest.fixture
    def client_failing_after_success(
        self, client: MagicMock, observed: PureStorageArray
    ) -> MagicMock:
        client.get_array.side_effect = [observed, RuntimeError("connection refused")]
        return client

    @pytest.fixture
    def check(
        self, backend_id: StorageBackendID, client: MagicMock
    ) -> PureStorageBackendStatusCheck:
        return PureStorageBackendStatusCheck(
            PureStorageBackendStatusCheckArgs(backend_id=backend_id, client=client)
        )

    def test_id_is_backend_id(
        self, check: PureStorageBackendStatusCheck, backend_id: StorageBackendID
    ) -> None:
        assert check.id() == backend_id

    def test_latest_is_none_before_any_check(self, check: PureStorageBackendStatusCheck) -> None:
        assert check.latest() is None

    def test_records_what_the_client_observed(
        self,
        responding_client: MagicMock,
        check: PureStorageBackendStatusCheck,
        observed: PureStorageArray,
    ) -> None:
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is None
        assert result.duration is not None
        assert result.array_id == observed.array_id
        assert result.array_name == observed.array_name
        assert result.os == observed.os
        assert result.version == observed.version

    def test_records_error_when_the_client_raises(
        self,
        failing_client: MagicMock,
        check: PureStorageBackendStatusCheck,
    ) -> None:
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg == "connection refused"
        assert result.duration is not None
        assert result.array_id is None
        assert result.array_name is None
        assert result.os is None
        assert result.version is None

    def test_failure_replaces_an_earlier_observation(
        self,
        client_failing_after_success: MagicMock,
        check: PureStorageBackendStatusCheck,
    ) -> None:
        check.check_status()
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg == "connection refused"
        assert result.array_id is None
        assert result.array_name is None
        assert result.os is None
        assert result.version is None
