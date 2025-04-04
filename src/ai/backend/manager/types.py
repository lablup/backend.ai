from __future__ import annotations

import enum
import uuid
from collections import UserDict
from dataclasses import dataclass, fields
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Generic,
    Optional,
    Protocol,
    Self,
    TypeVar,
)

import attr
from pydantic import AliasChoices, BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.types import MountPermission, MountTypes

from .exceptions import InvalidArgument

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


_SENTINEL = Sentinel.token


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


class State(enum.Enum):
    UPDATE = "update"
    NULLIFY = "nullify"
    NOP = "nop"


TVal = TypeVar("TVal")


@dataclass
class TriState(Generic[TVal]):
    _attr_name: str
    _state: State
    _value: Optional[TVal]

    def __init__(self, attr_name: str, state: State, value: Optional[TVal]):
        self._attr_name = attr_name
        self._state = state
        self._value = value

    @classmethod
    def update(cls, attr_name: str, value: TVal) -> TriState[TVal]:
        return cls(attr_name, state=State.UPDATE, value=value)

    @classmethod
    def nullify(cls, attr_name: str) -> TriState[TVal]:
        return cls(attr_name, state=State.NULLIFY, value=None)

    @classmethod
    def nop(cls, attr_name: str) -> TriState[TVal]:
        return cls(attr_name, state=State.NOP, value=None)

    def value(self) -> Optional[TVal]:
        if self._state == State.UPDATE:
            return self._value
        raise ValueError(f"Value is not set for {self._attr_name}")

    def state(self) -> State:
        return self._state

    def set_attr(self, obj: Any) -> None:
        match self._state:
            case State.UPDATE:
                setattr(obj, self._attr_name, self._value)
            case State.NULLIFY:
                setattr(obj, self._attr_name, None)
            case State.NOP:
                pass


class OptionalState(TriState[TVal]):
    def __init__(self, attr_name: str, state: State, value: Optional[TVal]):
        self._attr_name = attr_name
        if state == State.NULLIFY:
            raise ValueError("OptionalState cannot be NULLIFY")
        self._state = state
        self._value = value

    @classmethod
    def update(cls, attr_name: str, value: TVal) -> OptionalState[TVal]:
        return cls(attr_name, state=State.UPDATE, value=value)

    @classmethod
    def nop(cls, attr_name: str) -> OptionalState[TVal]:
        return cls(attr_name, state=State.NOP, value=None)


class TriStateField(Generic[TVal]):
    _value: Optional[TVal] | Sentinel

    def __init__(self, value: Optional[TVal] | Sentinel = _SENTINEL) -> None:
        self._value = value

    def value(self) -> Optional[TVal]:
        if self._value is not _SENTINEL:
            return self._value
        raise ValueError(f"Value is not set for {self.__class__.__name__}")

    def is_valid(self) -> bool:
        return self._value is not _SENTINEL

    @classmethod
    def nop(cls) -> Self:
        return cls(_SENTINEL)


class NonNullField(Generic[TVal]):
    _value: TVal | Sentinel

    def __init__(self, value: TVal | Sentinel = _SENTINEL) -> None:
        if value is None:
            raise InvalidArgument
        self._value = value

    def value(self) -> TVal:
        if self._value is not _SENTINEL:
            return self._value
        raise ValueError(f"Value is not set for {self.__class__.__name__}")

    def is_valid(self) -> bool:
        return self._value is not _SENTINEL

    @classmethod
    def nop(cls) -> Self:
        return cls(_SENTINEL)


@dataclass
class DataclassInput:
    """
    Base class for inputs that are dataclasses.

    The classes that inherit from this class should be dataclasses and
    should have fields that are TriStateField or NonNullField.
    """

    def _get_fields(self) -> list[tuple[str, TriStateField | NonNullField]]:
        return [(field_meta.name, getattr(self, field_meta.name)) for field_meta in fields(self)]

    def set_attr(self, obj: Any) -> None:
        for field_name, value in self._get_fields():
            if value.is_valid():
                setattr(obj, field_name, value.value())

    def to_dict(self) -> dict[str, Any]:
        return {
            field_name: value.value()
            for field_name, value in self._get_fields()
            if value.is_valid()
        }


class DictInput(UserDict[str, TriStateField | NonNullField]):
    """
    Base class for inputs that are UserDict.
    """

    def _get_fields(self) -> list[tuple[str, TriStateField | NonNullField]]:
        return [(k, v) for k, v in self.data.items()]

    def set_attr(self, obj: Any) -> None:
        for field_name, value in self._get_fields():
            if value.is_valid():
                setattr(obj, field_name, value.value())

    def to_dict(self) -> dict[str, Any]:
        return {
            field_name: value.value()
            for field_name, value in self._get_fields()
            if value.is_valid()
        }
