from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING, Annotated, Any, Generic, Optional, Protocol, Self, TypeVar

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


SENTINEL = Sentinel.token


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

type TriStateValue = Optional[TVal] | Sentinel


class TriState(Generic[TVal]):
    _attr_name: str
    _value: TriStateValue

    def __init__(
        self,
        attr_name: str,
        value: TriStateValue = SENTINEL,
    ) -> None:
        self._attr_name = attr_name
        self._value = value

    @classmethod
    def set(cls, attr_name: str, value: Optional[TVal]) -> Self:
        return cls(attr_name, value=value)

    @classmethod
    def unset(cls, attr_name: str) -> Self:
        return cls(attr_name, value=None)

    @classmethod
    def nop(cls, attr_name: str) -> Self:
        return cls(attr_name)

    def has_value(self) -> bool:
        return self._value is not SENTINEL

    def set_attr(self, obj: Any) -> None:
        if self._value is not SENTINEL:
            setattr(obj, self._attr_name, self._value)


class NonNullState(TriState[TVal]):
    _attr_name: str
    _value: TVal

    def __init__(self, attr_name: str, value: TVal | Sentinel) -> None:
        self._attr_name = attr_name
        self._value = value

    @classmethod
    def set(cls, attr_name: str, value: TVal) -> Self:
        return cls(attr_name, value=value)

    @classmethod
    def none(cls, attr_name: str) -> Self:
        return cls(attr_name, value=SENTINEL)
