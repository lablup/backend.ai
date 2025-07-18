"""
Container SSH stage for kernel lifecycle.

This stage handles SSH key setup inside containers for inter-container communication.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, override

from ai.backend.agent.resources import Mount
from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage
from ai.backend.common.types import ContainerSSHKeyPair

from .utils import ChownUtil, PathOwnerDeterminer


@dataclass
class AgentConfig:
    kernel_features: frozenset[str]
    kernel_uid: int
    kernel_gid: int


@dataclass
class ContainerSSHSpec:
    work_dir: Path
    ssh_keypair: ContainerSSHKeyPair
    mounts: list[Mount]

    # Override UID/GID settings
    uid_override: Optional[int]
    gid_override: Optional[int]

    agent_config: AgentConfig


class ContainerSSHSpecGenerator(ArgsSpecGenerator[ContainerSSHSpec]):
    pass


@dataclass
class ContainerSSHResult:
    ssh_dir: Optional[Path]


class ContainerSSHProvisioner(Provisioner[ContainerSSHSpec, ContainerSSHResult]):
    """
    Provisioner for container SSH configuration.

    Sets up SSH keypairs in the container work directory for inter-container communication.
    This is different from cluster SSH which is handled by a separate SSHStage.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-container-ssh"

    @override
    async def setup(self, spec: ContainerSSHSpec) -> ContainerSSHResult:
        if not spec.ssh_keypair:
            return ContainerSSHResult(ssh_dir=None)

        # Check if /home/work/.ssh is already mounted
        for mount in spec.mounts:
            container_path = mount.target
            if container_path == Path("/home/work/.ssh"):
                # SSH directory is already mounted, skip setup
                return ContainerSSHResult(ssh_dir=None)

        loop = asyncio.get_running_loop()

        ssh_dir = await loop.run_in_executor(None, self._populate_ssh_config, spec)
        return ContainerSSHResult(ssh_dir=ssh_dir)

    def _populate_ssh_config(self, spec: ContainerSSHSpec) -> Path:
        pubkey = spec.ssh_keypair.public_key.encode("ascii")
        privkey = spec.ssh_keypair.private_key.encode("ascii")
        ssh_dir = spec.work_dir / ".ssh"

        # Create SSH directory
        ssh_dir.mkdir(parents=True, exist_ok=True)
        ssh_dir.chmod(0o700)

        # Write SSH keys
        (ssh_dir / "authorized_keys").write_bytes(pubkey)
        (ssh_dir / "authorized_keys").chmod(0o600)

        if not (ssh_dir / "id_rsa").is_file():
            (ssh_dir / "id_rsa").write_bytes(privkey)
            (ssh_dir / "id_rsa").chmod(0o600)

        # Write container key for backward compatibility
        (spec.work_dir / "id_container").write_bytes(privkey)
        (spec.work_dir / "id_container").chmod(0o600)

        # Set proper ownership
        paths = [
            ssh_dir,
            ssh_dir / "authorized_keys",
            ssh_dir / "id_rsa",
            spec.work_dir / "id_container",
        ]

        chowner = ChownUtil()
        owner_determiner = PathOwnerDeterminer.by_kernel_features(
            spec.agent_config.kernel_uid,
            spec.agent_config.kernel_gid,
            spec.agent_config.kernel_features,
        )
        for path in paths:
            uid, gid = owner_determiner.determine(
                path, uid_override=spec.uid_override, gid_override=spec.gid_override
            )
            chowner.chown_path(path, uid, gid)

        return ssh_dir

    @override
    async def teardown(self, resource: ContainerSSHResult) -> None:
        # SSH files are cleaned up with scratch directory
        pass


class ContainerSSHStage(ProvisionStage[ContainerSSHSpec, ContainerSSHResult]):
    """
    Stage for setting up SSH keys inside containers.
    """

    pass
