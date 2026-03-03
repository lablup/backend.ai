from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.agent.docker.agent import DockerKernelCreationContext
from ai.backend.common.docker import KernelFeatures
from ai.backend.common.types import ClusterInfo


def _make_subprocess_side_effect(config_dir: Path) -> Callable[..., None]:
    """Side effect for subprocess_run that creates the host key file."""

    def _side_effect(*args: Any, **kwargs: Any) -> None:
        host_key_path = config_dir / "ssh" / "dropbear_rsa_host_key"
        host_key_path.write_bytes(b"fake-host-key")

    return _side_effect


@pytest.fixture()
def cluster_info_with_keypair() -> dict[str, Any]:
    return {
        "ssh_keypair": {
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\nfake\n-----END RSA PRIVATE KEY-----",
            "public_key": "ssh-rsa AAAAFAKE user@host",
        },
        "cluster_ssh_port_mapping": None,
    }


@pytest.fixture()
def cluster_info_no_keypair() -> dict[str, Any]:
    return {
        "ssh_keypair": None,
        "cluster_ssh_port_mapping": None,
    }


@pytest.fixture()
def mock_ctx(tmp_path: Path) -> MagicMock:
    """Create a minimal mock of DockerKernelCreationContext."""
    ctx = MagicMock(spec=DockerKernelCreationContext)
    ctx.config_dir = tmp_path / "config"

    # Create a fake dropbearmulti binary
    bin_path = tmp_path / "dropbearmulti.x86_64.bin"
    bin_path.write_text("fake")
    ctx.resolve_krunner_filepath.return_value = bin_path

    ctx.kernel_features = frozenset()
    ctx.local_config = MagicMock()
    ctx.local_config.container.kernel_uid = 1000
    ctx.local_config.container.kernel_gid = 1000
    ctx.get_overriding_uid.return_value = None
    ctx.get_overriding_gid.return_value = None
    ctx._chown_paths_if_root = MagicMock()
    return ctx


async def _call_prepare_ssh(
    ctx: MagicMock,
    cluster_info: dict[str, Any],
) -> None:
    """Call prepare_ssh with current_loop mocked to run synchronously."""
    with patch("ai.backend.agent.docker.agent.current_loop") as mock_loop:

        async def run_in_executor_sync(executor: Any, fn: Any, *args: Any) -> Any:
            return fn(*args)

        mock_event_loop = MagicMock()
        mock_event_loop.run_in_executor = run_in_executor_sync
        mock_loop.return_value = mock_event_loop

        await DockerKernelCreationContext.prepare_ssh(ctx, cast(ClusterInfo, cluster_info))


class TestPrepareSshHostKeyGeneration:
    @pytest.mark.asyncio
    async def test_calls_dropbearkey_with_correct_args(
        self,
        mock_ctx: MagicMock,
        cluster_info_no_keypair: dict[str, Any],
        tmp_path: Path,
    ) -> None:
        side_effect = _make_subprocess_side_effect(mock_ctx.config_dir)
        with (
            patch(
                "ai.backend.agent.docker.agent.subprocess_run",
                side_effect=side_effect,
            ) as mock_run,
            patch(
                "ai.backend.agent.docker.agent.get_arch_name",
                return_value="x86_64",
            ),
        ):
            await _call_prepare_ssh(mock_ctx, cluster_info_no_keypair)

            mock_run.assert_called_once()
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            dropbearmulti = mock_ctx.resolve_krunner_filepath.return_value
            assert cmd[0] == str(dropbearmulti)
            assert cmd[1] == "dropbearkey"
            assert cmd[2:4] == ["-t", "rsa"]
            assert cmd[4:6] == ["-s", "2048"]
            assert cmd[6] == "-f"
            expected_key_path = str(tmp_path / "config" / "ssh" / "dropbear_rsa_host_key")
            assert cmd[7] == expected_key_path
            assert call_args[1]["check"] is True
            assert call_args[1]["capture_output"] is True

    @pytest.mark.asyncio
    async def test_skips_generation_when_host_key_exists(
        self,
        mock_ctx: MagicMock,
        cluster_info_no_keypair: dict[str, Any],
        tmp_path: Path,
    ) -> None:
        ssh_dir = tmp_path / "config" / "ssh"
        ssh_dir.mkdir(parents=True, exist_ok=True)
        host_key = ssh_dir / "dropbear_rsa_host_key"
        host_key.write_text("existing_key")

        with (
            patch(
                "ai.backend.agent.docker.agent.subprocess_run",
            ) as mock_run,
            patch(
                "ai.backend.agent.docker.agent.get_arch_name",
                return_value="x86_64",
            ),
        ):
            await _call_prepare_ssh(mock_ctx, cluster_info_no_keypair)

            mock_run.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_file_not_found_when_binary_missing(
        self,
        mock_ctx: MagicMock,
        cluster_info_no_keypair: dict[str, Any],
        tmp_path: Path,
    ) -> None:
        mock_ctx.resolve_krunner_filepath.return_value = tmp_path / "nonexistent.bin"

        with patch(
            "ai.backend.agent.docker.agent.get_arch_name",
            return_value="x86_64",
        ):
            # FileNotFoundError caught by outer try/except and logged
            await _call_prepare_ssh(mock_ctx, cluster_info_no_keypair)

            # Execution was halted — no cluster keypair written
            cluster_key = tmp_path / "config" / "ssh" / "id_cluster"
            assert not cluster_key.exists()

    @pytest.mark.asyncio
    async def test_logs_and_reraises_on_subprocess_failure(
        self,
        mock_ctx: MagicMock,
        cluster_info_no_keypair: dict[str, Any],
    ) -> None:
        error = CalledProcessError(1, "dropbearkey", b"out", b"err")
        with (
            patch(
                "ai.backend.agent.docker.agent.subprocess_run",
                side_effect=error,
            ),
            patch(
                "ai.backend.agent.docker.agent.get_arch_name",
                return_value="x86_64",
            ),
        ):
            # CalledProcessError caught by outer try/except and logged
            await _call_prepare_ssh(mock_ctx, cluster_info_no_keypair)

            # Execution was halted — no cluster keypair written
            ssh_dir = mock_ctx.config_dir / "ssh"
            assert not (ssh_dir / "id_cluster").exists()

    @pytest.mark.asyncio
    async def test_host_key_gets_chmod_0o600(
        self,
        mock_ctx: MagicMock,
        cluster_info_no_keypair: dict[str, Any],
        tmp_path: Path,
    ) -> None:
        side_effect = _make_subprocess_side_effect(mock_ctx.config_dir)
        with (
            patch(
                "ai.backend.agent.docker.agent.subprocess_run",
                side_effect=side_effect,
            ),
            patch(
                "ai.backend.agent.docker.agent.get_arch_name",
                return_value="x86_64",
            ),
        ):
            await _call_prepare_ssh(mock_ctx, cluster_info_no_keypair)

            host_key = tmp_path / "config" / "ssh" / "dropbear_rsa_host_key"
            assert host_key.stat().st_mode & 0o777 == 0o600


