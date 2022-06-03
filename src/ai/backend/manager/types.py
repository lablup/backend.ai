from __future__ import annotations

import attr
import enum
import uuid
from typing import (
    Protocol,
    TYPE_CHECKING,
)

from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.engine.row import Row

if TYPE_CHECKING:
    from ai.backend.common.lock import AbstractDistributedLock
    from .defs import LockID


class SessionGetter(Protocol):

    def __call__(self, *, db_connection: SAConnection) -> Row:
        ...


# Sentinel is a special object that indicates a special status instead of a value
# where the user expects a value.
# According to the discussion in https://github.com/python/typing/issues/236,
# we define our Sentinel type as an enum with only one special value.
# This enables passing of type checks by "value is sentinel" (or "value is Sentinel.token")
# instead of more expensive "isinstance(value, Sentinel)" because we can assure type checkers
# to think there is no other possible instances of the Sentinel type.

class Sentinel(enum.Enum):
    token = 0


@attr.define(slots=True)
class UserScope:
    domain_name: str
    group_id: uuid.UUID
    user_uuid: uuid.UUID
    user_role: str


class DistributedLockFactory(Protocol):

    def __call__(self, lock_id: LockID, lifetime_hint: float) -> AbstractDistributedLock:
        ...
