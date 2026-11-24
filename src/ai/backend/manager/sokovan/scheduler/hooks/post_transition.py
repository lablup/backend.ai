"""Hooks that run after a session status transition is committed.

Unlike ``StatusTransitionHook``, a post-transition hook cannot affect the
transition: it runs after the commit, and its failure is only logged.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Collection, Sequence

from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.views.sokovan.session import SessionStatusTransition

log = StructuredLogger(logging.getLogger(__name__))


class PostTransitionHook(ABC):
    """Base class for hooks called after session status transitions are committed."""

    @abstractmethod
    async def on_transitioned(self, transitions: Sequence[SessionStatusTransition]) -> None:
        """Handle committed status changes that share one ``to_status``.

        Args:
            transitions: Changes whose status actually changed (never empty)
        """
        raise NotImplementedError


class PostTransitionHookRegistry:
    """Registry of post-transition hooks, for specific statuses or for all statuses.

    One registry is shared by every component that commits session status
    transitions, so a registered hook sees each committed transition once.
    """

    _all_status_hooks: list[PostTransitionHook]
    _status_hooks: dict[SessionStatus, list[PostTransitionHook]]

    def __init__(self) -> None:
        self._all_status_hooks = []
        self._status_hooks = {}

    def register(
        self,
        hook: PostTransitionHook,
        statuses: Collection[SessionStatus],
    ) -> None:
        """Register a hook for transitions to the given target statuses."""
        for status in statuses:
            self._status_hooks.setdefault(status, []).append(hook)

    def register_for_all_transitions(self, hook: PostTransitionHook) -> None:
        """Register a hook for transitions to every status."""
        self._all_status_hooks.append(hook)

    def get_hooks(self, status: SessionStatus) -> list[PostTransitionHook]:
        """Return the hooks that run for transitions to ``status``."""
        return [*self._status_hooks.get(status, []), *self._all_status_hooks]

    async def notify(self, transitions: Sequence[SessionStatusTransition]) -> None:
        """Run the hooks for committed status changes.

        Changes whose status did not change are dropped. The rest are grouped by
        ``to_status``, and each group runs its hooks concurrently. A hook failure is
        logged and does not affect the other hooks or the caller.

        Args:
            transitions: The status changes a commit wrote
        """
        by_status: dict[SessionStatus, list[SessionStatusTransition]] = {}
        for transition in transitions:
            if transition.from_status == transition.to_status:
                continue
            by_status.setdefault(transition.to_status, []).append(transition)
        for to_status, group in by_status.items():
            hooks = self.get_hooks(to_status)
            if hooks:
                await asyncio.gather(*(self._run_hook(hook, to_status, group) for hook in hooks))

    async def _run_hook(
        self,
        hook: PostTransitionHook,
        to_status: SessionStatus,
        transitions: Sequence[SessionStatusTransition],
    ) -> None:
        try:
            await hook.on_transitioned(transitions)
        except Exception:
            log.exception(
                "post-transition hook failed",
                hook_name=hook.__class__.__name__,
                to_status=to_status,
                session_count=len(transitions),
            )
