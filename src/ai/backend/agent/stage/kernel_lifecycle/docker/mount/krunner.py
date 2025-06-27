import sys
import asyncio
from dataclasses import dataclass
from typing import override, Any,Optional
from decimal import Decimal
from pathlib import Path
from collections.abc import Mapping
from functools import partial
import secrets
import itertools
import re

import pkg_resources
from aiodocker.docker import Docker
import aiotools

from ai.backend.agent.kernel import match_distro_data
from ai.backend.agent.utils import get_arch_name
from ai.backend.agent.proxy import DomainSocketProxy, proxy_connection
from ai.backend.agent.types import VolumeInfo
from ai.backend.agent.exception import UnsupportedResource
from ai.backend.agent.resources import known_slot_types, KernelResourceSpec,Mount, allocate
from ai.backend.common.asyncio import closing_async
from ai.backend.common.docker import ImageRef
from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator
from ai.backend.common.types import (
    ResourceSlot,
    MountTypes,
    MountPermission,
    SlotName,
    current_resource_slots,
)


@dataclass
class KernelRunnerMountSpec:
    mounts: list[KernelRunnerMount]
    internal_data: Mapping[str, Any]


class KernelRunnerMountSpecGenerator(SpecGenerator[KernelRunnerMountSpec]):
    def __init__(self, raw_mounts: list[Mapping[str, Any]]) -> None:
        self._raw_mounts = raw_mounts
    
    @override
    async def wait_for_spec(self) -> KernelRunnerMountSpec:
        """
        Waits for the spec to be ready.
        """
        vfolder_mounts= [KernelRunnerMount.from_json(item) for item in self._raw_mounts]
        return KernelRunnerMountSpec(mounts=vfolder_mounts)


@dataclass
class KernelRunnerMountResult:
    mounts: list[Mount]


