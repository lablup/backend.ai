"""Unit tests for SSH stage provisioners and utility classes."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.agent.stage.kernel_lifecycle.docker.container_ssh import (
    AgentConfig,
    ContainerSSHProvisioner,
    ContainerSSHResult,
    ContainerSSHSpec,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.ssh import (
    Chowner,
    SSHProvisioner,
    SSHResult,
    SSHSpec,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.utils import (
    ChownUtil,
    PathOwnerDeterminer,
)
from ai.backend.common.docker import KernelFeatures

# ---------------------------------------------------------------------------
# PathOwnerDeterminer
# ---------------------------------------------------------------------------


class TestPathOwnerDeterminer:
    def test_determine_with_uid_gid_override(self, tmp_path: Path) -> None:
        p = tmp_path / "f"
        p.touch()
        det = PathOwnerDeterminer(kernel_uid=1000, kernel_gid=1000, do_uid_match=False)
        uid, gid = det.determine(p, uid_override=5000, gid_override=6000)
        assert uid == 5000
        assert gid == 6000

    def test_determine_with_uid_match_no_override(self, tmp_path: Path) -> None:
        p = tmp_path / "f"
        p.touch()
        det = PathOwnerDeterminer(kernel_uid=1000, kernel_gid=1001, do_uid_match=True)
        uid, gid = det.determine(p, uid_override=None, gid_override=None)
        assert uid == 1000
        assert gid == 1001

    def test_determine_without_uid_match_no_override(self, tmp_path: Path) -> None:
        p = tmp_path / "f"
        p.touch()
        st = p.stat()
        det = PathOwnerDeterminer(kernel_uid=9999, kernel_gid=9999, do_uid_match=False)
        uid, gid = det.determine(p, uid_override=None, gid_override=None)
        assert uid == st.st_uid
        assert gid == st.st_gid

    def test_determine_mixed_override(self, tmp_path: Path) -> None:
        p = tmp_path / "f"
        p.touch()
        det = PathOwnerDeterminer(kernel_uid=1000, kernel_gid=1001, do_uid_match=True)
        uid, gid = det.determine(p, uid_override=5000, gid_override=None)
        assert uid == 5000
        assert gid == 1001

        uid2, gid2 = det.determine(p, uid_override=None, gid_override=6000)
        assert uid2 == 1000
        assert gid2 == 6000

    def test_by_kernel_features_with_uid_match(self) -> None:
        det = PathOwnerDeterminer.by_kernel_features(
            kernel_uid=1000,
            kernel_gid=1001,
            kernel_features=frozenset({KernelFeatures.UID_MATCH}),
        )
        assert det._do_uid_match is True

    def test_by_kernel_features_without_uid_match(self) -> None:
        det = PathOwnerDeterminer.by_kernel_features(
            kernel_uid=1000,
            kernel_gid=1001,
            kernel_features=frozenset(),
        )
        assert det._do_uid_match is False


# ---------------------------------------------------------------------------
# ChownUtil
# ---------------------------------------------------------------------------


class TestChownUtil:
    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.utils.os.geteuid", return_value=0)
    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.utils.os.chown")
    def test_chown_path_as_root(
        self, mock_chown: MagicMock, mock_geteuid: MagicMock, tmp_path: Path
    ) -> None:
        p = tmp_path / "f"
        p.touch()
        util = ChownUtil()
        util.chown_path(p, 1000, 1001)
        mock_chown.assert_called_once_with(p, 1000, 1001)

    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.utils.os.geteuid", return_value=1000)
    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.utils.os.chown")
    def test_chown_path_as_non_root(
        self, mock_chown: MagicMock, mock_geteuid: MagicMock, tmp_path: Path
    ) -> None:
        p = tmp_path / "f"
        p.touch()
        util = ChownUtil()
        util.chown_path(p, 1000, 1001)
        mock_chown.assert_not_called()

    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.utils.os.geteuid", return_value=0)
    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.utils.os.chown")
    def test_chown_paths_as_root(
        self, mock_chown: MagicMock, mock_geteuid: MagicMock, tmp_path: Path
    ) -> None:
        p1 = tmp_path / "a"
        p2 = tmp_path / "b"
        p1.touch()
        p2.touch()
        util = ChownUtil()
        util.chown_paths([p1, p2], 500, 501)
        assert mock_chown.call_count == 2

    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.utils.os.geteuid", return_value=1000)
    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.utils.os.chown")
    def test_chown_paths_as_non_root(
        self, mock_chown: MagicMock, mock_geteuid: MagicMock, tmp_path: Path
    ) -> None:
        p1 = tmp_path / "a"
        p2 = tmp_path / "b"
        p1.touch()
        p2.touch()
        util = ChownUtil()
        util.chown_paths([p1, p2], 500, 501)
        mock_chown.assert_not_called()


# ---------------------------------------------------------------------------
# Chowner (ssh.py)
# ---------------------------------------------------------------------------


class TestChowner:
    @staticmethod
    def _make_spec(
        *,
        uid_match: bool = False,
        kernel_uid: int = 1000,
        kernel_gid: int = 1001,
    ) -> SSHSpec:
        features: frozenset[KernelFeatures] = (
            frozenset({KernelFeatures.UID_MATCH}) if uid_match else frozenset()
        )
        return SSHSpec(
            config_dir=Path("/tmp/fake"),
            ssh_keypair=None,
            cluster_ssh_port_mapping=None,
            agent_kernel_features=features,
            agent_kernel_uid=kernel_uid,
            agent_kernel_gid=kernel_gid,
            overriding_uid=None,
            overriding_gid=None,
            supplementary_gids=set(),
        )

    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os.geteuid", return_value=1000)
    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os.chown")
    def test_chown_paths_if_root_as_non_root(
        self, mock_chown: MagicMock, mock_geteuid: MagicMock, tmp_path: Path
    ) -> None:
        spec = self._make_spec(uid_match=True)
        chowner = Chowner(spec)
        p = tmp_path / "f"
        p.touch()
        chowner.chown_paths_if_root([p], 500, 501)
        mock_chown.assert_not_called()

    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os.geteuid", return_value=0)
    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os.chown")
    def test_chown_paths_if_root_with_uid_match(
        self, mock_chown: MagicMock, mock_geteuid: MagicMock, tmp_path: Path
    ) -> None:
        spec = self._make_spec(uid_match=True, kernel_uid=2000, kernel_gid=2001)
        chowner = Chowner(spec)
        p = tmp_path / "f"
        p.touch()
        chowner.chown_paths_if_root([p], None, None)
        mock_chown.assert_called_once_with(p, 2000, 2001)

    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os.geteuid", return_value=0)
    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os.chown")
    def test_chown_paths_if_root_without_uid_match(
        self, mock_chown: MagicMock, mock_geteuid: MagicMock, tmp_path: Path
    ) -> None:
        spec = self._make_spec(uid_match=False)
        chowner = Chowner(spec)
        p = tmp_path / "f"
        p.touch()
        st = p.stat()
        chowner.chown_paths_if_root([p], None, None)
        mock_chown.assert_called_once_with(p, st.st_uid, st.st_gid)

    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os.geteuid", return_value=0)
    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os.chown")
    def test_chown_paths_if_root_with_override_uid_gid(
        self, mock_chown: MagicMock, mock_geteuid: MagicMock, tmp_path: Path
    ) -> None:
        spec = self._make_spec(uid_match=True, kernel_uid=2000, kernel_gid=2001)
        chowner = Chowner(spec)
        p = tmp_path / "f"
        p.touch()
        chowner.chown_paths_if_root([p], 5000, 6000)
        mock_chown.assert_called_once_with(p, 5000, 6000)


# ---------------------------------------------------------------------------
# SSHProvisioner._write_config_func
# ---------------------------------------------------------------------------


class TestSSHProvisionerWriteConfigFunc:
    @staticmethod
    def _make_spec(
        tmp_path: Path,
        *,
        keypair: dict[str, str] | None = None,
        port_mapping: object | None = None,
        uid_match: bool = False,
        overriding_uid: int | None = None,
        overriding_gid: int | None = None,
        kernel_uid: int = 1000,
        kernel_gid: int = 1001,
    ) -> SSHSpec:
        features: frozenset[KernelFeatures] = (
            frozenset({KernelFeatures.UID_MATCH}) if uid_match else frozenset()
        )
        return SSHSpec(
            config_dir=tmp_path / "config",
            ssh_keypair=keypair,
            cluster_ssh_port_mapping=port_mapping,
            agent_kernel_features=features,
            agent_kernel_uid=kernel_uid,
            agent_kernel_gid=kernel_gid,
            overriding_uid=overriding_uid,
            overriding_gid=overriding_gid,
            supplementary_gids=set(),
        )

    def test_write_config_func_none_keypair(self, tmp_path: Path) -> None:
        spec = self._make_spec(tmp_path, keypair=None)
        provisioner = SSHProvisioner()
        result = provisioner._write_config_func(spec)
        assert result == SSHResult(None, None, None)

    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os.geteuid", return_value=1000)
    def test_write_config_func_valid_keypair(self, mock_geteuid: MagicMock, tmp_path: Path) -> None:
        keypair = {"public_key": "ssh-rsa AAAA...", "private_key": "-----BEGIN RSA-----\n..."}
        spec = self._make_spec(tmp_path, keypair=keypair)
        provisioner = SSHProvisioner()
        result = provisioner._write_config_func(spec)

        assert result.pub_key_path is not None
        assert result.priv_key_path is not None
        assert result.port_mapping_json_path is None

        assert result.pub_key_path.read_text() == keypair["public_key"]
        assert result.priv_key_path.read_text() == keypair["private_key"]
        assert oct(result.priv_key_path.stat().st_mode & 0o777) == oct(0o600)

    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os.geteuid", return_value=1000)
    def test_write_config_func_with_port_mapping(
        self, mock_geteuid: MagicMock, tmp_path: Path
    ) -> None:
        keypair = {"public_key": "pub", "private_key": "priv"}
        port_mapping = {"node1": ("192.168.0.1", 2200)}
        spec = self._make_spec(tmp_path, keypair=keypair, port_mapping=port_mapping)
        provisioner = SSHProvisioner()
        result = provisioner._write_config_func(spec)

        assert result.port_mapping_json_path is not None
        assert result.port_mapping_json_path.exists()

    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os.geteuid", return_value=0)
    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os.chown")
    def test_write_config_func_with_override_uid_gid(
        self, mock_chown: MagicMock, mock_geteuid: MagicMock, tmp_path: Path
    ) -> None:
        keypair = {"public_key": "pub", "private_key": "priv"}
        spec = self._make_spec(tmp_path, keypair=keypair, overriding_uid=5000, overriding_gid=6000)
        provisioner = SSHProvisioner()
        provisioner._write_config_func(spec)

        assert mock_chown.call_count == 2
        for call in mock_chown.call_args_list:
            assert call.args[1] == 5000
            assert call.args[2] == 6000

    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os.geteuid", return_value=0)
    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.ssh.os.chown")
    def test_write_config_func_with_uid_match(
        self, mock_chown: MagicMock, mock_geteuid: MagicMock, tmp_path: Path
    ) -> None:
        keypair = {"public_key": "pub", "private_key": "priv"}
        spec = self._make_spec(
            tmp_path, keypair=keypair, uid_match=True, kernel_uid=2000, kernel_gid=2001
        )
        provisioner = SSHProvisioner()
        provisioner._write_config_func(spec)

        assert mock_chown.call_count == 2
        for call in mock_chown.call_args_list:
            assert call.args[1] == 2000
            assert call.args[2] == 2001


# ---------------------------------------------------------------------------
# ContainerSSHProvisioner
# ---------------------------------------------------------------------------


class TestContainerSSHProvisioner:
    @staticmethod
    def _make_keypair() -> MagicMock:
        kp = MagicMock()
        kp.public_key = "ssh-rsa AAAA..."
        kp.private_key = "-----BEGIN RSA-----\nfake"
        return kp

    @staticmethod
    def _make_spec(
        work_dir: Path,
        *,
        keypair: object | None = None,
        mounts: list[object] | None = None,
        uid_override: int | None = None,
        gid_override: int | None = None,
        uid_match: bool = False,
        kernel_uid: int = 1000,
        kernel_gid: int = 1001,
    ) -> ContainerSSHSpec:
        features: frozenset[str] = (
            frozenset({KernelFeatures.UID_MATCH}) if uid_match else frozenset()
        )
        return ContainerSSHSpec(
            work_dir=work_dir,
            ssh_keypair=keypair,
            mounts=mounts or [],
            uid_override=uid_override,
            gid_override=gid_override,
            agent_config=AgentConfig(
                kernel_features=features,
                kernel_uid=kernel_uid,
                kernel_gid=kernel_gid,
            ),
        )

    @pytest.mark.asyncio
    async def test_setup_no_keypair(self, tmp_path: Path) -> None:
        spec = self._make_spec(tmp_path, keypair=None)
        provisioner = ContainerSSHProvisioner()
        result = await provisioner.setup(spec)
        assert result == ContainerSSHResult(ssh_dir=None)

    @pytest.mark.asyncio
    async def test_setup_ssh_already_mounted(self, tmp_path: Path) -> None:
        mount = MagicMock()
        mount.target = Path("/home/work/.ssh")
        kp = self._make_keypair()
        spec = self._make_spec(tmp_path, keypair=kp, mounts=[mount])
        provisioner = ContainerSSHProvisioner()
        result = await provisioner.setup(spec)
        assert result == ContainerSSHResult(ssh_dir=None)

    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.utils.os.geteuid", return_value=1000)
    def test_populate_ssh_config_creates_files(
        self, mock_geteuid: MagicMock, tmp_path: Path
    ) -> None:
        kp = self._make_keypair()
        spec = self._make_spec(tmp_path, keypair=kp)
        provisioner = ContainerSSHProvisioner()
        ssh_dir = provisioner._populate_ssh_config(spec)

        assert ssh_dir == tmp_path / ".ssh"
        assert ssh_dir.is_dir()
        assert oct(ssh_dir.stat().st_mode & 0o777) == oct(0o700)

        auth_keys = ssh_dir / "authorized_keys"
        assert auth_keys.read_bytes() == kp.public_key.encode("ascii")
        assert oct(auth_keys.stat().st_mode & 0o777) == oct(0o600)

        id_rsa = ssh_dir / "id_rsa"
        assert id_rsa.read_bytes() == kp.private_key.encode("ascii")
        assert oct(id_rsa.stat().st_mode & 0o777) == oct(0o600)

        id_container = tmp_path / "id_container"
        assert id_container.read_bytes() == kp.private_key.encode("ascii")
        assert oct(id_container.stat().st_mode & 0o777) == oct(0o600)

    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.utils.os.geteuid", return_value=1000)
    def test_populate_ssh_config_skips_existing_id_rsa(
        self, mock_geteuid: MagicMock, tmp_path: Path
    ) -> None:
        kp = self._make_keypair()
        spec = self._make_spec(tmp_path, keypair=kp)

        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        existing_content = b"existing-key-content"
        (ssh_dir / "id_rsa").write_bytes(existing_content)

        provisioner = ContainerSSHProvisioner()
        provisioner._populate_ssh_config(spec)

        assert (ssh_dir / "id_rsa").read_bytes() == existing_content

    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.utils.os.geteuid", return_value=0)
    @patch("ai.backend.agent.stage.kernel_lifecycle.docker.utils.os.chown")
    def test_populate_ssh_config_ownership(
        self, mock_chown: MagicMock, mock_geteuid: MagicMock, tmp_path: Path
    ) -> None:
        kp = self._make_keypair()
        spec = self._make_spec(tmp_path, keypair=kp, uid_override=3000, gid_override=3001)
        provisioner = ContainerSSHProvisioner()
        provisioner._populate_ssh_config(spec)

        assert mock_chown.call_count == 4
        for call in mock_chown.call_args_list:
            assert call.args[1] == 3000
            assert call.args[2] == 3001
