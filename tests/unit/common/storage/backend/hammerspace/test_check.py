from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.storage.backend.hammerspace.check import (
    HammerspaceBackendStatusCheck,
    HammerspaceBackendStatusCheckArgs,
)
from ai.backend.common.storage.client.hammerspace.client import HammerspaceClient
from ai.backend.common.storage.client.hammerspace.types import HammerspaceSite


class TestHammerspaceBackendStatusCheck:
    @pytest.fixture
    def backend_id(self) -> StorageBackendID:
        return StorageBackendID(uuid.uuid4())

    @pytest.fixture
    def observed(self) -> tuple[HammerspaceSite, ...]:
        return (
            HammerspaceSite(name="site-a", type="LOCAL"),
            HammerspaceSite(name="site-b", type="REMOTE"),
        )

    @pytest.fixture
    def client(self) -> MagicMock:
        return MagicMock(spec=HammerspaceClient)

    @pytest.fixture
    def responding_client(
        self, client: MagicMock, observed: tuple[HammerspaceSite, ...]
    ) -> MagicMock:
        client.list_sites.return_value = observed
        return client

    @pytest.fixture
    def failing_client(self, client: MagicMock) -> MagicMock:
        client.list_sites.side_effect = RuntimeError("connection refused")
        return client

    @pytest.fixture
    def client_failing_after_success(
        self, client: MagicMock, observed: tuple[HammerspaceSite, ...]
    ) -> MagicMock:
        client.list_sites.side_effect = [observed, RuntimeError("connection refused")]
        return client

    @pytest.fixture
    def check(
        self, backend_id: StorageBackendID, client: MagicMock
    ) -> HammerspaceBackendStatusCheck:
        return HammerspaceBackendStatusCheck(
            HammerspaceBackendStatusCheckArgs(backend_id=backend_id, client=client)
        )

    def test_id_is_backend_id(
        self, check: HammerspaceBackendStatusCheck, backend_id: StorageBackendID
    ) -> None:
        assert check.id() == backend_id

    def test_latest_is_none_before_any_check(self, check: HammerspaceBackendStatusCheck) -> None:
        assert check.latest() is None

    def test_records_what_the_client_observed(
        self,
        responding_client: MagicMock,
        check: HammerspaceBackendStatusCheck,
        observed: tuple[HammerspaceSite, ...],
    ) -> None:
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is None
        assert result.duration is not None
        assert result.sites == observed

    def test_records_error_when_the_client_raises(
        self,
        failing_client: MagicMock,
        check: HammerspaceBackendStatusCheck,
    ) -> None:
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg == "connection refused"
        assert result.duration is not None
        assert result.sites is None

    def test_failure_replaces_an_earlier_observation(
        self,
        client_failing_after_success: MagicMock,
        check: HammerspaceBackendStatusCheck,
    ) -> None:
        check.check_status()
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg == "connection refused"
        assert result.sites is None
