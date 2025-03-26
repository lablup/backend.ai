from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING, Annotated, Any, Generic, Optional, Protocol, TypeVar

import attr
from pydantic import AliasChoices, BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.types import MountPermission, MountTypes

if TYPE_CHECKING:
    from ai.backend.common.lock import AbstractDistributedLock

    from .defs import LockID
    from .models import SessionRow


class SessionGetter(Protocol):
    def __call__(self, *, db_session: SASession) -> SessionRow: ...


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
    def __call__(self, lock_id: LockID, lifetime_hint: float) -> AbstractDistributedLock: ...


class MountOptionModel(BaseModel):
    mount_destination: Annotated[
        str | None,
        Field(description="Mount destination, defaults to /home/work/{folder_name}.", default=None),
    ]
    type: Annotated[MountTypes, Field(default=MountTypes.BIND)]
    permission: Annotated[
        MountPermission | None,
        Field(validation_alias=AliasChoices("permission", "perm"), default=None),
    ]


TVal = TypeVar("TVal")


class TriStatus(Generic[TVal]):
    _attr_name: str
    _unset: bool
    _value: Optional[TVal]

    def __init__(self, attr_name: str, unset: bool, value: Optional[TVal]):
        self._attr_name = attr_name
        self._unset = unset
        self._value = value

    def set_attr(self, row: Any):
        if self._unset:
            # TODO: Is this necessary?
            assert self._value is None
            setattr(row, self._attr_name, None)
        else:
            if self._value is not None:
                setattr(row, self._attr_name, self._value)
            else:
                pass


class NoUnsetStatus(TriStatus[TVal]):
    def __init__(self, attr_name: str, value: Optional[TVal]):
        super().__init__(attr_name, False, value)
