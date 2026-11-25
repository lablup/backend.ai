"""Common fixtures for sokovan scheduler tests."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import (
    SessionStatus,
    StatusTransitions,
    TransitionStatus,
)
from ai.backend.manager.sokovan.scheduler.hooks.post_transition import PostTransitionHook

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


# =============================================================================
# Post-transition hook fixtures
# =============================================================================


@pytest.fixture
def recording_post_transition_hook() -> AsyncMock:
    """A post-transition hook that records its calls."""
    return AsyncMock(spec=PostTransitionHook)


@pytest.fixture
def failing_post_transition_hook() -> AsyncMock:
    """A post-transition hook that always raises."""
    hook = AsyncMock(spec=PostTransitionHook)
    hook.on_transitioned.side_effect = RuntimeError("post-transition hook failure")
    return hook
