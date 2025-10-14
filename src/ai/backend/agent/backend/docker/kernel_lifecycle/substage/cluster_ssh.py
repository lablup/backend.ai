import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, override

from ai.backend.common.json import dump_json
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import (
    ClusterSSHKeyPair,
    ClusterSSHPortMapping,
)

from .types import ContainerOwnershipData
from .utils import ChownUtil, PathOwnerDeterminer


@dataclass
class ClusterSSHSpec:
    config_dir: Path
    ssh_keypair: Optional[ClusterSSHKeyPair]
    cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping]

    container_ownership: ContainerOwnershipData


class ClusterSSHSpecGenerator(ArgsSpecGenerator[ClusterSSHSpec]):
    pass


@dataclass
class ClusterSSHResult:
    pub_key_path: Optional[Path]
    priv_key_path: Optional[Path]
    port_mapping_json_path: Optional[Path]


class ClusterSSHProvisioner(Provisioner[ClusterSSHSpec, ClusterSSHResult]):
    @property
    @override
    def name(self) -> str:
        return "docker-ssh"

    @override
    async def setup(self, spec: ClusterSSHSpec) -> ClusterSSHResult:
        return await self._write_config(spec)

    async def _write_config(self, spec: ClusterSSHSpec) -> ClusterSSHResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._write_config_func, spec)

    def _write_config_func(self, spec: ClusterSSHSpec) -> ClusterSSHResult:
        sshkey = spec.ssh_keypair
        if sshkey is None:
            return ClusterSSHResult(None, None, None)

        priv_key_path = spec.config_dir / "ssh" / "id_cluster"
        pub_key_path = spec.config_dir / "ssh" / "id_cluster.pub"
        priv_key_path.parent.mkdir(parents=True, exist_ok=True)
        priv_key_path.write_text(sshkey["private_key"])
        pub_key_path.write_text(sshkey["public_key"])

        chowner = ChownUtil()
        owner_determiner = PathOwnerDeterminer.by_kernel_features(
            spec.container_ownership.kernel_uid,
            spec.container_ownership.kernel_gid,
            spec.container_ownership.kernel_features,
        )
        for path in [priv_key_path, pub_key_path]:
            uid, gid = owner_determiner.determine(
                path,
                uid_override=spec.container_ownership.uid_override,
                gid_override=spec.container_ownership.gid_override,
            )
            chowner.chown_path(path, uid, gid)

        priv_key_path.chmod(0o600)
        if cluster_ssh_port_mapping := spec.cluster_ssh_port_mapping:
            port_mapping_json_path = spec.config_dir / "ssh" / "port-mapping.json"
            port_mapping_json_path.write_bytes(dump_json(cluster_ssh_port_mapping))
        else:
            port_mapping_json_path = None
        return ClusterSSHResult(
            pub_key_path=pub_key_path,
            priv_key_path=priv_key_path,
            port_mapping_json_path=port_mapping_json_path,
        )

    @override
    async def teardown(self, resource: ClusterSSHResult) -> None:
        pass


class ClusterSSHStage(ProvisionStage[ClusterSSHSpec, ClusterSSHResult]):
    pass
