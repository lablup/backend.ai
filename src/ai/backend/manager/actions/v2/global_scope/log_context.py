from collections.abc import Iterator
from contextlib import contextmanager

from ai.backend.common.data.entity.action import ActionID
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.log_context import with_action_log_context

__all__ = ("with_global_action_context",)


@contextmanager
def with_global_action_context(action: BaseGlobalAction) -> Iterator[ActionID]:
    with with_action_log_context(
        action.action_name(), entity_type=action.entity_type()
    ) as action_id:
        yield action_id
