from __future__ import annotations

import enum
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

from ai.backend.common.types import KernelCreationConfig, KernelId, SessionId, SlotName
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


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
    config: KernelCreationConfig  # after RuntimeProfile.prepare()
    slots: Mapping[SlotName, Decimal]  # the kernel's resource_slots, as seen by accepts()
    devices: Sequence[TranslatedDevice]
    mounts: Sequence[GeneratedMount]
    trusted_storage_path: Path | None
    base_spec: Mapping[str, Any]  # the agent's generic OCI spec, read-only


@dataclass(frozen=True)
class RuntimeOptions:
    """A typed runtime options message for Containers.Create, passed through unparsed."""

    type_url: str  # e.g. "runtimeoptions.v1.Options"
    value: bytes  # the serialized message


@dataclass(frozen=True)
class LaunchPlan:
    runtime_handler: str  # e.g. "io.containerd.runc.v2"
    rootfs_image: str  # image reference the rootfs is unpacked from
    spec_patch: Mapping[str, Any]  # merged over base_spec by the agent
    allowed_mount_kinds: frozenset[GeneratedMountKind]
    stdio: StdioMode
    readiness: KernelRunnerReadiness | TlsConnectReadiness
    runtime_options: RuntimeOptions | None = None  # runc: None


@runtime_checkable
class RuntimeProfile(Protocol):
    """Chooses how a kernel runs; pure data out, the agent performs all I/O."""

    @property
    def name(self) -> str: ...

    def accepts(self, slots: Mapping[SlotName, Decimal]) -> bool: ...

    def plan(self, kernel: KernelLaunch) -> LaunchPlan:
        """May raise ProfileSpecRejected."""
        ...

    async def prepare(self, config: KernelCreationConfig) -> KernelCreationConfig:
        """
        Do the profile's own async lookups before plan(); return the config plan() will see.
        Return a new config rather than mutating the argument. Errors propagate unchanged.
        Only the creation context and plan() see the returned config.
        """
        return config

    def describe_failure(self, exit_status: int | None, error_text: str) -> str | None:
        """
        Name why a kernel failed; the text is added to the session error message, None keeps it.
        error_text is the text core has: str() of the runtime error on a create failure, core's
        own message on a task exit. exit_status is None when no task ran.
        """
        return None

    # Provisional name. True: the image carries its own krunner, so core skips the host krunner
    # mounts and env (and the runner and libbaihook resolution they need) but keeps the
    # accelerator setup. The image distro is still resolved before the creation context.
    skips_host_krunner: bool = False


def profile_skips_host_krunner(profile: RuntimeProfile) -> bool:
    """Read profile.skips_host_krunner; a third-party profile without it keeps the host krunner."""
    return bool(getattr(profile, "skips_host_krunner", False))


async def prepare_kernel_config(
    profile: RuntimeProfile, config: KernelCreationConfig
) -> KernelCreationConfig:
    """Call profile.prepare(); a third-party profile written against the two-method seam is a no-op."""
    prepare = getattr(profile, "prepare", None)
    if prepare is None:
        return config
    prepared: KernelCreationConfig = await prepare(config)
    return prepared


def describe_profile_failure(
    profile: RuntimeProfile, exit_status: int | None, error_text: str
) -> str | None:
    """Call profile.describe_failure(); a missing or failing hook describes nothing."""
    describe = getattr(profile, "describe_failure", None)
    if describe is None:
        return None
    try:
        reason: str | None = describe(exit_status, error_text)
    except Exception:
        log.exception("runtime profile describe_failure failed", profile=profile.name)
        return None
    return reason
