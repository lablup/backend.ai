"""Isolation providers: what a shared allocation adds to the container (suggestion-1122 4, L6)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ai.backend.dra.bridge import ContainerEdits, Mount

_HAMI_LIB: Final = "/usr/local/vgpu/libvgpu.so"


@dataclass(frozen=True)
class DeviceLimit:
    """One device of a claim, in the container's device order."""

    memory_bytes: int
    shares: int  # out of SHARES_PER_DEVICE


@dataclass(frozen=True)
class HamiCore:
    """HAMi-core (`libvgpu.so`, preloaded) caps device memory and SM use per container."""

    lib_dir: Path  # on the node: libvgpu.so and ld.so.preload

    def edits(self, claim_uid: str, limits: Sequence[DeviceLimit]) -> ContainerEdits:
        # HAMi-core segfaults when the cache's directory is missing; /tmp always exists.
        env = [f"CUDA_DEVICE_MEMORY_SHARED_CACHE=/tmp/hami-{claim_uid}.cache"]
        for i, limit in enumerate(limits):
            env.append(f"CUDA_DEVICE_MEMORY_LIMIT_{i}={limit.memory_bytes // (1024 * 1024)}m")
        env.append(f"CUDA_DEVICE_SM_LIMIT={min(limit.shares for limit in limits)}")
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
