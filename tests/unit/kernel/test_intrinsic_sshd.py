from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from ai.backend.kernel.intrinsic import (
    AGENT_HOST_KEY_PATH,
    LEGACY_HOST_KEY_PATH,
    init_sshd_service,
    prepare_sshd_service,
)

DROPBEAR_KEYGEN_STDOUT = b"Will output 2048 bit rsa secret key\nssh-rsa AAAA... user@host\n"


def _make_proc(returncode: int = 0, stdout: bytes = b"", stderr: bytes = b"") -> AsyncMock:
    """Create a mock subprocess.Process with preset communicate() results."""
    proc = AsyncMock()
    proc.returncode = returncode
    proc.communicate = AsyncMock(return_value=(stdout, stderr))
    return proc


class TestPrepareSshdService:
    """Tests for prepare_sshd_service() host-key selection and port binding."""

    @pytest.fixture
    def service_info_single_port(self) -> dict[str, Any]:
        return {"port": 2200}

    @pytest.fixture
    def service_info_multi_port(self) -> dict[str, Any]:
        return {"port": [2200, 2201, 2202]}

    @pytest.fixture
    def mock_agent_key_present(self) -> Generator[None, None, None]:
        with patch.object(Path, "is_file", return_value=True):
            yield

    @pytest.fixture
    def mock_agent_key_absent(self) -> Generator[None, None, None]:
        with patch.object(Path, "is_file", return_value=False):
            yield

    async def test_uses_agent_host_key_when_present(
        self,
        service_info_multi_port: dict[str, Any],
        mock_agent_key_present: None,
    ) -> None:
        cmdargs, _env = await prepare_sshd_service(service_info_multi_port)

        assert str(AGENT_HOST_KEY_PATH) in cmdargs
        assert str(LEGACY_HOST_KEY_PATH) not in cmdargs

    async def test_uses_legacy_host_key_when_agent_absent(
        self,
        service_info_multi_port: dict[str, Any],
        mock_agent_key_absent: None,
    ) -> None:
        cmdargs, _env = await prepare_sshd_service(service_info_multi_port)

        assert str(LEGACY_HOST_KEY_PATH) in cmdargs
        assert str(AGENT_HOST_KEY_PATH) not in cmdargs

    async def test_returns_empty_env(
        self,
        service_info_multi_port: dict[str, Any],
        mock_agent_key_present: None,
    ) -> None:
        _cmdargs, env = await prepare_sshd_service(service_info_multi_port)

        assert env == {}

    async def test_single_port(
        self,
        service_info_single_port: dict[str, Any],
        mock_agent_key_present: None,
    ) -> None:
        cmdargs, _env = await prepare_sshd_service(service_info_single_port)

        port_flags = [cmdargs[i + 1] for i, v in enumerate(cmdargs) if v == "-p"]
        assert port_flags == ["0.0.0.0:2200"]

    async def test_multiple_ports(
        self,
        service_info_multi_port: dict[str, Any],
        mock_agent_key_present: None,
    ) -> None:
        cmdargs, _env = await prepare_sshd_service(service_info_multi_port)

        port_flags = [cmdargs[i + 1] for i, v in enumerate(cmdargs) if v == "-p"]
        assert port_flags == ["0.0.0.0:2200", "0.0.0.0:2201", "0.0.0.0:2202"]


