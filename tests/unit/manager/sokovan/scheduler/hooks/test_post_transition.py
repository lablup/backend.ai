"""Tests for ``PostTransitionHookRegistry``."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from ai.backend.common.types import SessionId
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.scheduler.hooks.post_transition import (
    PostTransitionHook,
    PostTransitionHookRegistry,
)
from ai.backend.manager.views.sokovan.session import SessionStatusTransition


@pytest.fixture
def registry() -> PostTransitionHookRegistry:
    return PostTransitionHookRegistry()


@pytest.fixture
def to_running() -> SessionStatusTransition:
    return SessionStatusTransition(
        session_id=SessionId(uuid4()),
        from_status=SessionStatus.CREATING,
        to_status=SessionStatus.RUNNING,
    )


@pytest.fixture
def to_terminated() -> SessionStatusTransition:
    return SessionStatusTransition(
        session_id=SessionId(uuid4()),
        from_status=SessionStatus.TERMINATING,
        to_status=SessionStatus.TERMINATED,
    )


@pytest.fixture
def unchanged_terminating() -> SessionStatusTransition:
    return SessionStatusTransition(
        session_id=SessionId(uuid4()),
        from_status=SessionStatus.TERMINATING,
        to_status=SessionStatus.TERMINATING,
    )


@pytest.fixture
def running_only_hook() -> AsyncMock:
    return AsyncMock(spec=PostTransitionHook)


class TestPostTransitionHookRegistry:
    async def test_all_transition_hook_called_once_per_transition(
        self,
        registry: PostTransitionHookRegistry,
        recording_post_transition_hook: AsyncMock,
        to_running: SessionStatusTransition,
        to_terminated: SessionStatusTransition,
    ) -> None:
        registry.register_for_all_transitions(recording_post_transition_hook)

        await registry.notify([to_running])
        await registry.notify([to_terminated])

        assert recording_post_transition_hook.on_transitioned.await_args_list == [
            (([to_running],),),
            (([to_terminated],),),
        ]

    async def test_transitions_grouped_by_target_status(
        self,
        registry: PostTransitionHookRegistry,
        recording_post_transition_hook: AsyncMock,
        to_running: SessionStatusTransition,
        to_terminated: SessionStatusTransition,
    ) -> None:
        registry.register_for_all_transitions(recording_post_transition_hook)

        await registry.notify([to_running, to_terminated])

        assert recording_post_transition_hook.on_transitioned.await_args_list == [
            (([to_running],),),
            (([to_terminated],),),
        ]

    async def test_unchanged_status_is_dropped(
        self,
        registry: PostTransitionHookRegistry,
        recording_post_transition_hook: AsyncMock,
        to_terminated: SessionStatusTransition,
        unchanged_terminating: SessionStatusTransition,
    ) -> None:
        registry.register_for_all_transitions(recording_post_transition_hook)

        await registry.notify([unchanged_terminating, to_terminated])

        recording_post_transition_hook.on_transitioned.assert_awaited_once_with([to_terminated])

    async def test_status_hook_called_only_for_its_status(
        self,
        registry: PostTransitionHookRegistry,
        running_only_hook: AsyncMock,
        to_running: SessionStatusTransition,
        to_terminated: SessionStatusTransition,
    ) -> None:
        registry.register(running_only_hook, statuses=[SessionStatus.RUNNING])

        await registry.notify([to_running, to_terminated])

        running_only_hook.on_transitioned.assert_awaited_once_with([to_running])

    async def test_status_and_all_transition_hooks_both_called(
        self,
        registry: PostTransitionHookRegistry,
        running_only_hook: AsyncMock,
        recording_post_transition_hook: AsyncMock,
        to_running: SessionStatusTransition,
    ) -> None:
        registry.register(running_only_hook, statuses=[SessionStatus.RUNNING])
        registry.register_for_all_transitions(recording_post_transition_hook)

        await registry.notify([to_running])

        running_only_hook.on_transitioned.assert_awaited_once_with([to_running])
        recording_post_transition_hook.on_transitioned.assert_awaited_once_with([to_running])

    async def test_no_transitions_calls_no_hook(
        self,
        registry: PostTransitionHookRegistry,
        recording_post_transition_hook: AsyncMock,
    ) -> None:
        registry.register_for_all_transitions(recording_post_transition_hook)

        await registry.notify([])

        recording_post_transition_hook.on_transitioned.assert_not_awaited()

    async def test_no_registered_hook_is_noop(
        self,
        registry: PostTransitionHookRegistry,
        to_running: SessionStatusTransition,
    ) -> None:
        await registry.notify([to_running])

        assert registry.get_hooks(SessionStatus.RUNNING) == []

    async def test_failing_hook_does_not_affect_others_or_caller(
        self,
        registry: PostTransitionHookRegistry,
        failing_post_transition_hook: AsyncMock,
        recording_post_transition_hook: AsyncMock,
        to_terminated: SessionStatusTransition,
    ) -> None:
        registry.register_for_all_transitions(failing_post_transition_hook)
        registry.register_for_all_transitions(recording_post_transition_hook)

        await registry.notify([to_terminated])

        failing_post_transition_hook.on_transitioned.assert_awaited_once()
        recording_post_transition_hook.on_transitioned.assert_awaited_once_with([to_terminated])
