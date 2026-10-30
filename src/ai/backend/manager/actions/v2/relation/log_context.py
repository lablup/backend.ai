from collections.abc import Iterator
from contextlib import contextmanager

from ai.backend.common.data.entity.action import ActionID
from ai.backend.manager.actions.v2.log_context import with_action_log_context
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction

__all__ = ("with_relation_action_context",)


@contextmanager
def with_relation_action_context(action: BaseRelationAction) -> Iterator[ActionID]:
    with with_action_log_context(
        action.action_name(), scope_count=len(action.scope_targets())
    ) as action_id:
        yield action_id
