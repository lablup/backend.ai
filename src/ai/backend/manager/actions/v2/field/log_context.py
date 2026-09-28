from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from ai.backend.common.data.entity.action import ActionID
from ai.backend.logging.structured import LogValue
from ai.backend.manager.actions.v2.field.base import (
    BaseRuntimeSingleFieldAction,
    BaseSingleFieldAction,
)
from ai.backend.manager.actions.v2.field.bulk_base import BaseBulkFieldAction
from ai.backend.manager.actions.v2.log_context import with_action_log_context

__all__ = ("with_single_field_action_context", "with_bulk_field_action_context")


@contextmanager
def with_single_field_action_context(
    action: BaseSingleFieldAction[Any, Any] | BaseRuntimeSingleFieldAction[Any],
) -> Iterator[ActionID]:
    field_id = action.to_owner_lookup_action().field_id()
    with with_action_log_context(
        action.action_name(), field_type=field_id.field_type(), field_id=field_id
    ) as action_id:
        yield action_id


@contextmanager
def with_bulk_field_action_context(action: BaseBulkFieldAction[Any, Any]) -> Iterator[ActionID]:
    field_ids = action.field_ids()
    field_types = {field_id.field_type() for field_id in field_ids}
    fields: dict[str, LogValue] = {"field_count": len(field_ids)}
    if len(field_types) == 1:
        fields["field_type"] = field_types.pop()
    with with_action_log_context(action.action_name(), **fields) as action_id:
        yield action_id
