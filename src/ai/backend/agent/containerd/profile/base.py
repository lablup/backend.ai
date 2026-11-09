"""The runtime profile seam: how a kernel container is run."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from ai.backend.agent.containerd.rpc.types import RuntimeOptions
from ai.backend.common.types import KernelCreationConfig


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

    def plan(self, kernel_config: KernelCreationConfig) -> LaunchPlan: ...
