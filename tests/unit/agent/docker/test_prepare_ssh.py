from __future__ import annotations

import json
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.docker.agent import DockerKernelCreationContext
from ai.backend.common.docker import KernelFeatures
from ai.backend.common.types import (
    ClusterInfo,
    ClusterMode,
    ClusterSSHKeyPair,
    ClusterSSHPortMapping,
)


class PrepareSSHFixture:
    """Provides mock context, patches, and a call method for prepare_ssh tests."""

    def __init__(self, tmp_path: Path, mocker: MockerFixture) -> None:
        self.tmp_path = tmp_path
        self.config_dir = tmp_path / "config"
        self.ctx = self._build_mock_ctx()

        self.mock_subprocess_run = mocker.patch(
            "ai.backend.agent.docker.agent.subprocess_run",
            side_effect=self._default_subprocess_side_effect,
        )
        self.mock_get_arch_name = mocker.patch(
            "ai.backend.agent.docker.agent.get_arch_name",
            return_value="x86_64",
        )

        mock_current_loop = mocker.patch("ai.backend.agent.docker.agent.current_loop")
        mock_event_loop = MagicMock()

        async def run_in_executor_sync(executor: Any, fn: Any, *args: Any) -> Any:
            return fn(*args)

        mock_event_loop.run_in_executor = run_in_executor_sync
        mock_current_loop.return_value = mock_event_loop

    def _build_mock_ctx(self) -> MagicMock:
        ctx = MagicMock(spec=DockerKernelCreationContext)
        ctx.config_dir = self.config_dir
        bin_path = self.tmp_path / "dropbearmulti.x86_64.bin"
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

    def _default_subprocess_side_effect(self, *args: Any, **kwargs: Any) -> None:
        host_key_path = self.config_dir / "ssh" / "dropbear_rsa_host_key"
        host_key_path.parent.mkdir(parents=True, exist_ok=True)
        host_key_path.write_bytes(b"fake-host-key")

    async def call(self, cluster_info: ClusterInfo) -> None:
        await DockerKernelCreationContext.prepare_ssh(self.ctx, cluster_info)

    @property
    def ssh_dir(self) -> Path:
        return self.config_dir / "ssh"


@pytest.fixture()
def prepare_ssh(tmp_path: Path, mocker: MockerFixture) -> PrepareSSHFixture:
    return PrepareSSHFixture(tmp_path, mocker)


@pytest.fixture()
def cluster_info_with_keypair() -> ClusterInfo:
    return ClusterInfo(
        mode=ClusterMode.SINGLE_NODE,
        size=1,
        replicas={},
        network_config={},
        ssh_keypair=ClusterSSHKeyPair(
            private_key="-----BEGIN RSA PRIVATE KEY-----\nfake\n-----END RSA PRIVATE KEY-----",
            public_key="ssh-rsa AAAAFAKE user@host",
        ),
        cluster_ssh_port_mapping=None,
    )


@pytest.fixture()
def cluster_info_no_keypair() -> ClusterInfo:
    return ClusterInfo(
        mode=ClusterMode.SINGLE_NODE,
        size=1,
        replicas={},
        network_config={},
        ssh_keypair=None,
        cluster_ssh_port_mapping=None,
    )


class TestPrepareSshHostKeyGeneration:
    async def test_calls_dropbearkey_with_correct_args(
        self,
        prepare_ssh: PrepareSSHFixture,
        cluster_info_no_keypair: ClusterInfo,
    ) -> None:
        await prepare_ssh.call(cluster_info_no_keypair)

        prepare_ssh.mock_subprocess_run.assert_called_once()
        call_args = prepare_ssh.mock_subprocess_run.call_args
        cmd = call_args[0][0]
        dropbearmulti = prepare_ssh.ctx.resolve_krunner_filepath.return_value
        expected_key_path = str(prepare_ssh.ssh_dir / "dropbear_rsa_host_key")
        assert cmd == [
            str(dropbearmulti),
            "dropbearkey",
            "-t",
            "rsa",
            "-s",
            "2048",
            "-f",
            expected_key_path,
        ]
        assert call_args.kwargs["check"] is True
        assert call_args.kwargs["capture_output"] is True

    async def test_skips_generation_when_host_key_exists(
        self,
        prepare_ssh: PrepareSSHFixture,
        cluster_info_no_keypair: ClusterInfo,
    ) -> None:
        prepare_ssh.ssh_dir.mkdir(parents=True, exist_ok=True)
        (prepare_ssh.ssh_dir / "dropbear_rsa_host_key").write_text("existing_key")

        await prepare_ssh.call(cluster_info_no_keypair)

        prepare_ssh.mock_subprocess_run.assert_not_called()

    async def test_raises_file_not_found_when_binary_missing(
        self,
        prepare_ssh: PrepareSSHFixture,
        cluster_info_no_keypair: ClusterInfo,
    ) -> None:
        prepare_ssh.ctx.resolve_krunner_filepath.return_value = (
            prepare_ssh.tmp_path / "nonexistent.bin"
        )

        await prepare_ssh.call(cluster_info_no_keypair)

        assert not (prepare_ssh.ssh_dir / "id_cluster").exists()

    async def test_logs_and_reraises_on_subprocess_failure(
        self,
        prepare_ssh: PrepareSSHFixture,
        cluster_info_no_keypair: ClusterInfo,
    ) -> None:
        prepare_ssh.mock_subprocess_run.side_effect = CalledProcessError(
            1, "dropbearkey", b"out", b"err"
        )

        await prepare_ssh.call(cluster_info_no_keypair)

        assert not (prepare_ssh.ssh_dir / "id_cluster").exists()

    async def test_host_key_gets_chmod_0o600(
        self,
        prepare_ssh: PrepareSSHFixture,
        cluster_info_no_keypair: ClusterInfo,
    ) -> None:
        await prepare_ssh.call(cluster_info_no_keypair)

        host_key = prepare_ssh.ssh_dir / "dropbear_rsa_host_key"
        assert host_key.stat().st_mode & 0o777 == 0o600


