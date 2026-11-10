import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from ai.backend.common.data.entity.action import ActionID
from ai.backend.logging.structured import LogValue, with_log_context

__all__ = ("with_action_log_context",)


@contextmanager
def with_action_log_context(action_name: str, **fields: LogValue) -> Iterator[ActionID]:
    """Open the log scope of one action run and yield the id of that run."""
    action_id = uuid.uuid4()
    with with_log_context(action_id=action_id, action_name=action_name, **fields):
        yield action_id
