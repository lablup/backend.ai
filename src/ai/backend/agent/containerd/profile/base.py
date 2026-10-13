from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

from ai.backend.common.types import KernelCreationConfig, KernelId, SessionId, SlotName


class GeneratedMountKind(enum.StrEnum):
    KRUNNER = "krunner"
    CONFIG_DIR = "config"
    SCRATCH = "scratch"
    VFOLDER = "vfolder"
    ACCELERATOR = "accelerator"
    LOG_WRITER = "log-writer"
    BOOTSTRAP = "bootstrap"


class StdioMode(enum.StrEnum):
    LOG_FILE = "log-file"
    NULL = "null"


@dataclass(frozen=True)
class GeneratedMount:
    kind: GeneratedMountKind
    source: Path
    target: str
    read_only: bool


@dataclass(frozen=True)
class TranslatedDevice:
    path: str
    type: Literal["c", "b"]
    major: int
    minor: int
    access: str


@dataclass(frozen=True)
class KernelRunnerReadiness:
    timeout_s: float


@dataclass(frozen=True)
class TlsConnectReadiness:
    port_name: str
    timeout_s: float


@dataclass(frozen=True)
class KernelLaunch:
    kernel_id: KernelId
    session_id: SessionId
    config: KernelCreationConfig  # as received from the manager
    slots: Mapping[SlotName, Decimal]  # the kernel's resource_slots, as seen by accepts()
    devices: Sequence[TranslatedDevice]
    mounts: Sequence[GeneratedMount]
    trusted_storage_path: Path | None
    base_spec: Mapping[str, Any]  # the agent's generic OCI spec, read-only


@dataclass(frozen=True)
class LaunchPlan:
    runtime_handler: str  # e.g. "io.containerd.runc.v2"
    rootfs_image: str  # image reference the rootfs is unpacked from
    spec_patch: Mapping[str, Any]  # merged over base_spec by the agent
    allowed_mount_kinds: frozenset[GeneratedMountKind]
    stdio: StdioMode
    readiness: KernelRunnerReadiness | TlsConnectReadiness


@runtime_checkable
class RuntimeProfile(Protocol):
    """Chooses how a kernel runs; pure data out, the agent performs all I/O."""

    @property
    def name(self) -> str: ...

    def accepts(self, slots: Mapping[SlotName, Decimal]) -> bool: ...

    def plan(self, kernel: KernelLaunch) -> LaunchPlan:
        """May raise ProfileSpecRejected."""
        ...
