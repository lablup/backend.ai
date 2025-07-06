import asyncio
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, override

from ai.backend.common.docker import KernelFeatures
from ai.backend.common.json import dump_json
from ai.backend.common.stage.types import (
    Provisioner,
    ProvisionStage,
    SpecGenerator,
)
from ai.backend.common.types import (
    ClusterSSHKeyPair,
    ClusterSSHPortMapping,
)


@dataclass
class SSHSpec:
    config_dir: Path
    ssh_keypair: Optional[ClusterSSHKeyPair]
    cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping]

    agent_kernel_features: frozenset[KernelFeatures]
    agent_kernel_uid: int
    agent_kernel_gid: int

    overriding_uid: Optional[int]
    overriding_gid: Optional[int]
    supplementary_gids: set[int]


class SSHSpecGenerator(SpecGenerator[SSHSpec]):
    def __init__(
        self,
        config_dir: Path,
        ssh_keypair: Optional[ClusterSSHKeyPair],
        cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping],
        agent_kernel_features: frozenset[KernelFeatures],
        agent_kernel_uid: int,
        agent_kernel_gid: int,
        overriding_uid: Optional[int],
        overriding_gid: Optional[int],
        supplementary_gids: set[int],
    ) -> None:
        self._config_dir = config_dir
        self._ssh_keypair = ssh_keypair
        self._cluster_ssh_port_mapping = cluster_ssh_port_mapping
        self._agent_kernel_features = agent_kernel_features
        self._agent_kernel_uid = agent_kernel_uid
        self._agent_kernel_gid = agent_kernel_gid
        self._overriding_uid = overriding_uid
        self._overriding_gid = overriding_gid
        self._supplementary_gids = supplementary_gids

    @override
    async def wait_for_spec(self) -> SSHSpec:
        """
        Waits for the spec to be ready.
        """
        return SSHSpec(
            config_dir=self._config_dir,
            ssh_keypair=self._ssh_keypair,
            cluster_ssh_port_mapping=self._cluster_ssh_port_mapping,
            agent_kernel_features=self._agent_kernel_features,
            agent_kernel_uid=self._agent_kernel_uid,
            agent_kernel_gid=self._agent_kernel_gid,
            overriding_uid=self._overriding_uid,
            overriding_gid=self._overriding_gid,
            supplementary_gids=self._supplementary_gids,
        )


@dataclass
class SSHResult:
    pass


class SSHProvisioner(Provisioner[SSHSpec, SSHResult]):
    @property
    @override
    def name(self) -> str:
        return "docker-ssh"

    @override
    async def setup(self, spec: SSHSpec) -> SSHResult:
        await self._write_config(spec)
        return SSHResult()

    async def _write_config(self, spec: SSHSpec) -> None:
        sshkey = spec.ssh_keypair
        if sshkey is None:
            return

        def chown_paths_if_root(
            paths: Iterable[Path], uid: Optional[int], gid: Optional[int]
        ) -> None:
            if os.geteuid() == 0:  # only possible when I am root.
                for p in paths:
                    if KernelFeatures.UID_MATCH in spec.agent_kernel_features:
                        valid_uid = uid if uid is not None else spec.agent_kernel_uid
                        valid_gid = gid if gid is not None else spec.agent_kernel_gid
                    else:
                        stat = os.stat(p)
                        valid_uid = uid if uid is not None else stat.st_uid
                        valid_gid = gid if gid is not None else stat.st_gid
                    os.chown(p, valid_uid, valid_gid)

        def write_config() -> None:
            priv_key_path = spec.config_dir / "ssh" / "id_cluster"
            pub_key_path = spec.config_dir / "ssh" / "id_cluster.pub"
            priv_key_path.parent.mkdir(parents=True, exist_ok=True)
            priv_key_path.write_text(sshkey["private_key"])
            pub_key_path.write_text(sshkey["public_key"])

            do_override = False
            if (ouid := spec.overriding_uid) is not None:
                do_override = True

            if (ogid := spec.overriding_gid) is not None:
                do_override = True

            if do_override:
                chown_paths_if_root([priv_key_path, pub_key_path], ouid, ogid)
            else:
                if KernelFeatures.UID_MATCH in spec.agent_kernel_features:
                    chown_paths_if_root(
                        [priv_key_path, pub_key_path], spec.agent_kernel_uid, spec.agent_kernel_gid
                    )

            priv_key_path.chmod(0o600)
            if cluster_ssh_port_mapping := spec.cluster_ssh_port_mapping:
                port_mapping_json_path = spec.config_dir / "ssh" / "port-mapping.json"
                port_mapping_json_path.write_bytes(dump_json(cluster_ssh_port_mapping))

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, write_config)

    @override
    async def teardown(self, resource: SSHResult) -> None:
        pass


class SSHStage(ProvisionStage[SSHSpec, SSHResult]):
    pass