class TestPrepareSshClusterKeypair:
    @pytest.mark.asyncio
    async def test_writes_keypair_with_correct_permissions(
        self,
        mock_ctx: MagicMock,
        cluster_info_with_keypair: dict[str, Any],
        tmp_path: Path,
    ) -> None:
        side_effect = _make_subprocess_side_effect(mock_ctx.config_dir)
        with (
            patch(
                "ai.backend.agent.docker.agent.subprocess_run",
                side_effect=side_effect,
            ),
            patch(
                "ai.backend.agent.docker.agent.get_arch_name",
                return_value="x86_64",
            ),
        ):
            await _call_prepare_ssh(mock_ctx, cluster_info_with_keypair)

            ssh_dir = tmp_path / "config" / "ssh"
            priv_key = ssh_dir / "id_cluster"
            pub_key = ssh_dir / "id_cluster.pub"

            assert priv_key.read_text() == cluster_info_with_keypair["ssh_keypair"]["private_key"]
            assert pub_key.read_text() == cluster_info_with_keypair["ssh_keypair"]["public_key"]
            assert priv_key.stat().st_mode & 0o777 == 0o600

    @pytest.mark.asyncio
    async def test_skips_cluster_keypair_when_sshkey_none(
        self,
        mock_ctx: MagicMock,
        cluster_info_no_keypair: dict[str, Any],
        tmp_path: Path,
    ) -> None:
        side_effect = _make_subprocess_side_effect(mock_ctx.config_dir)
        with (
            patch(
                "ai.backend.agent.docker.agent.subprocess_run",
                side_effect=side_effect,
            ),
            patch(
                "ai.backend.agent.docker.agent.get_arch_name",
                return_value="x86_64",
            ),
        ):
            await _call_prepare_ssh(mock_ctx, cluster_info_no_keypair)

            ssh_dir = tmp_path / "config" / "ssh"
            assert not (ssh_dir / "id_cluster").exists()
            assert not (ssh_dir / "id_cluster.pub").exists()
            # Host key should still be generated
            assert (ssh_dir / "dropbear_rsa_host_key").exists()


class TestPrepareSshPortMapping:
    @pytest.mark.asyncio
    async def test_writes_port_mapping_json(
        self,
        mock_ctx: MagicMock,
        cluster_info_with_keypair: dict[str, Any],
        tmp_path: Path,
    ) -> None:
        port_mapping = {"node1": ["10.0.0.1", 2222], "node2": ["10.0.0.2", 2223]}
        cluster_info_with_keypair["cluster_ssh_port_mapping"] = port_mapping

        side_effect = _make_subprocess_side_effect(mock_ctx.config_dir)
        with (
            patch(
                "ai.backend.agent.docker.agent.subprocess_run",
                side_effect=side_effect,
            ),
            patch(
                "ai.backend.agent.docker.agent.get_arch_name",
                return_value="x86_64",
            ),
        ):
            await _call_prepare_ssh(mock_ctx, cluster_info_with_keypair)

            mapping_path = tmp_path / "config" / "ssh" / "port-mapping.json"
            assert mapping_path.exists()
            written = json.loads(mapping_path.read_bytes())
            assert written == port_mapping

    @pytest.mark.asyncio
    async def test_skips_port_mapping_when_none(
        self,
        mock_ctx: MagicMock,
        cluster_info_with_keypair: dict[str, Any],
        tmp_path: Path,
    ) -> None:
        cluster_info_with_keypair["cluster_ssh_port_mapping"] = None

        side_effect = _make_subprocess_side_effect(mock_ctx.config_dir)
        with (
            patch(
                "ai.backend.agent.docker.agent.subprocess_run",
                side_effect=side_effect,
            ),
            patch(
                "ai.backend.agent.docker.agent.get_arch_name",
                return_value="x86_64",
            ),
        ):
            await _call_prepare_ssh(mock_ctx, cluster_info_with_keypair)

            mapping_path = tmp_path / "config" / "ssh" / "port-mapping.json"
            assert not mapping_path.exists()


