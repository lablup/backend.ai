import enum
import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Final, Optional, override

import aiofiles
import pkg_resources
from cachetools import LRUCache, cached
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from ai.backend.agent.kernel import match_distro_data
from ai.backend.agent.resources import ComputerContext, KernelResourceSpec, Mount
from ai.backend.agent.utils import get_arch_name
from ai.backend.common.json import load_json
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import (
    DeviceName,
    MountPermission,
    MountTypes,
)

DISTRO_PATTERN = re.compile(r"\.([a-z-]+\d+\.\d+)\.")
ARTIFACT_PATH = Path(pkg_resources.resource_filename("ai.backend.agent", "../runner"))


class LibcStyle(enum.StrEnum):
    GLIBC = "glibc"
    MUSL = "musl"


FALLBACK_KERNEL_PYTHON_VERSION: Final[str] = "3.6"  # Need to update?


@dataclass
class KernelRunnerInfo:
    distro: str
    architecture: str
    libc_style: LibcStyle
    krunner_volume: str
    krunner_py_version: str


@dataclass
class KernelRunnerMountSpec:
    distro: str
    krunner_volumes: Optional[Mapping[str, str]]
    sandbox_type: str  # docker, jail

    existing_computers: Mapping[DeviceName, ComputerContext]
    resource_spec: KernelResourceSpec


class KernelRunnerMountSpecGenerator(ArgsSpecGenerator[KernelRunnerMountSpec]):
    pass


class SyscallArg(BaseModel):
    index: int
    value: int
    op: str


class SyscallFilter(BaseModel):
    model_config = ConfigDict(extra="allow")

    caps: Optional[list[str]] = Field(default=None)
    arches: Optional[list[str]] = Field(default=None)


class Syscall(BaseModel):
    model_config = ConfigDict(extra="allow")

    names: list[str]
    action: str
    errno_ret: Optional[int] = Field(
        default=None, validation_alias=AliasChoices("errnoRet", "errno_ret")
    )
    args: Optional[list[SyscallArg]] = Field(default=None)
    comment: Optional[str] = Field(default=None)
    includes: Optional[SyscallFilter] = Field(default=None)
    excludes: Optional[SyscallFilter] = Field(default=None)


class ArchMap(BaseModel):
    model_config = ConfigDict(extra="allow")

    architecture: str
    sub_architectures: Optional[list[str]] = Field(
        default=None,
        validation_alias=AliasChoices("subArchitectures", "sub_architectures"),
    )


class SeccompProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    default_action: str = Field(
        validation_alias=AliasChoices("defaultAction", "default_action"),
    )
    default_errno_ret: int = Field(
        validation_alias=AliasChoices("defaultErrnoRet", "default_errno_ret"),
    )
    arch_map: list[ArchMap] = Field(
        default_factory=list,
        validation_alias=AliasChoices("archMap", "arch_map"),
    )
    syscalls: list[Syscall] = Field()


@dataclass
class KernelRunnerMountResult:
    mounts: list[Mount]
    seccomp_profile: Optional[SeccompProfile]


