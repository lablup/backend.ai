"""Isolation providers: what a shared allocation adds to the container (suggestion-1122 4.6, L6)."""

from __future__ import annotations

import asyncio
import enum
import math
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Final, override

from ai.backend.agent.resources import AbstractComputePlugin
from ai.backend.common.arch import DEFAULT_IMAGE_ARCH
from ai.backend.common.types import DeviceId, SlotName
from ai.backend.dra.bridge import SHARE_SCALE, ContainerEdits, Mount
from ai.backend.dra.errors import IsolationUnavailableError

_HAMI_LIB: Final = "/usr/local/vgpu/libvgpu.so"
# HAMi-core reads this file (`ENV_OVERRIDE_FILE`) and `setenv`s every `KEY=VALUE` line over the
# environment.
HAMI_OVERRIDE_ENV: Final = "/overrideEnv"
HAMI_OVERRIDE_FILE: Final = "hami-core.env"
_HOOK_DIR: Final = "/usr/local/bai-hook"
PRELOAD_FILE: Final = "ld.so.preload"
# The keys the fGPU hook reads from `/home/config/resource.txt`, else from `BACKEND_<key>`.
BAI_HOOK_ENV_PREFIX: Final = "BACKEND_"
BAI_HOOK_REQUIRED_KEYS: Final = (
    "CUDA_RESOURCE_VIRTUALIZED",
    "CUDA_MEMORY_LIMITS",
    "CUDA_PROCESSOR_LIMITS",
)
BAI_HOOK_DEFAULT_DISTRO: Final = "ubuntu22.04"
MIN_SMP_COUNT: Final = 4  # the Docker path's minimum SM count of a share (mock and CUDA plugins)


class IsolationKind(enum.StrEnum):
    HAMI_CORE = "hami-core"
    BAI_HOOK = "bai-hook"
    NONE = "none"


@dataclass(frozen=True)
class DeviceLimit:
    """One device of a claim; `index` is its CUDA device index in the container."""

    index: int
    memory_bytes: int
    sm_percent: int


def limit_from_shares(
    index: int, shares: int, unit_mem: int, unit_proc: int, device_sms: int
) -> DeviceLimit:
    """`shares` in 0.01-share units; the same conversion as the plugin's `_share_to_spec()`."""
    memory_bytes = shares * unit_mem // SHARE_SCALE
    sm_count = max(shares * unit_proc // SHARE_SCALE, MIN_SMP_COUNT)
    sm_percent = 100 if device_sms <= 0 else min(100, math.ceil(sm_count * 100 / device_sms))
    return DeviceLimit(index=index, memory_bytes=memory_bytes, sm_percent=sm_percent)


@dataclass(frozen=True)
class SharedAllocation:
    """One claim's shared devices, as the plugin and the providers see it."""

    claim_uid: str
    claim_dir: Path  # on the node, removed on unprepare
    limits: Sequence[DeviceLimit]  # in the container's device order
    alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]  # `<key>.shares` → device → shares


class IsolationProvider(ABC):
    kind: IsolationKind

    @abstractmethod
    async def edits(
        self, allocation: SharedAllocation, plugin: AbstractComputePlugin
    ) -> ContainerEdits:
        raise NotImplementedError


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content)
    tmp.chmod(0o444)
    tmp.replace(path)


