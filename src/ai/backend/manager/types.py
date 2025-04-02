from __future__ import annotations

import enum
import uuid
from collections import UserDict
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Generic,
    Optional,
    Protocol,
    Self,
    TypeAlias,
    TypeVar,
)

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


class UpdateState(enum.Enum):
    UPDATE = "update"
    NULLIFY = "nullify"
    NOP = "nop"


TVal = TypeVar("TVal")

TriStateValue: TypeAlias = Optional[TVal] | Sentinel


class TriState(Generic[TVal]):
    _attr_name: str
    _state: UpdateState
    _value: Optional[TVal]

    def __init__(
        self,
        attr_name: str,
        state: UpdateState,
        value: Optional[TVal],
    ) -> None:
        self._attr_name = attr_name
        self._state = state
        self._value = value

    @classmethod
    def set(cls, attr_name: str, value: TVal) -> Self:
        return cls(attr_name, state=UpdateState.UPDATE, value=value)

    @classmethod
    def unset(cls, attr_name: str) -> Self:
        return cls(attr_name, state=UpdateState.NULLIFY, value=None)

    @classmethod
    def nop(cls, attr_name: str) -> Self:
        return cls(attr_name, state=UpdateState.NOP, value=None)

    @property
    def state(self) -> UpdateState:
        return self._state

    def value(self) -> TVal | None:
        if self._state == UpdateState.UPDATE:
            return self._value
        raise ValueError(f"Value is not set for {self._attr_name}")

    def set_attr(self, obj: Any) -> None:
        match self._state:
            case UpdateState.UPDATE:
                setattr(obj, self._attr_name, self._value)
            case UpdateState.NULLIFY:
                setattr(obj, self._attr_name, None)
            case UpdateState.NOP:
                pass


class NonNullState(TriState[TVal]):
    _attr_name: str
    _state: UpdateState
    _value: TVal | None

    def __init__(
        self,
        attr_name: str,
        state: UpdateState,
        value: TVal | None,
    ) -> None:
        self._attr_name = attr_name
        self._state = state
        self._value = value

    @classmethod
    def set(cls, attr_name: str, value: TVal) -> Self:
        return cls(attr_name, state=UpdateState.UPDATE, value=value)

    @classmethod
    def none(cls, attr_name: str) -> Self:
        return cls(attr_name, state=UpdateState.NOP, value=None)


class TriStateField(Generic[TVal]):
    _value: Optional[TVal] | Sentinel

    def __init__(self, value: Optional[TVal] | Sentinel = SENTINEL) -> None:
        self._value = value

    def value(self) -> Optional[TVal]:
        if self._value is not SENTINEL:
            return self._value
        raise ValueError(f"Value is not set for {self.__class__.__name__}")

    @classmethod
    def set(cls, value: TVal) -> Self:
        return cls(value)

    @classmethod
    def unset(cls) -> Self:
        return cls(None)

    @classmethod
    def nop(cls) -> Self:
        return cls(SENTINEL)


NonNullValue: TypeAlias = TVal | Sentinel


class NonNullStateField(TriStateField[TVal]):
    _value: TVal | Sentinel

    def __init__(self, value: TVal | Sentinel = SENTINEL) -> None:
        self._value = value

    def value(self) -> TVal:
        if self._value is not SENTINEL and self._value is not None:
            return self._value
        raise ValueError(f"Value is not set for {self.__class__.__name__}")

    @classmethod
    def set(cls, value: TVal) -> Self:
        return cls(value)


class TriStateData(UserDict):
    def set_attr(self, obj: Any) -> None:
        for field_name, value in self.data.items():
            if value is not SENTINEL:
                setattr(obj, field_name, value)
