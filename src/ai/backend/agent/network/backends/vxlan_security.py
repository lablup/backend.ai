from __future__ import annotations

import enum
from collections.abc import Mapping
from typing import Final


class VxlanSecurityState(enum.StrEnum):
    """Security lifecycle of a VXLAN session."""

    PLAINTEXT = "plaintext"
    READY = "ready"
    VERIFYING = "verifying"
    BLOCKING = "blocking"
    BLOCKED = "blocked"
    RESTORING = "restoring"


class VxlanSecurityEvent(enum.StrEnum):
    """Events accepted by the VXLAN security state machine."""

    RECONCILE_STARTED = "reconcile-started"
    PROTECTION_READY = "protection-ready"
    PROTECTION_FAILED = "protection-failed"
    TUNNEL_BLOCKED = "tunnel-blocked"


_SECURITY_TRANSITIONS: Final[
    Mapping[
        tuple[VxlanSecurityState, VxlanSecurityEvent],
        VxlanSecurityState,
    ]
] = {
    (VxlanSecurityState.PLAINTEXT, VxlanSecurityEvent.RECONCILE_STARTED): (
        VxlanSecurityState.PLAINTEXT
    ),
    (VxlanSecurityState.PLAINTEXT, VxlanSecurityEvent.PROTECTION_READY): (
        VxlanSecurityState.PLAINTEXT
    ),
    (VxlanSecurityState.PLAINTEXT, VxlanSecurityEvent.PROTECTION_FAILED): (
        VxlanSecurityState.PLAINTEXT
    ),
    (VxlanSecurityState.READY, VxlanSecurityEvent.RECONCILE_STARTED): (
        VxlanSecurityState.VERIFYING
    ),
    (VxlanSecurityState.READY, VxlanSecurityEvent.PROTECTION_READY): (VxlanSecurityState.READY),
    (VxlanSecurityState.READY, VxlanSecurityEvent.PROTECTION_FAILED): (VxlanSecurityState.BLOCKING),
    (VxlanSecurityState.VERIFYING, VxlanSecurityEvent.RECONCILE_STARTED): (
        VxlanSecurityState.VERIFYING
    ),
    (VxlanSecurityState.VERIFYING, VxlanSecurityEvent.PROTECTION_READY): (VxlanSecurityState.READY),
    (VxlanSecurityState.VERIFYING, VxlanSecurityEvent.PROTECTION_FAILED): (
        VxlanSecurityState.BLOCKING
    ),
    (VxlanSecurityState.BLOCKING, VxlanSecurityEvent.RECONCILE_STARTED): (
        VxlanSecurityState.BLOCKING
    ),
    (VxlanSecurityState.BLOCKING, VxlanSecurityEvent.PROTECTION_READY): (
        VxlanSecurityState.BLOCKING
    ),
    (VxlanSecurityState.BLOCKING, VxlanSecurityEvent.PROTECTION_FAILED): (
        VxlanSecurityState.BLOCKING
    ),
    (VxlanSecurityState.BLOCKING, VxlanSecurityEvent.TUNNEL_BLOCKED): (VxlanSecurityState.BLOCKED),
    (VxlanSecurityState.BLOCKED, VxlanSecurityEvent.RECONCILE_STARTED): (
        VxlanSecurityState.RESTORING
    ),
    (VxlanSecurityState.BLOCKED, VxlanSecurityEvent.PROTECTION_READY): (VxlanSecurityState.BLOCKED),
    (VxlanSecurityState.BLOCKED, VxlanSecurityEvent.PROTECTION_FAILED): (
        VxlanSecurityState.BLOCKED
    ),
    (VxlanSecurityState.RESTORING, VxlanSecurityEvent.RECONCILE_STARTED): (
        VxlanSecurityState.RESTORING
    ),
    (VxlanSecurityState.RESTORING, VxlanSecurityEvent.PROTECTION_READY): (VxlanSecurityState.READY),
    (VxlanSecurityState.RESTORING, VxlanSecurityEvent.PROTECTION_FAILED): (
        VxlanSecurityState.BLOCKED
    ),
}


class VxlanSecurityStateMachine:
    state: VxlanSecurityState
    failure_reason: str | None

    def __init__(self, initial_state: VxlanSecurityState) -> None:
        self.state = initial_state
        self.failure_reason = None

    @property
    def holds_tunnel_down(self) -> bool:
        """Whether a successful link-down operation established this state."""
        return self.state in {
            VxlanSecurityState.BLOCKED,
            VxlanSecurityState.RESTORING,
        }

    def transition(
        self,
        event: VxlanSecurityEvent,
        *,
        reason: str | None = None,
    ) -> VxlanSecurityState:
        self.state = _SECURITY_TRANSITIONS[(self.state, event)]
        if self.state in {
            VxlanSecurityState.BLOCKING,
            VxlanSecurityState.BLOCKED,
        }:
            self.failure_reason = reason or self.failure_reason
        elif self.state in {
            VxlanSecurityState.PLAINTEXT,
            VxlanSecurityState.READY,
        }:
            self.failure_reason = None
        return self.state
