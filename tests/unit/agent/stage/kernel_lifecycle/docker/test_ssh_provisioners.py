"""Unit tests for SSH stage provisioners and utility classes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from ai.backend.agent.resources import Mount
from ai.backend.agent.stage.kernel_lifecycle.docker.container_ssh import (
    AgentConfig,
    ContainerSSHProvisioner,
    ContainerSSHResult,
    ContainerSSHSpec,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.ssh import (
    SSHProvisioner,
    SSHResult,
    SSHSpec,
)
from ai.backend.common.docker import KernelFeatures
from ai.backend.common.types import (
    ClusterSSHKeyPair,
    ClusterSSHPortMapping,
    ContainerSSHKeyPair,
    MountTypes,
)


@dataclass
class OwnershipParam:
    id: str
    uid_match: bool
    kernel_uid: int
    kernel_gid: int
    uid_override: int | None
    gid_override: int | None
    expected_uid: int
    expected_gid: int


_UTILS_OS = "ai.backend.agent.stage.kernel_lifecycle.docker.utils.os"
_SSH_OS = "ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os"


class TestSSHProvisionerWriteConfigFunc:
    @pytest.fixture
    def provisioner(self) -> SSHProvisioner:
        return SSHProvisioner()

    @pytest.fixture
    def cluster_ssh_keypair(self) -> ClusterSSHKeyPair:
        return ClusterSSHKeyPair(
            public_key="ssh-rsa AAAA...", private_key="-----BEGIN RSA-----\n..."
        )

    @pytest.fixture
    def spec_no_keypair(self, tmp_path: Path) -> SSHSpec:
        return SSHSpec(
            config_dir=tmp_path / "config",
            ssh_keypair=None,
            cluster_ssh_port_mapping=None,
            agent_kernel_features=frozenset(),
            agent_kernel_uid=1000,
            agent_kernel_gid=1001,
            overriding_uid=None,
            overriding_gid=None,
            supplementary_gids=set(),
        )

    @pytest.fixture
    def spec_with_keypair(self, tmp_path: Path, cluster_ssh_keypair: ClusterSSHKeyPair) -> SSHSpec:
        return SSHSpec(
            config_dir=tmp_path / "config",
            ssh_keypair=cluster_ssh_keypair,
            cluster_ssh_port_mapping=None,
            agent_kernel_features=frozenset(),
            agent_kernel_uid=1000,
            agent_kernel_gid=1001,
            overriding_uid=None,
            overriding_gid=None,
            supplementary_gids=set(),
        )

    @pytest.fixture
    def spec_with_port_mapping(
        self, tmp_path: Path, cluster_ssh_keypair: ClusterSSHKeyPair
    ) -> SSHSpec:
        return SSHSpec(
            config_dir=tmp_path / "config",
            ssh_keypair=cluster_ssh_keypair,
            cluster_ssh_port_mapping=ClusterSSHPortMapping({"node1": ("192.168.0.1", 2200)}),
            agent_kernel_features=frozenset(),
            agent_kernel_uid=1000,
            agent_kernel_gid=1001,
            overriding_uid=None,
            overriding_gid=None,
            supplementary_gids=set(),
        )

    async def test_write_config_func_none_keypair(
        self, provisioner: SSHProvisioner, spec_no_keypair: SSHSpec
    ) -> None:
        result = provisioner._write_config_func(spec_no_keypair)
        assert result == SSHResult(None, None, None)

    async def test_write_config_func_valid_keypair(
        self,
        provisioner: SSHProvisioner,
        cluster_ssh_keypair: ClusterSSHKeyPair,
        spec_with_keypair: SSHSpec,
    ) -> None:
        with patch(f"{_SSH_OS}.geteuid", return_value=1000):
            result = provisioner._write_config_func(spec_with_keypair)

        assert result.pub_key_path is not None
        assert result.priv_key_path is not None
        assert result.port_mapping_json_path is None

        assert result.pub_key_path.read_text() == cluster_ssh_keypair["public_key"]
        assert result.priv_key_path.read_text() == cluster_ssh_keypair["private_key"]
        assert oct(result.priv_key_path.stat().st_mode & 0o777) == oct(0o600)

    async def test_write_config_func_with_port_mapping(
        self, provisioner: SSHProvisioner, spec_with_port_mapping: SSHSpec
    ) -> None:
        with patch(f"{_SSH_OS}.geteuid", return_value=1000):
            result = provisioner._write_config_func(spec_with_port_mapping)

        assert result.port_mapping_json_path is not None
        assert result.port_mapping_json_path.exists()

    @pytest.mark.parametrize(
        "ownership",
        [
            OwnershipParam(
                id="override_uid_gid",
                uid_match=False,
                kernel_uid=1000,
                kernel_gid=1001,
                uid_override=5000,
                gid_override=6000,
                expected_uid=5000,
                expected_gid=6000,
            ),
            OwnershipParam(
                id="uid_match",
                uid_match=True,
                kernel_uid=2000,
                kernel_gid=2001,
                uid_override=None,
                gid_override=None,
                expected_uid=2000,
                expected_gid=2001,
            ),
        ],
        ids=lambda o: o.id,
    )
    async def test_write_config_func_chown(
        self, tmp_path: Path, provisioner: SSHProvisioner, ownership: OwnershipParam
    ) -> None:
        features: frozenset[KernelFeatures] = (
            frozenset({KernelFeatures.UID_MATCH}) if ownership.uid_match else frozenset()
        )
        spec = SSHSpec(
            config_dir=tmp_path / "config",
            ssh_keypair=ClusterSSHKeyPair(public_key="pub", private_key="priv"),
            cluster_ssh_port_mapping=None,
            agent_kernel_features=features,
            agent_kernel_uid=ownership.kernel_uid,
            agent_kernel_gid=ownership.kernel_gid,
            overriding_uid=ownership.uid_override,
            overriding_gid=ownership.gid_override,
            supplementary_gids=set(),
        )
        with (
            patch(f"{_SSH_OS}.geteuid", return_value=0),
            patch(f"{_SSH_OS}.chown") as mock_chown,
        ):
            provisioner._write_config_func(spec)

        assert mock_chown.call_count == 2
        for call in mock_chown.call_args_list:
            assert call.args[1] == ownership.expected_uid
            assert call.args[2] == ownership.expected_gid


# ---------------------------------------------------------------------------
# ContainerSSHProvisioner
# ---------------------------------------------------------------------------


class TestContainerSSHProvisioner:
    @pytest.fixture
    def agent_config(self) -> AgentConfig:
        return AgentConfig(
            kernel_features=frozenset(),
            kernel_uid=1000,
            kernel_gid=1001,
        )

    @pytest.fixture
    def ssh_keypair(self) -> ContainerSSHKeyPair:
        return ContainerSSHKeyPair(
            public_key="ssh-rsa AAAA...",
            private_key="-----BEGIN RSA-----\nfake",
        )

    @pytest.fixture
    def provisioner(self) -> ContainerSSHProvisioner:
        return ContainerSSHProvisioner()

    @pytest.fixture
    def spec_no_keypair(self, tmp_path: Path, agent_config: AgentConfig) -> ContainerSSHSpec:
        return ContainerSSHSpec(
            work_dir=tmp_path,
            ssh_keypair=cast(ContainerSSHKeyPair, None),
            mounts=[],
            uid_override=None,
            gid_override=None,
            agent_config=agent_config,
        )

    @pytest.fixture
    def spec_with_ssh_mount(
        self, tmp_path: Path, ssh_keypair: ContainerSSHKeyPair, agent_config: AgentConfig
    ) -> ContainerSSHSpec:
        return ContainerSSHSpec(
            work_dir=tmp_path,
            ssh_keypair=ssh_keypair,
            mounts=[Mount(type=MountTypes.BIND, source=None, target=Path("/home/work/.ssh"))],
            uid_override=None,
            gid_override=None,
            agent_config=agent_config,
        )

    @pytest.fixture
    def spec_default(
        self, tmp_path: Path, ssh_keypair: ContainerSSHKeyPair, agent_config: AgentConfig
    ) -> ContainerSSHSpec:
        return ContainerSSHSpec(
            work_dir=tmp_path,
            ssh_keypair=ssh_keypair,
            mounts=[],
            uid_override=None,
            gid_override=None,
            agent_config=agent_config,
        )

    @pytest.fixture
    def spec_with_ownership(
        self, tmp_path: Path, ssh_keypair: ContainerSSHKeyPair, agent_config: AgentConfig
    ) -> ContainerSSHSpec:
        return ContainerSSHSpec(
            work_dir=tmp_path,
            ssh_keypair=ssh_keypair,
            mounts=[],
            uid_override=3000,
            gid_override=3001,
            agent_config=agent_config,
        )

    async def test_setup_no_keypair(
        self, provisioner: ContainerSSHProvisioner, spec_no_keypair: ContainerSSHSpec
    ) -> None:
        result = await provisioner.setup(spec_no_keypair)
        assert result == ContainerSSHResult(ssh_dir=None)

    async def test_setup_ssh_already_mounted(
        self, provisioner: ContainerSSHProvisioner, spec_with_ssh_mount: ContainerSSHSpec
    ) -> None:
        result = await provisioner.setup(spec_with_ssh_mount)
        assert result == ContainerSSHResult(ssh_dir=None)

    async def test_populate_ssh_config_creates_files(
        self,
        tmp_path: Path,
        ssh_keypair: ContainerSSHKeyPair,
        provisioner: ContainerSSHProvisioner,
        spec_default: ContainerSSHSpec,
    ) -> None:
        with patch(f"{_UTILS_OS}.geteuid", return_value=1000):
            ssh_dir = provisioner._populate_ssh_config(spec_default)

        assert ssh_dir == tmp_path / ".ssh"
        assert ssh_dir.is_dir()
        assert oct(ssh_dir.stat().st_mode & 0o777) == oct(0o700)

        auth_keys = ssh_dir / "authorized_keys"
        assert auth_keys.read_bytes() == ssh_keypair.public_key.encode("ascii")
        assert oct(auth_keys.stat().st_mode & 0o777) == oct(0o600)

        id_rsa = ssh_dir / "id_rsa"
        assert id_rsa.read_bytes() == ssh_keypair.private_key.encode("ascii")
        assert oct(id_rsa.stat().st_mode & 0o777) == oct(0o600)

        id_container = tmp_path / "id_container"
        assert id_container.read_bytes() == ssh_keypair.private_key.encode("ascii")
        assert oct(id_container.stat().st_mode & 0o777) == oct(0o600)

    async def test_populate_ssh_config_skips_existing_id_rsa(
        self,
        tmp_path: Path,
        provisioner: ContainerSSHProvisioner,
        spec_default: ContainerSSHSpec,
    ) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        existing_content = b"existing-key-content"
        (ssh_dir / "id_rsa").write_bytes(existing_content)

        with patch(f"{_UTILS_OS}.geteuid", return_value=1000):
            provisioner._populate_ssh_config(spec_default)

        assert (ssh_dir / "id_rsa").read_bytes() == existing_content

    async def test_populate_ssh_config_ownership(
        self,
        provisioner: ContainerSSHProvisioner,
        spec_with_ownership: ContainerSSHSpec,
    ) -> None:
        with (
            patch(f"{_UTILS_OS}.geteuid", return_value=0),
            patch(f"{_UTILS_OS}.chown") as mock_chown,
        ):
            provisioner._populate_ssh_config(spec_with_ownership)

        assert mock_chown.call_count == 4
        for call in mock_chown.call_args_list:
            assert call.args[1] == 3000
            assert call.args[2] == 3001
