"""The runtime profile seam: how a kernel container is run."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from ai.backend.agent.containerd.rpc.types import RuntimeOptions
from ai.backend.common.types import KernelCreationConfig
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class TlsConnectReadiness:
    """Ready when a TLS handshake succeeds on the published service port `port_name`.

    The outer create loop (init_polling_attempt / init_polling_timeout_sec) bounds the wait,
    so `timeout_s` only takes effect below that bound."""

    port_name: str
    timeout_s: float


@dataclass(frozen=True)
class LaunchPlan:
    """How to launch a kernel. The agent uses the cgroupfs path form, so runtime options must not enable systemd cgroups."""

    runtime_handler: str  # e.g. "io.containerd.runc.v2"
    spec_patch: Mapping[str, Any] = field(default_factory=dict)  # merged over the OCI spec
    runtime_options: RuntimeOptions | None = None
    readiness: TlsConnectReadiness | None = None  # None: the started task counts as ready


class RuntimeProfile(Protocol):
    """Chooses the runtime of a kernel; pure data out, the agent performs all I/O."""

    @property
    def name(self) -> str: ...

    def plan(
        self, kernel_config: KernelCreationConfig, *, trusted_storage_path: Path | None = None
    ) -> LaunchPlan:
        """Plan the launch; trusted_storage_path is the loop device, passed only when enabled."""
        ...

    def describe_failure(self, exit_status: int | None, error_text: str) -> str | None:
        """Name why a kernel failed (exit_status is None when no task ran); None keeps the message."""
        return None

    async def summarize_attestation(
        self, host: str, port: int, timeout_s: float
    ) -> Mapping[str, Any] | None:
        """After readiness, describe the launch evidence as a small flat mapping, or None.
        Core stores it as host-reported, unverified data. Users see it, and it reaches the owner's
        callback URL and the legacy GraphQL `status_data`: hold no nonces, tokens or keys."""
        return None


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


async def summarize_profile_attestation(
    profile: RuntimeProfile, host: str, port: int, timeout_s: float
) -> Mapping[str, Any] | None:
    """Call profile.summarize_attestation(); a missing or failing hook summarizes nothing."""
    summarize = getattr(profile, "summarize_attestation", None)
    if summarize is None:
        return None
    try:
        summary: Mapping[str, Any] | None = await summarize(host, port, timeout_s)
    except Exception as e:
        log.warning(
            "runtime profile summarize_attestation failed", profile=profile.name, error=repr(e)
        )
        return None
    return summary
