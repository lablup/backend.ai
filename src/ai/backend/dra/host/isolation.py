"""Isolation providers: what a shared allocation adds to the container (suggestion-1122 4.6, L6)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ai.backend.dra.bridge import SHARE_SCALE, ContainerEdits, Mount

_HAMI_LIB: Final = "/usr/local/vgpu/libvgpu.so"
MIN_SMP_COUNT: Final = 4  # the Docker path's minimum SM count of a share (mock and CUDA plugins)


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
class HamiCore:
    """HAMi-core (`libvgpu.so` in a read-only `/etc/ld.so.preload`) caps memory and SMs."""

    # HAMi-core reads the limits only from the environment: they are cooperative against a
    # process that changes its environment and re-executes.
    lib_dir: Path  # on the node: libvgpu.so and ld.so.preload

    def edits(self, claim_uid: str, limits: Sequence[DeviceLimit]) -> ContainerEdits:
        # HAMi-core segfaults when the cache's directory is missing; /tmp always exists.
        env = [f"CUDA_DEVICE_MEMORY_SHARED_CACHE=/tmp/hami-{claim_uid}.cache"]
        for limit in limits:
            env.append(f"CUDA_DEVICE_MEMORY_LIMIT_{limit.index}={limit.memory_bytes}")
            env.append(f"CUDA_DEVICE_SM_LIMIT_{limit.index}={limit.sm_percent}")
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
            ],
        )
