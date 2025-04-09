from __future__ import annotations

import enum
import uuid
from abc import ABC, abstractmethod
from collections import UserDict
from dataclasses import dataclass, fields
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Dict,
    Generic,
    Optional,
    Protocol,
    TypeVar,
)

import attr
from graphql import Undefined, UndefinedType
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


class Creator(ABC):
    """
    Base class for all creation operations.
    Implementations should directly map fields to storage keys instead of using reflection.
    """

    @abstractmethod
    def get_creation_data(self) -> dict[str, Any]:
        """
        Returns a dictionary of data that should be stored in the database.
        This is different from to_dict() as it specifically maps fields to their storage keys.
        """
        pass


class PartialModifier(ABC):
    @abstractmethod
    def get_modified_fields(self) -> Dict[str, Any]:
        """
        Returns a dictionary of field name to value for modified fields.
        """
        pass


class TriStateEnum(enum.Enum):
    UPDATE = "update"
    NULLIFY = "nullify"
    NOP = "nop"


TVal = TypeVar("TVal")


@dataclass
class TriState(Generic[TVal]):
    """
    TriState is a class that represents partial updates to an attribute of an object.
    It is used to indicate whether an attribute should be updated, set to None, or not modified at all.
    It can be in one of three states:
    - UPDATE: The attribute should be updated with the given value.
    - NULLIFY: The attribute should be set to None.
    - NOP: No operation should be performed on the attribute.
    """

    _attr_name: str
    _state: TriStateEnum
    _value: Optional[TVal]

    def __init__(self, attr_name: str, state: TriStateEnum, value: Optional[TVal]):
        self._attr_name = attr_name
        self._state = state
        self._value = value

    @classmethod
    def from_graphql(cls, attr_name: str, value: Optional[TVal] | UndefinedType) -> TriState[TVal]:
        if value is None:
            return cls.nullify(attr_name)
        if value is Undefined:
            return cls.nop(attr_name)
        return cls.update(attr_name, value)  # type: ignore

    @classmethod
    def update(cls, attr_name: str, value: TVal) -> TriState[TVal]:
        return cls(attr_name, state=TriStateEnum.UPDATE, value=value)

    @classmethod
    def nullify(cls, attr_name: str) -> TriState[TVal]:
        return cls(attr_name, state=TriStateEnum.NULLIFY, value=None)

    @classmethod
    def nop(cls, attr_name: str) -> TriState[TVal]:
        return cls(attr_name, state=TriStateEnum.NOP, value=None)

    def value(self) -> Optional[TVal]:
        if self._state == TriStateEnum.UPDATE:
            return self._value
        raise ValueError(f"Value is not set for {self._attr_name}")

    def state(self) -> TriStateEnum:
        return self._state

    def set_attr(self, obj: Any) -> None:
        match self._state:
            case TriStateEnum.UPDATE:
                setattr(obj, self._attr_name, self._value)
            case TriStateEnum.NULLIFY:
                setattr(obj, self._attr_name, None)
            case TriStateEnum.NOP:
                pass


class OptionalState(TriState[TVal]):
    """
    OptionalState is a class that represents partial updates to an attribute of an object.
    It is used to indicate whether an attribute should be updated or not modified at all.
    It can be in one of two states:
    - UPDATE: The attribute should be updated with the given value.
    - NOP: No operation should be performed on the attribute.
    This class is similar to TriState, but it cannot be in the NULLIFY state.
    """

    def __init__(self, attr_name: str, state: TriStateEnum, value: Optional[TVal]):
        self._attr_name = attr_name
        if state == TriStateEnum.NULLIFY:
            raise ValueError("OptionalState cannot be NULLIFY")
        self._state = state
        self._value = value

    @classmethod
    def from_graphql(
        cls, attr_name: str, value: Optional[TVal] | UndefinedType
    ) -> OptionalState[TVal]:
        if value is None:
            raise ValueError("OptionalState cannot be NULLIFY")
        if value is Undefined:
            return OptionalState.nop(attr_name)
        return OptionalState.update(attr_name, value)  # type: ignore

    @classmethod
    def nullify(cls, _: str) -> TriState[TVal]:
        raise ValueError("OptionalState cannot be NULLIFY")

    @classmethod
    def update(cls, attr_name: str, value: TVal) -> OptionalState[TVal]:
        return cls(attr_name, state=TriStateEnum.UPDATE, value=value)

    @classmethod
    def nop(cls, attr_name: str) -> OptionalState[TVal]:
        return cls(attr_name, state=TriStateEnum.NOP, value=None)


@dataclass
class DataclassInput:
    """
    Base class for inputs that are dataclasses.

    The classes that inherit from this class should be dataclasses and
    should have fields that are TriStateField.
    """

    def _get_fields(self) -> list[tuple[str, TriState]]:
        return [(field_meta.name, getattr(self, field_meta.name)) for field_meta in fields(self)]

    def set_attr(self, obj: Any) -> None:
        for field_name, value in self._get_fields():
            if value.state() != TriStateEnum.NOP:
                setattr(obj, field_name, value.value())

    def to_dict(self) -> dict[str, Any]:
        return {
            field_name: value.value()
            for field_name, value in self._get_fields()
            if value.state() != TriStateEnum.NOP
        }


class DictInput(UserDict[str, TriState]):
    """
    Base class for inputs that are UserDict.
    """

    def _get_fields(self) -> list[tuple[str, TriState]]:
        return [(k, v) for k, v in self.data.items()]

    def set_attr(self, obj: Any) -> None:
        for field_name, field in self._get_fields():
            field.set_attr(obj)

    def to_dict(self) -> dict[str, Any]:
        result = {}
        for field_name, field in self._get_fields():
            if field.state() != TriStateEnum.NOP:
                result[field_name] = field.value()
        return result
