from __future__ import annotations

import subprocess
import uuid
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.storage.backend.exascaler.check import (
    EXAScalerBackendStatusCheck,
    EXAScalerBackendStatusCheckArgs,
)
from ai.backend.common.storage.client.exascaler.client import EXAScalerClient
from ai.backend.common.storage.client.exascaler.types import LustreServerConnection


class TestEXAScalerBackendStatusCheck:
    @pytest.fixture
    def backend_id(self) -> StorageBackendID:
        return StorageBackendID(uuid.uuid4())

    @pytest.fixture
    def observed_servers(self) -> tuple[LustreServerConnection, ...]:
        return (
            LustreServerConnection(name="lufs01-MDT0000-mdc-ffff8800", state="active"),
            LustreServerConnection(name="lufs01-OST0000-osc-ffff8800", state="active"),
        )

    @pytest.fixture
    def client(self) -> MagicMock:
        return MagicMock(spec=EXAScalerClient)

    @pytest.fixture
    def responding_client(
        self, client: MagicMock, observed_servers: tuple[LustreServerConnection, ...]
    ) -> MagicMock:
        client.get_lfs_version.return_value = "2.15.4"
        client.check_servers.return_value = observed_servers
        return client

    @pytest.fixture
    def failing_client(self, client: MagicMock) -> MagicMock:
        client.get_lfs_version.side_effect = RuntimeError("lfs not found")
        return client

    @pytest.fixture
    def client_with_failing_command(self, client: MagicMock) -> MagicMock:
        client.get_lfs_version.return_value = "2.15.4"
        client.check_servers.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["sudo", "-n", "lfs", "check", "servers"],
            stderr="error: check 'lufs01-OST0001': Resource temporarily unavailable (11)\n",
        )
        return client

    @pytest.fixture
    def client_failing_after_success(
        self, client: MagicMock, observed_servers: tuple[LustreServerConnection, ...]
    ) -> MagicMock:
        client.get_lfs_version.return_value = "2.15.4"
        client.check_servers.side_effect = [observed_servers, RuntimeError("timed out")]
        return client

    @pytest.fixture
    def check(self, backend_id: StorageBackendID, client: MagicMock) -> EXAScalerBackendStatusCheck:
        return EXAScalerBackendStatusCheck(
            EXAScalerBackendStatusCheckArgs(backend_id=backend_id, client=client)
        )

    def test_id_is_backend_id(
        self, check: EXAScalerBackendStatusCheck, backend_id: StorageBackendID
    ) -> None:
        assert check.id() == backend_id

    def test_latest_is_none_before_any_check(self, check: EXAScalerBackendStatusCheck) -> None:
        assert check.latest() is None

    def test_records_what_the_client_observed(
        self,
        responding_client: MagicMock,
        check: EXAScalerBackendStatusCheck,
        observed_servers: tuple[LustreServerConnection, ...],
    ) -> None:
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is None
        assert result.duration is not None
        assert result.lfs_version == "2.15.4"
        assert result.servers == observed_servers

    def test_records_error_when_the_client_raises(
        self,
        failing_client: MagicMock,
        check: EXAScalerBackendStatusCheck,
    ) -> None:
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg == "lfs not found"
        assert result.duration is not None
        assert result.lfs_version is None
        assert result.servers is None

    def test_records_stderr_when_the_command_fails(
        self,
        client_with_failing_command: MagicMock,
        check: EXAScalerBackendStatusCheck,
    ) -> None:
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg is not None
        assert "Resource temporarily unavailable" in result.error_msg
        assert result.lfs_version == "2.15.4"
        assert result.servers is None

    def test_failure_replaces_an_earlier_observation(
        self,
        client_failing_after_success: MagicMock,
        check: EXAScalerBackendStatusCheck,
    ) -> None:
        check.check_status()
        check.check_status()

        result = check.latest()
        assert result is not None
        assert result.error_msg == "timed out"
        assert result.servers is None