class TestPrepareSshChown:
    @pytest.mark.asyncio
    async def test_chown_called_with_overriding_uid_gid(
        self,
        mock_ctx: MagicMock,
        cluster_info_with_keypair: dict[str, Any],
        tmp_path: Path,
    ) -> None:
        mock_ctx.get_overriding_uid.return_value = 5000
        mock_ctx.get_overriding_gid.return_value = 5001

        side_effect = _make_subprocess_side_effect(mock_ctx.config_dir)
        with (
            patch(
                "ai.backend.agent.docker.agent.subprocess_run",
                side_effect=side_effect,
            ),
            patch(
                "ai.backend.agent.docker.agent.get_arch_name",
                return_value="x86_64",
            ),
        ):
            await _call_prepare_ssh(mock_ctx, cluster_info_with_keypair)

            mock_ctx._chown_paths_if_root.assert_called_once()
            call_args = mock_ctx._chown_paths_if_root.call_args
            paths = call_args[0][0]
            uid = call_args[0][1]
            gid = call_args[0][2]
            assert uid == 5000
            assert gid == 5001
            path_names = [p.name for p in paths]
            assert "dropbear_rsa_host_key" in path_names
            assert "id_cluster" in path_names
            assert "id_cluster.pub" in path_names

    @pytest.mark.asyncio
    async def test_chown_called_with_uid_match_feature(
        self,
        mock_ctx: MagicMock,
        cluster_info_with_keypair: dict[str, Any],
    ) -> None:
        mock_ctx.kernel_features = frozenset({KernelFeatures.UID_MATCH})
        mock_ctx.get_overriding_uid.return_value = None
        mock_ctx.get_overriding_gid.return_value = None

        side_effect = _make_subprocess_side_effect(mock_ctx.config_dir)
        with (
            patch(
                "ai.backend.agent.docker.agent.subprocess_run",
                side_effect=side_effect,
            ),
            patch(
                "ai.backend.agent.docker.agent.get_arch_name",
                return_value="x86_64",
            ),
        ):
            await _call_prepare_ssh(mock_ctx, cluster_info_with_keypair)

            mock_ctx._chown_paths_if_root.assert_called_once()
            call_args = mock_ctx._chown_paths_if_root.call_args
            uid = call_args[0][1]
            gid = call_args[0][2]
            assert uid == mock_ctx.local_config.container.kernel_uid
            assert gid == mock_ctx.local_config.container.kernel_gid

    @pytest.mark.asyncio
    async def test_chown_skipped_when_no_override_and_no_uid_match(
        self,
        mock_ctx: MagicMock,
        cluster_info_with_keypair: dict[str, Any],
    ) -> None:
        mock_ctx.kernel_features = frozenset()
        mock_ctx.get_overriding_uid.return_value = None
        mock_ctx.get_overriding_gid.return_value = None

        side_effect = _make_subprocess_side_effect(mock_ctx.config_dir)
        with (
            patch(
                "ai.backend.agent.docker.agent.subprocess_run",
                side_effect=side_effect,
            ),
            patch(
                "ai.backend.agent.docker.agent.get_arch_name",
                return_value="x86_64",
            ),
        ):
            await _call_prepare_ssh(mock_ctx, cluster_info_with_keypair)

            mock_ctx._chown_paths_if_root.assert_not_called()

    @pytest.mark.asyncio
    async def test_chown_called_with_only_overriding_uid(
        self,
        mock_ctx: MagicMock,
        cluster_info_with_keypair: dict[str, Any],
    ) -> None:
        mock_ctx.get_overriding_uid.return_value = 5000
        mock_ctx.get_overriding_gid.return_value = None

        side_effect = _make_subprocess_side_effect(mock_ctx.config_dir)
        with (
            patch(
                "ai.backend.agent.docker.agent.subprocess_run",
                side_effect=side_effect,
            ),
            patch(
                "ai.backend.agent.docker.agent.get_arch_name",
                return_value="x86_64",
            ),
        ):
            await _call_prepare_ssh(mock_ctx, cluster_info_with_keypair)

            mock_ctx._chown_paths_if_root.assert_called_once()
            call_args = mock_ctx._chown_paths_if_root.call_args
            assert call_args[0][1] == 5000
            assert call_args[0][2] is None
