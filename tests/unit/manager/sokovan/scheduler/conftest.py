"""Common fixtures for sokovan scheduler tests."""

from __future__ import annotations

import pytest

from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import (
    SessionStatus,
    StatusTransitions,
    TransitionStatus,
)

# =============================================================================
# Coordinator test fixtures
# =============================================================================


@pytest.fixture
def status_transitions_with_all_outcomes() -> StatusTransitions:
    """StatusTransitions with all outcome types defined."""
    return StatusTransitions(
        success=TransitionStatus(session=SessionStatus.SCHEDULED, kernel=KernelStatus.SCHEDULED),
        need_retry=TransitionStatus(session=SessionStatus.PENDING, kernel=KernelStatus.PENDING),
        expired=TransitionStatus(session=SessionStatus.CANCELLED, kernel=KernelStatus.CANCELLED),
        give_up=TransitionStatus(session=SessionStatus.CANCELLED, kernel=KernelStatus.CANCELLED),
    )


@pytest.fixture
def status_transitions_success_only() -> StatusTransitions:
    """StatusTransitions with only success outcome."""
    return StatusTransitions(
        success=TransitionStatus(session=SessionStatus.SCHEDULED, kernel=KernelStatus.SCHEDULED),
        need_retry=None,
        expired=None,
        give_up=None,
    )
