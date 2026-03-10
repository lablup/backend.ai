"""Unit tests for DockerKernelCreationContext.prepare_ssh() platform guard."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from ai.backend.agent.docker.agent import DockerKernelCreationContext
from ai.backend.common.types import ClusterInfo, ClusterMode, ClusterSSHKeyPair

_AGENT_MODULE = "ai.backend.agent.docker.agent"


def _make_cluster_info(
    *,
    ssh_keypair: ClusterSSHKeyPair | None = None,
) -> ClusterInfo:
    return ClusterInfo(
        mode=ClusterMode.SINGLE_NODE,
        size=1,
        replicas={},
        network_config={},
        ssh_keypair=ssh_keypair,
        cluster_ssh_port_mapping=None,
    )


def _make_mock_ctx(tmp_path: Path) -> MagicMock:
    """Create a MagicMock mimicking DockerKernelCreationContext for prepare_ssh."""
    ctx = MagicMock()
    ctx.config_dir = tmp_path / "config"
    ctx.config_dir.mkdir(parents=True, exist_ok=True)
    ctx.kernel_features = frozenset()
    ctx.get_overriding_uid.return_value = None
    ctx.get_overriding_gid.return_value = None
    ctx.resolve_krunner_filepath.return_value = tmp_path / "dropbearmulti.aarch64.bin"
    return ctx


class TestPrepareSSHPlatformGuard:
    """Tests for the sys.platform guard in prepare_ssh / _write_config."""

    async def test_skips_dropbearmulti_on_non_linux(self, tmp_path: Path) -> None:
        """On non-Linux platforms, _write_config must skip dropbearmulti and log a warning."""
        ctx = _make_mock_ctx(tmp_path)
        cluster_info = _make_cluster_info()

        with (
            patch(f"{_AGENT_MODULE}.sys") as mock_sys,
            patch(f"{_AGENT_MODULE}.subprocess_run") as mock_subprocess_run,
            patch(f"{_AGENT_MODULE}.current_loop") as mock_current_loop,
            patch(f"{_AGENT_MODULE}.log") as mock_log,
        ):
            mock_sys.platform = "darwin"

            # Make run_in_executor call the function directly (synchronously).
            loop_mock = MagicMock()
            loop_mock.run_in_executor = AsyncMock(
                side_effect=lambda _, fn: fn(),
            )
            mock_current_loop.return_value = loop_mock

            # Call the real prepare_ssh with our mocked self
            await DockerKernelCreationContext.prepare_ssh(ctx, cluster_info)

            # dropbearmulti must NOT be executed
            mock_subprocess_run.assert_not_called()

            # A warning must be logged about skipping
            mock_log.warning.assert_called_once()
            warning_args = mock_log.warning.call_args
            assert "Skipping dropbearmulti" in warning_args[0][0]
            assert "darwin" in warning_args[0]

        # The ssh directory should still be created
        ssh_dir = tmp_path / "config" / "ssh"
        assert ssh_dir.is_dir()

        # No host key file should exist
        assert not (ssh_dir / "dropbear_rsa_host_key").exists()

    async def test_runs_dropbearmulti_on_linux(self, tmp_path: Path) -> None:
        """On Linux, _write_config must execute dropbearmulti to generate the host key."""
        ctx = _make_mock_ctx(tmp_path)
        cluster_info = _make_cluster_info()

        # Create a fake dropbearmulti binary so the exists() check passes.
        fake_bin = tmp_path / "dropbearmulti.aarch64.bin"
        fake_bin.touch()

        ctx.resolve_krunner_filepath.return_value = fake_bin

        with (
            patch(f"{_AGENT_MODULE}.sys") as mock_sys,
            patch(f"{_AGENT_MODULE}.subprocess_run") as mock_subprocess_run,
            patch(f"{_AGENT_MODULE}.get_arch_name", return_value="aarch64"),
            patch(f"{_AGENT_MODULE}.current_loop") as mock_current_loop,
            patch(f"{_AGENT_MODULE}.log"),
        ):
            mock_sys.platform = "linux"

            loop_mock = MagicMock()
            loop_mock.run_in_executor = AsyncMock(
                side_effect=lambda _, fn: fn(),
            )
            mock_current_loop.return_value = loop_mock

            await DockerKernelCreationContext.prepare_ssh(ctx, cluster_info)

            # dropbearmulti MUST be called
            mock_subprocess_run.assert_called_once()
            call_args = mock_subprocess_run.call_args
            assert str(fake_bin) in call_args[0][0]
            assert "dropbearkey" in call_args[0][0]

    async def test_cluster_keypair_written_regardless_of_platform(self, tmp_path: Path) -> None:
        """Cluster SSH keypair must be written on any platform (not gated by sys.platform)."""
        ctx = _make_mock_ctx(tmp_path)
        keypair = ClusterSSHKeyPair(
            public_key="ssh-rsa AAAA_TEST_PUB_KEY",
            private_key="-----BEGIN RSA-----\nTEST_PRIV_KEY",
        )
        cluster_info = _make_cluster_info(ssh_keypair=keypair)

        with (
            patch(f"{_AGENT_MODULE}.sys") as mock_sys,
            patch(f"{_AGENT_MODULE}.subprocess_run"),
            patch(f"{_AGENT_MODULE}.current_loop") as mock_current_loop,
            patch(f"{_AGENT_MODULE}.log"),
        ):
            mock_sys.platform = "darwin"

            loop_mock = MagicMock()
            loop_mock.run_in_executor = AsyncMock(
                side_effect=lambda _, fn: fn(),
            )
            mock_current_loop.return_value = loop_mock

            await DockerKernelCreationContext.prepare_ssh(ctx, cluster_info)

        ssh_dir = tmp_path / "config" / "ssh"
        priv_key = ssh_dir / "id_cluster"
        pub_key = ssh_dir / "id_cluster.pub"
        assert priv_key.read_text() == keypair["private_key"]
        assert pub_key.read_text() == keypair["public_key"]