class KernelRunnerMountProvisioner(Provisioner[KernelRunnerMountSpec, KernelRunnerMountResult]):
    """
    Provisioner for the kernel creation setup stage.
    This is a no-op provisioner as it does not create any resources.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-vfolder-mount"

    @override
    async def setup(self, spec: KernelRunnerMountSpec) -> KernelRunnerMountResult:
        # Inject Backend.AI kernel runner dependencies.
        distro = self.distro

        (
            arch,
            matched_distro,
            matched_libc_style,
            krunner_volume,
            krunner_pyver,
        ) = self._get_krunner_info()
        await self._prepare_static_binary(arch, distro)

        jail_path: Optional[Path] = None
        if self.local_config["container"]["sandbox-type"] == "jail":
            jail_candidates = find_artifacts(
                f"jail.*.{arch}.bin"
            )  # architecture check is already done when starting agent
            _, jail_candidate = match_distro_data(jail_candidates, distro)
            jail_path = self.resolve_krunner_filepath("runner/" + jail_candidate)

        dotfile_extractor_path = self.resolve_krunner_filepath("runner/extract_dotfiles.py")
        persistent_files_warning_doc_path = self.resolve_krunner_filepath(
            "runner/DO_NOT_STORE_PERSISTENT_FILES_HERE.md"
        )
        entrypoint_sh_path = self.resolve_krunner_filepath("runner/entrypoint.sh")

        fantompass_path = self.resolve_krunner_filepath("runner/fantompass.py")
        hash_phrase_path = self.resolve_krunner_filepath("runner/hash_phrase.py")
        words_json_path = self.resolve_krunner_filepath("runner/words.json")

        if matched_libc_style == "musl":
            terminfo_path = self.resolve_krunner_filepath("runner/terminfo.alpine3.8")
            _mount(MountTypes.BIND, terminfo_path, "/home/work/.terminfo")

        _mount(MountTypes.BIND, dotfile_extractor_path, "/opt/kernel/extract_dotfiles.py")
        _mount(MountTypes.BIND, entrypoint_sh_path, "/opt/kernel/entrypoint.sh")
        _mount(MountTypes.BIND, fantompass_path, "/opt/kernel/fantompass.py")
        _mount(MountTypes.BIND, hash_phrase_path, "/opt/kernel/hash_phrase.py")
        _mount(MountTypes.BIND, words_json_path, "/opt/kernel/words.json")
        if jail_path is not None:
            _mount(MountTypes.BIND, jail_path, "/opt/kernel/jail")
        _mount(
            MountTypes.BIND,
            persistent_files_warning_doc_path,
            "/home/work/DO_NOT_STORE_PERSISTENT_FILES_HERE.md",
        )

        _mount(MountTypes.VOLUME, krunner_volume, "/opt/backend.ai")
        pylib_path = f"/opt/backend.ai/lib/python{krunner_pyver}/site-packages/"
        kernel_pkg_path = self.resolve_krunner_filepath("kernel")
        helpers_pkg_path = self.resolve_krunner_filepath("helpers")
        _mount(MountTypes.BIND, kernel_pkg_path, pylib_path + "ai/backend/kernel")
        _mount(MountTypes.BIND, helpers_pkg_path, pylib_path + "ai/backend/helpers")
        environ["LD_PRELOAD"] = "/opt/kernel/libbaihook.so"

        # Inject ComputeDevice-specific hooks
        already_injected_hooks: set[Path] = set()

        for dev_type, device_alloc in resource_spec.allocations.items():
            computer_ctx = self.computers[dev_type]
            await self.apply_accelerator_allocation(
                computer_ctx.instance,
                device_alloc,
            )
            accelerator_mounts = await self.generate_accelerator_mounts(
                computer_ctx.instance,
                device_alloc,
            )

            for mount_info in accelerator_mounts:
                _mount(mount_info.mode, mount_info.src_path, mount_info.dst_path.as_posix())
            alloc_sum = Decimal(0)
            for dev_id, per_dev_alloc in device_alloc.items():
                alloc_sum += sum(per_dev_alloc.values())
            if alloc_sum > 0:
                hook_paths = await computer_ctx.instance.get_hooks(distro, arch)
                if hook_paths:
                    log.debug(
                        "accelerator {} provides hooks: {}",
                        type(computer_ctx.instance).__name__,
                        ", ".join(map(str, hook_paths)),
                    )
                for hook_path in map(lambda p: Path(p).absolute(), hook_paths):
                    if hook_path in already_injected_hooks:
                        continue
                    container_hook_path = f"/opt/kernel/{hook_path.name}"
                    _mount(MountTypes.BIND, hook_path, container_hook_path)
                    environ["LD_PRELOAD"] += ":" + container_hook_path
                    already_injected_hooks.add(hook_path)

    async def _prepare_static_binary(
        self, architecture: str, distro: str,
    ) -> list[Mount]:
        """
        Mounts a static binary file to the target path.
        """
        artifact_path = Path(pkg_resources.resource_filename("ai.backend.agent", "../runner"))
        def find_artifacts(pattern: str) -> Mapping[str, str]:
            artifacts = {}
            for p in artifact_path.glob(pattern):
                m = self._rx_distro.search(p.name)
                if m is not None:
                    artifacts[m.group(1)] = p.name
            return artifacts

        def mount_versioned_binary(candidate_glob: str, target_path: str) -> None:
            candidates = find_artifacts(candidate_glob)
            _, candidate = match_distro_data(candidates, distro)
            resolved_path = self.resolve_krunner_filepath("runner/" + candidate)
            self._mount(MountTypes.BIND, resolved_path, target_path)

        def mount_static_binary(filename: str, target_path: str) -> None:
            resolved_path = self.resolve_krunner_filepath("runner/" + filename)
            self._mount(MountTypes.BIND, resolved_path, target_path)

        mount_static_binary(f"su-exec.{architecture}.bin", "/opt/kernel/su-exec")
        mount_versioned_binary(f"libbaihook.*.{architecture}.so", "/opt/kernel/libbaihook.so")
        mount_static_binary(f"dropbearmulti.{architecture}.bin", "/opt/kernel/dropbearmulti")
        mount_static_binary(f"sftp-server.{architecture}.bin", "/opt/kernel/sftp-server")
        mount_static_binary(f"tmux.{architecture}.bin", "/opt/kernel/tmux")

    def _mount(
        self,
        type: MountTypes,
        src: Path | str,
        dst: Path | str,
    ) -> Mount:
        return Mount(
            type,
            Path(src),
            Path(dst),
            MountPermission.READ_ONLY,
        )

    def _get_krunner_info(self) -> tuple[str, str, str, str, str]:
        distro = self.distro
        matched_distro, krunner_volume = match_distro_data(
            self.local_config["container"]["krunner-volumes"], distro
        )
        matched_libc_style = "glibc"
        if distro.startswith("alpine"):
            matched_libc_style = "musl"
        krunner_pyver = "3.6"  # fallback
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
        return arch, matched_distro, matched_libc_style, krunner_volume, krunner_pyver


    @override
    async def teardown(self, resource: None) -> None:
        pass


class KernelRunnerMountStage(ProvisionStage[KernelRunnerMountSpec, KernelRunnerMountResult]):
    pass
