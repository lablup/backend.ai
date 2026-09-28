from collections.abc import Iterator
from contextlib import contextmanager

from ai.backend.common.data.entity.action import ActionID
from ai.backend.manager.actions.v2.log_context import with_action_log_context
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction

__all__ = ("with_scope_action_context",)


@contextmanager
def with_scope_action_context(action: BaseScopeAction) -> Iterator[ActionID]:
    with with_action_log_context(
        action.action_name(),
        entity_type=action.entity_type(),
        scope_count=len(action.scope_targets()),
    ) as action_id:
        yield action_id