class KernelRunnerMountProvisioner(Provisioner[KernelRunnerMountSpec, KernelRunnerMountResult]):
    """
    Provisioner for the kernel creation setup stage.
    This is a no-op provisioner as it does not create any resources.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-krunner-mount"

    @override
    async def setup(self, spec: KernelRunnerMountSpec) -> KernelRunnerMountResult:
        info = self._get_krunner_info(spec.distro, spec.krunner_volumes)
        mounts: list[Mount] = [
            *self._prepare_default_mounts(),
            *self._prepare_static_binary_mounts(info),
            *self._prepare_libbaihook_mounts(info),
            *self._prepare_krunner_volume_mounts(info),
            *self._prepare_python_lib_mounts(info),
            *self._prepare_musl_mounts(info),
            *self._prepare_jail_mounts(info, spec.sandbox_type),
        ]
        mounts.extend(await self._prepare_hook_mounts(spec, info))

        seccomp_profile = await self._get_seccomp_profile(spec)
        return KernelRunnerMountResult(
            mounts=mounts,
            seccomp_profile=seccomp_profile,
        )

    def _resolve_krunner_filepath(self, filename: str) -> Path:
        return Path(
            pkg_resources.resource_filename(
                "ai.backend.runner",
                "../" + filename,
            )
        ).resolve()

    def _find_artifacts(self, pattern: str) -> Mapping[str, str]:
        artifacts = {}
        for p in ARTIFACT_PATH.glob(pattern):
            m = DISTRO_PATTERN.search(p.name)
            if m is not None:
                artifacts[m.group(1)] = p.name
        return artifacts

    def _parse_mount(self, source: str, target: str) -> Mount:
        return Mount(
            MountTypes.BIND,
            self._resolve_krunner_filepath(source),
            Path(target),
            MountPermission.READ_ONLY,
        )

    def _prepare_default_mounts(self) -> list[Mount]:
        return [
            self._parse_mount("runner/extract_dotfiles.py", "/opt/kernel/extract_dotfiles.py"),
            self._parse_mount("runner/entrypoint.sh", "/opt/kernel/entrypoint.sh"),
            self._parse_mount("runner/fantompass.py", "/opt/kernel/fantompass.py"),
            self._parse_mount("runner/hash_phrase.py", "/opt/kernel/hash_phrase.py"),
            self._parse_mount("runner/words.json", "/opt/kernel/words.json"),
            self._parse_mount(
                "runner/DO_NOT_STORE_PERSISTENT_FILES_HERE.md",
                "/home/work/DO_NOT_STORE_PERSISTENT_FILES_HERE.md",
            ),
        ]

    def _prepare_musl_mounts(self, runner_info: KernelRunnerInfo) -> list[Mount]:
        """
        Mounts musl-specific files to the target path.
        """
        if runner_info.libc_style != LibcStyle.MUSL:
            return []
        return [
            Mount(
                MountTypes.BIND,
                self._resolve_krunner_filepath("runner/terminfo.alpine3.8"),
                Path("/home/work/.terminfo"),
                MountPermission.READ_ONLY,
            )
        ]

    def _prepare_static_binary_mounts(self, runner_info: KernelRunnerInfo) -> list[Mount]:
        """
        Mounts static binary files to the target path.
        """
        architecture = runner_info.architecture

        return [
            self._parse_mount(f"runner/su-exec.{architecture}.bin", "/opt/kernel/su-exec"),
            self._parse_mount(
                f"runner/dropbearmulti.{architecture}.bin", "/opt/kernel/dropbearmulti"
            ),
            self._parse_mount(f"runner/sftp-server.{architecture}.bin", "/opt/kernel/sftp-server"),
            self._parse_mount(f"runner/tmux.{architecture}.bin", "/opt/kernel/tmux"),
        ]

    def _prepare_libbaihook_mounts(self, runner_info: KernelRunnerInfo) -> list[Mount]:
        architecture = runner_info.architecture
        distro = runner_info.distro
        candidates = self._find_artifacts(f"libbaihook.*.{architecture}.so")
        _, cand = match_distro_data(candidates, distro)
        resolved_path = self._resolve_krunner_filepath(f"runner/{cand}")
        return [
            Mount(
                MountTypes.BIND,
                resolved_path,
                Path("/opt/kernel/libbaihook.so"),
                MountPermission.READ_ONLY,
            )
        ]

    def _prepare_jail_mounts(self, runner_info: KernelRunnerInfo, sandbox_type: str) -> list[Mount]:
        if sandbox_type != "jail":
            return []
        architecture = runner_info.architecture
        distro = runner_info.distro
        jail_candidates = self._find_artifacts(f"jail.*.{architecture}.bin")
        _, jail_cand = match_distro_data(jail_candidates, distro)
        resolved_path = self._resolve_krunner_filepath(f"runner/{jail_cand}")
        return [
            Mount(
                MountTypes.BIND,
                resolved_path,
                Path("/opt/kernel/jail"),
                MountPermission.READ_ONLY,
            )
        ]

    def _prepare_krunner_volume_mounts(
        self,
        runner_info: KernelRunnerInfo,
    ) -> list[Mount]:
        return [
            Mount(
                MountTypes.VOLUME,
                Path(runner_info.krunner_volume),
                Path("/opt/backend.ai"),
                MountPermission.READ_ONLY,
            )
        ]

    def _prepare_python_lib_mounts(
        self,
        runner_info: KernelRunnerInfo,
    ) -> list[Mount]:
        pylib_path = f"/opt/backend.ai/lib/python{runner_info.krunner_py_version}/site-packages/"
        kernel_pkg_path = self._resolve_krunner_filepath("kernel")
        helpers_pkg_path = self._resolve_krunner_filepath("helpers")
        return [
            Mount(
                MountTypes.BIND,
                kernel_pkg_path,
                Path(pylib_path + "ai/backend/kernel"),
                MountPermission.READ_ONLY,
            ),
            Mount(
                MountTypes.BIND,
                helpers_pkg_path,
                Path(pylib_path + "ai/backend/helpers"),
                MountPermission.READ_ONLY,
            ),
        ]

    async def _prepare_hook_mounts(
        self, spec: KernelRunnerMountSpec, runner_info: KernelRunnerInfo
    ) -> list[Mount]:
        mounts: list[Mount] = []
        already_injected_hooks: set[Path] = set()
        for dev_type, device_alloc in spec.resource_spec.allocations.items():
            computer_ctx = spec.existing_computers[dev_type]
            alloc_sum = Decimal(0)
            for per_dev_alloc in device_alloc.values():
                alloc_sum += sum(per_dev_alloc.values())
            do_hook_mount = alloc_sum > 0
            if do_hook_mount:
                hook_paths = await computer_ctx.instance.get_hooks(
                    runner_info.distro, runner_info.architecture
                )
                for hook_path in hook_paths:
                    if hook_path in already_injected_hooks:
                        continue
                    container_hook_path = f"/opt/kernel/{hook_path.name}"
                    already_injected_hooks.add(hook_path)
                    mounts.append(
                        Mount(
                            MountTypes.BIND,
                            hook_path,
                            Path(container_hook_path),
                            MountPermission.READ_ONLY,
                        )
                    )
        return mounts

    def _get_additional_syscalls(self, spec: KernelRunnerMountSpec) -> list[str]:
        additional_syscalls: set[str] = set()
        for dev_type, _ in spec.resource_spec.allocations.items():
            computer_ctx = spec.existing_computers[dev_type]
            syscall = computer_ctx.instance.get_additional_allowed_syscalls()
            additional_syscalls.update(syscall)
        return sorted(additional_syscalls)

    async def _get_seccomp_profile(self, spec: KernelRunnerMountSpec) -> Optional[SeccompProfile]:
        """
        Prepares the seccomp profile based on the kernel runner information.
        """
        default_seccomp_path = self._resolve_krunner_filepath("runner/default-seccomp.json")
        if not default_seccomp_path.exists():
            return None

        async with aiofiles.open(default_seccomp_path, mode="r") as fp:
            file_data = await fp.read()
            raw_seccomp_profile = load_json(file_data)

        additional_syscalls = self._get_additional_syscalls(spec)
        seccomp_profile = SeccompProfile(**raw_seccomp_profile)
        additional_syscall = Syscall(
            names=additional_syscalls,
            action="SCMP_ACT_ALLOW",
            args=[],
            comment="Additionally allowed syscalls by Backend.AI Agent",
        )
        seccomp_profile.syscalls.append(additional_syscall)
        return seccomp_profile

    @cached(
        cache=LRUCache(maxsize=32),
        key=lambda self, distro, krunner_volumes: (distro, tuple(sorted(krunner_volumes.items()))),
    )
    def _get_krunner_info(
        self, distro: str, krunner_volumes: Optional[Mapping[str, str]]
    ) -> KernelRunnerInfo:
        krunner_volume_map = krunner_volumes or {}
        matched_distro, krunner_volume = match_distro_data(krunner_volume_map, distro)
        matched_libc_style = LibcStyle.GLIBC
        if distro.startswith("alpine"):
            matched_libc_style = LibcStyle.MUSL
        krunner_pyver = FALLBACK_KERNEL_PYTHON_VERSION
        if m := re.search(r"^([a-z-]+)(\d+(\.\d+)*)?$", matched_distro):
            matched_distro_pkgname = m.group(1).replace("-", "_")
            try:
                krunner_pyver = (
                    Path(
                        pkg_resources.resource_filename(
                            f"ai.backend.krunner.{matched_distro_pkgname}",
                            f"krunner-python.{matched_distro}.txt",
                        )
                    )
                    .read_text()
                    .strip()
                )
            except FileNotFoundError:
                pass
        arch = get_arch_name()
        return KernelRunnerInfo(
            distro=matched_distro,
            architecture=arch,
            libc_style=matched_libc_style,
            krunner_volume=krunner_volume,
            krunner_py_version=krunner_pyver,
        )

    @override
    async def teardown(self, resource: KernelRunnerMountResult) -> None:
        pass


class KernelRunnerMountStage(ProvisionStage[KernelRunnerMountSpec, KernelRunnerMountResult]):
    pass
