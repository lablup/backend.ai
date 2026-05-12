from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EndpointEntry:
    """Endpoint metadata visible to selection strategies.

    The pool passes only the entries it has already filtered to the healthy
    subset. Future metadata (weight, region, priority) extends this in place
    without changing strategy signatures.
    """

    endpoint: str


@dataclass(frozen=True)
class AcquiredEndpoint:
    """A single endpoint acquired from an endpoint pool.

    Carries only the endpoint URL. Per-request HTTP client sessions are
    obtained by the caller from a separate user-scoped ``ClientPool`` so
    that per-user state (cookies, access keys) stays isolated; the pool
    keeps a probe-only session internally and does not expose it.
    """

    endpoint: str


@dataclass(frozen=True)
class EndpointPoolSpec:
    """Tunables for :class:`HealthyEndpointPool`'s background probe and failure gating."""

    probe_path: str
    """HTTP path that the background probe sends ``GET`` to. Different
    services may expose liveness under different paths (e.g. ``/livez``)."""

    health_check_interval: float
    """Seconds between background probe rounds."""

    failure_threshold: int
    """Consecutive probe (or caller-reported) failures required before an
    endpoint flips from healthy to unhealthy."""

    recovery_timeout: float
    """Seconds the ``unhealthy_since`` timestamp is retained after a flip to
    unhealthy. The endpoint itself stays in the pool and is flipped back to
    healthy when the next probe succeeds; this field is informational for
    operators and reserved for future eviction policies."""

    probe_timeout: float
    """Per-endpoint HTTP probe timeout in seconds. Independent of
    ``health_check_interval``: the probe must finish within this window or it
    counts as a failure."""

    def is_failure_threshold_reached(self, failure_count: int) -> bool:
        return failure_count >= self.failure_threshold
