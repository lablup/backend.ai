import asyncio
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, override

from ai.backend.common.docker import KernelFeatures
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


class SSHSpecGenerator(ArgsSpecGenerator[SSHSpec]):
    pass


@dataclass
class SSHResult:
    pub_key_path: Optional[Path]
    priv_key_path: Optional[Path]
    port_mapping_json_path: Optional[Path]


class Chowner:
    def __init__(self, spec: SSHSpec) -> None:
        self._spec = spec
        self._euid = os.geteuid()

    def chown_paths_if_root(
        self, paths: Iterable[Path], uid: Optional[int], gid: Optional[int]
    ) -> None:
        if self._euid == 0:  # only possible when I am root.
            for p in paths:
                if KernelFeatures.UID_MATCH in self._spec.agent_kernel_features:
                    valid_uid = uid if uid is not None else self._spec.agent_kernel_uid
                    valid_gid = gid if gid is not None else self._spec.agent_kernel_gid
                else:
                    stat = os.stat(p)
                    valid_uid = uid if uid is not None else stat.st_uid
                    valid_gid = gid if gid is not None else stat.st_gid
                os.chown(p, valid_uid, valid_gid)


class SSHProvisioner(Provisioner[SSHSpec, SSHResult]):
    @property
    @override
    def name(self) -> str:
        return "docker-ssh"

    @override
    async def setup(self, spec: SSHSpec) -> SSHResult:
        return await self._write_config(spec)

    async def _write_config(self, spec: SSHSpec) -> SSHResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._write_config_func, spec)

    def _write_config_func(self, spec: SSHSpec) -> SSHResult:
        sshkey = spec.ssh_keypair
        if sshkey is None:
            return SSHResult(None, None, None)

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

        chowner = Chowner(spec)
        if do_override:
            chowner.chown_paths_if_root([priv_key_path, pub_key_path], ouid, ogid)
        else:
            if KernelFeatures.UID_MATCH in spec.agent_kernel_features:
                chowner.chown_paths_if_root(
                    [priv_key_path, pub_key_path], spec.agent_kernel_uid, spec.agent_kernel_gid
                )

        priv_key_path.chmod(0o600)
        if cluster_ssh_port_mapping := spec.cluster_ssh_port_mapping:
            port_mapping_json_path = spec.config_dir / "ssh" / "port-mapping.json"
            port_mapping_json_path.write_bytes(dump_json(cluster_ssh_port_mapping))
        else:
            port_mapping_json_path = None
        return SSHResult(
            pub_key_path=pub_key_path,
            priv_key_path=priv_key_path,
            port_mapping_json_path=port_mapping_json_path,
        )

    @override
    async def teardown(self, resource: SSHResult) -> None:
        pass


class SSHStage(ProvisionStage[SSHSpec, SSHResult]):
    pass
