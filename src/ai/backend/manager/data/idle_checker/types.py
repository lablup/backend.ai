from __future__ import annotations

import enum


class CheckerType(enum.StrEnum):
    """Discriminator for the kind of idle checker; selects the concrete spec."""

    SESSION_LIFETIME = "session_lifetime"
    NETWORK_TIMEOUT = "network_timeout"
    UTILIZATION = "utilization"