class HamiCore(IsolationProvider):
    """HAMi-core (`libvgpu.so` in a read-only `/etc/ld.so.preload`) caps memory and SMs.
    The limits also go to a read-only `/overrideEnv`, which HAMi-core sets over the environment
    when it initializes NVML (after it has read the limits of its shared region from the env)."""

    kind = IsolationKind.HAMI_CORE
    lib_dir: Path  # on the node: libvgpu.so and ld.so.preload

    def __init__(self, lib_dir: Path) -> None:
        self.lib_dir = lib_dir

    @override
    async def edits(
        self, allocation: SharedAllocation, plugin: AbstractComputePlugin
    ) -> ContainerEdits:
        # HAMi-core segfaults when the cache's directory is missing; /tmp always exists.
        env = [f"CUDA_DEVICE_MEMORY_SHARED_CACHE=/tmp/hami-{allocation.claim_uid}.cache"]
        for limit in allocation.limits:
            env.append(f"CUDA_DEVICE_MEMORY_LIMIT_{limit.index}={limit.memory_bytes}")
            env.append(f"CUDA_DEVICE_SM_LIMIT_{limit.index}={limit.sm_percent}")
        override_file = allocation.claim_dir / HAMI_OVERRIDE_FILE
        await asyncio.to_thread(_write_file, override_file, "".join(f"{e}\n" for e in env))
        return ContainerEdits(
            env=env,
            mounts=[
                Mount(
                    host_path=str(self.lib_dir / "libvgpu.so"),
                    container_path=_HAMI_LIB,
                    options=["bind", "ro"],
                ),
                Mount(
                    host_path=str(self.lib_dir / "ld.so.preload"),
                    container_path="/etc/ld.so.preload",
                    options=["bind", "ro"],
                ),
                Mount(
                    host_path=str(override_file),
                    container_path=HAMI_OVERRIDE_ENV,
                    options=["bind", "ro"],
                ),
            ],
        )


def shares_value(alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]) -> str:
    """`<SLOT>_SHARES` of the Agent's resource.txt: `device:shares,...` of the share slots."""
    return ",".join(
        f"{device_id}:{amount}"
        for slot, per_device in alloc.items()
        if str(slot).endswith(".shares")
        for device_id, amount in per_device.items()
    )


class BaiHook(IsolationProvider):
    """The Backend.AI fGPU hook of the enterprise CUDA plugin, preloaded read-only.
    The limits are `BACKEND_<key>` env keyed by GPU UUID: cooperative until the hook reads a
    fixed file path."""

    kind = IsolationKind.BAI_HOOK
    distro: str
    arch: str

    def __init__(
        self, distro: str = BAI_HOOK_DEFAULT_DISTRO, arch: str = DEFAULT_IMAGE_ARCH
    ) -> None:
        self.distro = distro
        self.arch = arch

    @override
    async def edits(
        self, allocation: SharedAllocation, plugin: AbstractComputePlugin
    ) -> ContainerEdits:
        hooks = [Path(p) for p in await plugin.get_hooks(self.distro, self.arch)]
        if not hooks:
            raise IsolationUnavailableError(f"{plugin.key} provides no hook library")
        data = dict(await plugin.generate_resource_data(allocation.alloc))
        missing = [k for k in BAI_HOOK_REQUIRED_KEYS if not data.get(k)]
        if missing or data["CUDA_RESOURCE_VIRTUALIZED"] != "1":
            # A plugin outside its fractional mode leaves the device unlimited.
            raise IsolationUnavailableError(
                f"{plugin.key} gives no fGPU limits (missing {missing}); fractional mode?"
            )
        data[f"{str(plugin.key).upper()}.SHARES_SHARES"] = shares_value(allocation.alloc)
        container_hooks = [f"{_HOOK_DIR}/{hook.name}" for hook in hooks]
        preload = allocation.claim_dir / PRELOAD_FILE
        await asyncio.to_thread(_write_file, preload, "".join(f"{h}\n" for h in container_hooks))
        mounts = [
            Mount(host_path=str(hook), container_path=path, options=["bind", "ro"])
            for hook, path in zip(hooks, container_hooks, strict=True)
        ]
        # Not LD_PRELOAD: the kernel Pod sets it for its own hook.
        mounts.append(
            Mount(
                host_path=str(preload), container_path="/etc/ld.so.preload", options=["bind", "ro"]
            )
        )
        return ContainerEdits(
            env=[f"{BAI_HOOK_ENV_PREFIX}{k}={v}" for k, v in sorted(data.items())],
            mounts=mounts,
        )


def isolation_provider(
    kind: IsolationKind,
    *,
    hami_lib_dir: Path | None = None,
    hook_distro: str = BAI_HOOK_DEFAULT_DISTRO,
) -> IsolationProvider | None:
    match kind:
        case IsolationKind.HAMI_CORE:
            if hami_lib_dir is None:
                raise IsolationUnavailableError("hami-core needs the node's HAMi-core directory")
            return HamiCore(hami_lib_dir)
        case IsolationKind.BAI_HOOK:
            return BaiHook(hook_distro)
        case IsolationKind.NONE:
            return None