class TestInitSshdServiceHostKey:
    """Tests for init_sshd_service() host-key generation logic."""

    @pytest.fixture
    def child_env(self) -> dict[str, str]:
        return {}

    @pytest.fixture
    def cluster_replicas(self) -> dict[str, int]:
        return {"main": 1}

    @pytest.fixture
    def user_keygen_proc(self) -> AsyncMock:
        return _make_proc(returncode=0, stdout=DROPBEAR_KEYGEN_STDOUT)

    @pytest.fixture
    def user_convert_proc(self) -> AsyncMock:
        return _make_proc(returncode=0)

    @pytest.fixture
    def host_keygen_proc(self) -> AsyncMock:
        return _make_proc(returncode=0)

    @pytest.fixture
    def mock_fs_ops(self) -> Generator[None, None, None]:
        """Patch all filesystem operations used by init_sshd_service."""
        with (
            patch.object(Path, "is_dir", return_value=False),
            patch.object(Path, "mkdir"),
            patch.object(Path, "chmod"),
            patch.object(Path, "write_bytes"),
            patch("shutil.rmtree"),
        ):
            yield

    @pytest.fixture
    def mock_init_agent_key_present(
        self,
        mock_fs_ops: None,
        user_keygen_proc: AsyncMock,
        user_convert_proc: AsyncMock,
    ) -> Generator[AsyncMock, None, None]:
        """Agent host key EXISTS — only user keygen + convert, no host keygen."""
        mock_create = AsyncMock(side_effect=[user_keygen_proc, user_convert_proc])
        with (
            patch.object(
                Path,
                "is_file",
                autospec=True,
                side_effect=lambda self: self == AGENT_HOST_KEY_PATH,
            ),
            patch("asyncio.create_subprocess_exec", mock_create),
        ):
            yield mock_create

    @pytest.fixture
    def mock_init_agent_key_absent(
        self,
        mock_fs_ops: None,
        user_keygen_proc: AsyncMock,
        user_convert_proc: AsyncMock,
        host_keygen_proc: AsyncMock,
    ) -> Generator[AsyncMock, None, None]:
        """Agent host key ABSENT — user keygen + convert + host keygen."""
        mock_create = AsyncMock(side_effect=[user_keygen_proc, user_convert_proc, host_keygen_proc])
        with (
            patch.object(
                Path,
                "is_file",
                autospec=True,
                side_effect=lambda self: False,
            ),
            patch("asyncio.create_subprocess_exec", mock_create),
        ):
            yield mock_create

    async def test_skips_keygen_when_agent_host_key_exists(
        self,
        child_env: dict[str, str],
        cluster_replicas: dict[str, int],
        mock_init_agent_key_present: AsyncMock,
    ) -> None:
        await init_sshd_service(child_env, cluster_replicas)

        assert not any(
            str(LEGACY_HOST_KEY_PATH) in map(str, call[0])
            for call in mock_init_agent_key_present.call_args_list
        )

    async def test_generates_key_when_agent_host_key_absent(
        self,
        child_env: dict[str, str],
        cluster_replicas: dict[str, int],
        mock_init_agent_key_absent: AsyncMock,
    ) -> None:
        await init_sshd_service(child_env, cluster_replicas)

        assert any(
            str(LEGACY_HOST_KEY_PATH) in map(str, call[0])
            for call in mock_init_agent_key_absent.call_args_list
        )


@dataclass(frozen=True)
class _ClusterSshConfigCase:
    cluster_replicas: dict[str, int]
    expected_host_lines: list[str]


class TestInitSshdServiceClusterSshConfig:
    """Tests for the per-role ssh config entries init_sshd_service() writes without a port mapping."""

    @pytest.fixture
    def ssh_config_file_without_port_mapping(self) -> Generator[MagicMock, None, None]:
        """The cluster private key exists, the port mapping and the user's ssh config do not."""
        existing_paths = {
            Path("/home/work/.ssh/authorized_keys"),
            AGENT_HOST_KEY_PATH,
            Path("/home/config/ssh/id_cluster"),
        }
        ssh_config_file = mock_open()
        with (
            patch.object(Path, "is_dir", return_value=False),
            patch.object(Path, "mkdir"),
            patch.object(Path, "stat", side_effect=FileNotFoundError),
            patch.object(
                Path,
                "is_file",
                autospec=True,
                side_effect=lambda self: self in existing_paths,
            ),
            patch.object(Path, "read_text", side_effect=FileNotFoundError),
            patch.object(Path, "open", ssh_config_file),
            patch("shutil.rmtree"),
        ):
            yield ssh_config_file

    @pytest.mark.parametrize(
        "case",
        [
            _ClusterSshConfigCase(
                cluster_replicas={"main": 1},
                expected_host_lines=["Host main*"],
            ),
            _ClusterSshConfigCase(
                cluster_replicas={"main": 1, "sub": 2},
                expected_host_lines=["Host main*", "Host sub*"],
            ),
        ],
        ids=lambda case: ",".join(case.cluster_replicas),
    )
    async def test_writes_a_host_entry_per_cluster_role(
        self,
        case: _ClusterSshConfigCase,
        ssh_config_file_without_port_mapping: MagicMock,
    ) -> None:
        await init_sshd_service({}, case.cluster_replicas)

        written = "".join(
            call.args[0] for call in ssh_config_file_without_port_mapping().write.call_args_list
        )
        host_lines = [line for line in written.splitlines() if line.startswith("Host ")]
        assert host_lines == case.expected_host_lines
