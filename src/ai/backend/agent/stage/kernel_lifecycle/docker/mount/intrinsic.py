import asyncio
import secrets
import sys
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import override

from aiodocker.docker import Docker

from ai.backend.agent.proxy import DomainSocketProxy, proxy_connection
from ai.backend.agent.resources import Mount
from ai.backend.agent.types import VolumeInfo
from ai.backend.agent.utils import closing_async
from ai.backend.common.docker import ImageRef
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import (
    MountPermission,
    MountTypes,
)


@dataclass
class CoreDumpConfig:
    enabled: bool
    path: Path
    core_path: Path


@dataclass
class IntrinsicMountSpec:
    config_dir: Path
    work_dir: Path
    tmp_dir: Path
    scratch_type: str

    agent_sockpath: Path
    image_ref: ImageRef
    coredump: CoreDumpConfig
    ipc_base_path: Path
    domain_socket_proxies: list[DomainSocketProxy]


class IntrinsicMountSpecGenerator(ArgsSpecGenerator[IntrinsicMountSpec]):
    pass


@dataclass
class IntrinsicMountResult:
    mounts: list[Mount]
    domain_socket_proxies: list[DomainSocketProxy]


class IntrinsicMountProvisioner(Provisioner[IntrinsicMountSpec, IntrinsicMountResult]):
    """
    Provisioner for the kernel creation setup stage.
    This is a no-op provisioner as it does not create any resources.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-intrinsic-mount"

    @override
    async def setup(self, spec: IntrinsicMountSpec) -> IntrinsicMountResult:
        scratch_mounts = await self._prepare_scratch_mounts(spec)
        timezone_mounts = await self._prepare_timezone_mounts(spec)
        lxcfs_mounts = await self._prepare_lxcfs_mounts(spec)
        coredump_mounts = await self._prepare_coredump_mounts(spec)
        agent_socket_mounts = await self._prepare_agent_socket_mounts(spec)
        domain_socket_proxies, domain_socket_mounts = await self._prepare_domain_socket_proxies(
            spec
        )
        mounts = [
            *scratch_mounts,
            *timezone_mounts,
            *lxcfs_mounts,
            *coredump_mounts,
            *agent_socket_mounts,
            *domain_socket_mounts,
        ]
        return IntrinsicMountResult(
            mounts=mounts,
            domain_socket_proxies=domain_socket_proxies,
        )

    async def _prepare_scratch_mounts(self, spec: IntrinsicMountSpec) -> list[Mount]:
        # scratch/config/tmp mounts
        mounts: list[Mount] = [
            Mount(
                MountTypes.BIND, spec.config_dir, Path("/home/config"), MountPermission.READ_ONLY
            ),
            Mount(MountTypes.BIND, spec.work_dir, Path("/home/work"), MountPermission.READ_WRITE),
        ]
        if sys.platform.startswith("linux") and spec.scratch_type == "memory":
            mounts.append(
                Mount(
                    MountTypes.BIND,
                    spec.tmp_dir,
                    Path("/tmp"),
                    MountPermission.READ_WRITE,
                )
            )
        return mounts

    async def _prepare_timezone_mounts(self, spec: IntrinsicMountSpec) -> list[Mount]:
        # /etc/localtime and /etc/timezone mounts
        mounts: list[Mount] = []
        if sys.platform.startswith("linux"):
            localtime_file = Path("/etc/localtime")
            timezone_file = Path("/etc/timezone")
            if localtime_file.exists():
                mounts.append(
                    Mount(
                        type=MountTypes.BIND,
                        source=localtime_file,
                        target=localtime_file,
                        permission=MountPermission.READ_ONLY,
                    )
                )
            if timezone_file.exists():
                mounts.append(
                    Mount(
                        type=MountTypes.BIND,
                        source=timezone_file,
                        target=timezone_file,
                        permission=MountPermission.READ_ONLY,
                    )
                )
        return mounts

    async def _prepare_lxcfs_mounts(self, spec: IntrinsicMountSpec) -> list[Mount]:
        # lxcfs mounts
        mounts: list[Mount] = []
        lxcfs_root = Path("/var/lib/lxcfs")
        if lxcfs_root.is_dir():
            mounts.extend(
                Mount(
                    MountTypes.BIND,
                    lxcfs_proc_path,
                    "/" / lxcfs_proc_path.relative_to(lxcfs_root),
                    MountPermission.READ_WRITE,
                )
                for lxcfs_proc_path in (lxcfs_root / "proc").iterdir()
                if lxcfs_proc_path.stat().st_size > 0
            )
            mounts.extend(
                Mount(
                    MountTypes.BIND,
                    lxcfs_root / path,
                    "/" / Path(path),
                    MountPermission.READ_WRITE,
                )
                for path in [
                    "sys/devices/system/cpu",
                    "sys/devices/system/cpu/online",
                ]
                if Path(lxcfs_root / path).exists()
            )
        return mounts

    async def _prepare_coredump_mounts(self, spec: IntrinsicMountSpec) -> list[Mount]:
        """Prepare mounts for coredump if enabled."""
        # debug mounts
        mounts: list[Mount] = []
        if spec.coredump.enabled:
            mounts.append(
                Mount(
                    MountTypes.BIND,
                    spec.coredump.path,
                    spec.coredump.core_path,
                    MountPermission.READ_WRITE,
                )
            )
        return mounts

    async def _prepare_agent_socket_mounts(self, spec: IntrinsicMountSpec) -> list[Mount]:
        # agent-socket mount
        mounts: list[Mount] = []
        if sys.platform != "darwin":
            mounts.append(
                Mount(
                    MountTypes.BIND,
                    spec.agent_sockpath,
                    Path("/opt/kernel/agent.sock"),
                    MountPermission.READ_WRITE,
                )
            )
        return mounts

    async def _prepare_domain_socket_proxies(
        self, spec: IntrinsicMountSpec
    ) -> tuple[list[DomainSocketProxy], list[Mount]]:
        loop = asyncio.get_running_loop()
        ipc_base_path = spec.ipc_base_path
        domain_socket_proxies = []
        mounts = []

        # domain-socket proxy mount
        # (used for special service containers such image importer)
        if spec.domain_socket_proxies:
            await loop.run_in_executor(
                None, partial((ipc_base_path / "proxy").mkdir, parents=True, exist_ok=True)
            )
        for proxy in spec.domain_socket_proxies:
            host_proxy_path = ipc_base_path / "proxy" / f"{secrets.token_hex(12)}.sock"
            proxy_server = await asyncio.start_unix_server(
                partial(proxy_connection, proxy.host_sock_path), str(host_proxy_path)
            )
            await loop.run_in_executor(None, host_proxy_path.chmod, 0o666)
            domain_socket_proxies.append(
                DomainSocketProxy(
                    Path(proxy.host_sock_path),
                    host_proxy_path,
                    proxy_server,
                )
            )
            mounts.append(
                Mount(
                    MountTypes.BIND,
                    host_proxy_path,
                    proxy.host_sock_path,
                    MountPermission.READ_WRITE,
                )
            )
        return domain_socket_proxies, mounts

    async def _prepare_deeplearning_sample_mounts(self, spec: IntrinsicMountSpec) -> list[Mount]:
        """
        NOTE: !! This is deprecated and should not be used in new code !!
        Prepare mounts for deeplearning sample data if needed.
        """
        deeplearning_image_keys = {
            "tensorflow",
            "caffe",
            "keras",
            "torch",
            "mxnet",
            "theano",
        }

        deeplearning_sample_volume = VolumeInfo(
            "deeplearning-samples",
            "/home/work/samples",
            "ro",
        )
        short_image_ref = spec.image_ref.short
        async with closing_async(Docker()) as docker:
            avail_volumes = (await docker.volumes.list())["Volumes"]
            if not avail_volumes:
                return []
            avail_volume_names = set(v["Name"] for v in avail_volumes)

            # deeplearning specialization
            # TODO: extract as config
            volume_list: list[VolumeInfo] = []
            for k in deeplearning_image_keys:
                if k in short_image_ref:
                    volume_list.append(deeplearning_sample_volume)
                    break

            # Mount only actually existing volumes
            volume_mount_list: list[VolumeInfo] = []
            for vol in volume_list:
                if vol.name in avail_volume_names:
                    volume_mount_list.append(vol)
            return [
                Mount(
                    MountTypes.VOLUME, Path(v.name), Path(v.container_path), MountPermission(v.mode)
                )
                for v in volume_mount_list
            ]

    @override
    async def teardown(self, resource: IntrinsicMountResult) -> None:
        pass


class IntrinsicMountStage(ProvisionStage[IntrinsicMountSpec, IntrinsicMountResult]):
    pass
