from collections.abc import Iterator
from contextlib import contextmanager

from ai.backend.common.data.entity.action import ActionID
from ai.backend.logging.structured import LogValue
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.log_context import with_action_log_context

__all__ = ("with_bulk_action_context",)


@contextmanager
def with_bulk_action_context(action: BaseBulkAction) -> Iterator[ActionID]:
    entity_ids = action.entity_ids()
    entity_types = {entity_id.entity_type() for entity_id in entity_ids}
    fields: dict[str, LogValue] = {"entity_count": len(entity_ids)}
    if len(entity_types) == 1:
        fields["entity_type"] = entity_types.pop()
    with with_action_log_context(action.action_name(), **fields) as action_id:
        yield action_id