class TestPrepareSshClusterKeypair:
    async def test_writes_keypair_with_correct_permissions(
        self,
        prepare_ssh: PrepareSSHFixture,
        cluster_info_with_keypair: ClusterInfo,
    ) -> None:
        await prepare_ssh.call(cluster_info_with_keypair)

        priv_key = prepare_ssh.ssh_dir / "id_cluster"
        pub_key = prepare_ssh.ssh_dir / "id_cluster.pub"
        assert cluster_info_with_keypair["ssh_keypair"] is not None  # for mypy
        assert priv_key.read_text() == cluster_info_with_keypair["ssh_keypair"]["private_key"]
        assert pub_key.read_text() == cluster_info_with_keypair["ssh_keypair"]["public_key"]
        assert priv_key.stat().st_mode & 0o777 == 0o600

    async def test_skips_cluster_keypair_when_sshkey_none(
        self,
        prepare_ssh: PrepareSSHFixture,
        cluster_info_no_keypair: ClusterInfo,
    ) -> None:
        await prepare_ssh.call(cluster_info_no_keypair)

        assert not (prepare_ssh.ssh_dir / "id_cluster").exists()
        assert not (prepare_ssh.ssh_dir / "id_cluster.pub").exists()
        assert (prepare_ssh.ssh_dir / "dropbear_rsa_host_key").exists()


class TestPrepareSshPortMapping:
    async def test_writes_port_mapping_json(
        self,
        prepare_ssh: PrepareSSHFixture,
        cluster_info_with_keypair: ClusterInfo,
    ) -> None:
        port_mapping = ClusterSSHPortMapping({
            "node1": ("10.0.0.1", 2222),
            "node2": ("10.0.0.2", 2223),
        })
        cluster_info_with_keypair["cluster_ssh_port_mapping"] = port_mapping

        await prepare_ssh.call(cluster_info_with_keypair)

        mapping_path = prepare_ssh.ssh_dir / "port-mapping.json"
        assert mapping_path.exists()
        written = json.loads(mapping_path.read_bytes())
        assert written == {k: list(v) for k, v in port_mapping.items()}

    async def test_skips_port_mapping_when_none(
        self,
        prepare_ssh: PrepareSSHFixture,
        cluster_info_with_keypair: ClusterInfo,
    ) -> None:
        await prepare_ssh.call(cluster_info_with_keypair)

        assert not (prepare_ssh.ssh_dir / "port-mapping.json").exists()


class TestPrepareSshChown:
    async def test_chown_called_with_overriding_uid_gid(
        self,
        prepare_ssh: PrepareSSHFixture,
        cluster_info_with_keypair: ClusterInfo,
    ) -> None:
        prepare_ssh.ctx.get_overriding_uid.return_value = 5000
        prepare_ssh.ctx.get_overriding_gid.return_value = 5001

        await prepare_ssh.call(cluster_info_with_keypair)

        prepare_ssh.ctx._chown_paths_if_root.assert_called_once()
        call_args = prepare_ssh.ctx._chown_paths_if_root.call_args
        assert call_args[0][1] == 5000
        assert call_args[0][2] == 5001
        path_names = [p.name for p in call_args[0][0]]
        assert "dropbear_rsa_host_key" in path_names
        assert "id_cluster" in path_names
        assert "id_cluster.pub" in path_names

    async def test_chown_called_with_uid_match_feature(
        self,
        prepare_ssh: PrepareSSHFixture,
        cluster_info_with_keypair: ClusterInfo,
    ) -> None:
        prepare_ssh.ctx.kernel_features = frozenset({KernelFeatures.UID_MATCH})

        await prepare_ssh.call(cluster_info_with_keypair)

        prepare_ssh.ctx._chown_paths_if_root.assert_called_once()
        call_args = prepare_ssh.ctx._chown_paths_if_root.call_args
        assert call_args[0][1] == prepare_ssh.ctx.local_config.container.kernel_uid
        assert call_args[0][2] == prepare_ssh.ctx.local_config.container.kernel_gid

    async def test_chown_skipped_when_no_override_and_no_uid_match(
        self,
        prepare_ssh: PrepareSSHFixture,
        cluster_info_with_keypair: ClusterInfo,
    ) -> None:
        await prepare_ssh.call(cluster_info_with_keypair)

        prepare_ssh.ctx._chown_paths_if_root.assert_not_called()

    async def test_chown_called_with_only_overriding_uid(
        self,
        prepare_ssh: PrepareSSHFixture,
        cluster_info_with_keypair: ClusterInfo,
    ) -> None:
        prepare_ssh.ctx.get_overriding_uid.return_value = 5000

        await prepare_ssh.call(cluster_info_with_keypair)

        prepare_ssh.ctx._chown_paths_if_root.assert_called_once()
        call_args = prepare_ssh.ctx._chown_paths_if_root.call_args
        assert call_args[0][1] == 5000
        assert call_args[0][2] is None
