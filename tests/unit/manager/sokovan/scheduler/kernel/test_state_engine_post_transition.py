"""Tests for the post-transition hooks ``KernelStateEngine`` runs on session cancellation."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from ai.backend.common.types import AgentId, KernelId, SessionId
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.scheduler.hooks.post_transition import PostTransitionHookRegistry
from ai.backend.manager.sokovan.scheduler.kernel.state_engine import KernelStateEngine
from ai.backend.manager.views.sokovan.session import SessionStatusTransition


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def engine(
    repository: AsyncMock,
    recording_post_transition_hook: AsyncMock,
) -> KernelStateEngine:
    registry = PostTransitionHookRegistry()
    registry.register_for_all_transitions(recording_post_transition_hook)
    return KernelStateEngine(repository, registry)


@pytest.fixture
def session_id() -> SessionId:
    return SessionId(uuid4())


@pytest.fixture
def cancelled(session_id: SessionId) -> SessionStatusTransition:
    return SessionStatusTransition(
        session_id=session_id,
        from_status=SessionStatus.PREPARING,
        to_status=SessionStatus.CANCELLED,
    )


class TestKernelStateEnginePostTransitionHooks:
    async def test_session_cancelled_by_last_kernel_runs_hooks(
        self,
        engine: KernelStateEngine,
        repository: AsyncMock,
        recording_post_transition_hook: AsyncMock,
        session_id: SessionId,
        cancelled: SessionStatusTransition,
    ) -> None:
        repository.update_kernel_status_cancelled.return_value = True
        repository.check_and_cancel_session_if_needed.return_value = cancelled

        await engine.mark_kernel_cancelled(KernelId(uuid4()), session_id, "cancelled")

        recording_post_transition_hook.on_transitioned.assert_awaited_once_with([cancelled])

    async def test_session_not_cancelled_runs_no_hook(
        self,
        engine: KernelStateEngine,
        repository: AsyncMock,
        recording_post_transition_hook: AsyncMock,
        session_id: SessionId,
    ) -> None:
        repository.update_kernel_status_cancelled.return_value = True
        repository.check_and_cancel_session_if_needed.return_value = None

        await engine.mark_kernel_cancelled(KernelId(uuid4()), session_id, "cancelled")

        recording_post_transition_hook.on_transitioned.assert_not_awaited()

    async def test_failed_image_cancellation_runs_hooks_for_cancelled_sessions(
        self,
        engine: KernelStateEngine,
        repository: AsyncMock,
        recording_post_transition_hook: AsyncMock,
        cancelled: SessionStatusTransition,
    ) -> None:
        repository.cancel_kernels_for_failed_image.return_value = [cancelled]

        await engine.cancel_kernels_for_failed_image(AgentId("agent"), "image", "pull failed")

        recording_post_transition_hook.on_transitioned.assert_awaited_once_with([cancelled])
