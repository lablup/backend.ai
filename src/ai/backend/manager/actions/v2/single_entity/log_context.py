from collections.abc import Iterator
from contextlib import contextmanager

from ai.backend.common.data.entity.action import ActionID
from ai.backend.manager.actions.v2.log_context import with_action_log_context
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction

__all__ = ("with_single_entity_action_context",)


@contextmanager
def with_single_entity_action_context(action: BaseSingleEntityAction) -> Iterator[ActionID]:
    entity_id = action.entity_id()
    with with_action_log_context(
        action.action_name(), entity_type=entity_id.entity_type(), entity_id=entity_id
    ) as action_id:
        yield action_id
