from collections.abc import Iterator
from contextlib import contextmanager

from ai.backend.common.data.entity.action import ActionID
from ai.backend.manager.actions.v2.log_context import with_action_log_context
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction
from ai.backend.manager.actions.v2.lookup.bulk_base import BaseBulkLookupAction

__all__ = ("with_lookup_action_context", "with_bulk_lookup_action_context")


@contextmanager
def with_lookup_action_context(action: BaseLookupAction) -> Iterator[ActionID]:
    with with_action_log_context(
        action.action_name(),
        entity_type=action.entity_type(),
        lookup_kind=action.lookup_key().kind(),
    ) as action_id:
        yield action_id


@contextmanager
def with_bulk_lookup_action_context(action: BaseBulkLookupAction) -> Iterator[ActionID]:
    with with_action_log_context(
        action.action_name(),
        entity_type=action.entity_type(),
        lookup_count=len(action.lookup_keys()),
    ) as action_id:
        yield action_id
