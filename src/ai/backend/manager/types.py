from __future__ import annotations

import enum
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Generic,
    Optional,
    Protocol,
    TypeVar,
)

import attr
from graphql import UndefinedType
from pydantic import AliasChoices, BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from strawberry.types.unset import UnsetType

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
    TOKEN = 0


_SENTINEL = Sentinel.TOKEN


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
    def fields_to_store(self) -> dict[str, Any]:
        """
        Returns a dictionary of data that should be stored in the database.
        This is different from to_dict() as it specifically maps fields to their storage keys.
        """
        pass


class PartialModifier(ABC):
    @abstractmethod
    def fields_to_update(self) -> dict[str, Any]:
        """
        Returns a dictionary of fields that should be updated.
        This is different from to_dict() as it specifically maps fields to their storage keys.
        """
        pass


class _TriStateEnum(enum.Enum):
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

    _state: _TriStateEnum
    _value: Optional[TVal]

    def __init__(self, state: _TriStateEnum, value: Optional[TVal]):
        """
        Initialize a TriState object with the given state and value.
        Do not call this constructor directly. Use the class methods instead.
        """
        self._state = state
        self._value = value

    @classmethod
    def from_graphql(cls, value: Optional[TVal] | UndefinedType) -> TriState[TVal]:
        if value is None:
            return cls.nullify()
        if isinstance(value, UndefinedType) or isinstance(value, UnsetType):
            return cls.nop()
        return cls.update(value)

    @classmethod
    def update(cls, value: TVal) -> TriState[TVal]:
        return cls(state=_TriStateEnum.UPDATE, value=value)

    @classmethod
    def nullify(cls) -> TriState[TVal]:
        return cls(state=_TriStateEnum.NULLIFY, value=None)

    @classmethod
    def nop(cls) -> TriState[TVal]:
        return cls(state=_TriStateEnum.NOP, value=None)

    def value(self) -> TVal:
        """
        Returns the value of the TriState object.
        It should only be used when the state value is unambiguously UPDATE.
        """
        if self._state != _TriStateEnum.UPDATE:
            raise ValueError("Not allowed to get value when state is not UPDATE")
        if self._value is None:
            raise ValueError("TriState value is not set when state is UPDATE")
        return self._value

    def optional_value(self) -> Optional[TVal]:
        """
        Returns the value of the TriState object.
        When state is not UPDATE, it returns None.
        This is useful for cases where you want to check if the state is UPDATE
        and get the value, or if it is NULLIFY or NOP and get None.
        """
        if self._state == _TriStateEnum.UPDATE:
            return self._value
        return None

    def update_dict(self, dict: dict[str, Any], attr_name: str) -> None:
        match self._state:
            case _TriStateEnum.UPDATE:
                dict[attr_name] = self._value
            case _TriStateEnum.NULLIFY:
                dict[attr_name] = None
            case _TriStateEnum.NOP:
                pass


class OptionalState(Generic[TVal]):
    """
    OptionalState is a class that represents partial updates to an attribute of an object.
    It is used to indicate whether an attribute should be updated or not modified at all.
    It can be in one of two states:
    - UPDATE: The attribute should be updated with the given value.
    - NOP: No operation should be performed on the attribute.
    This class is similar to TriState, but it cannot be in the NULLIFY state.
    """

    _state: _TriStateEnum
    _value: Optional[TVal]

    def __init__(self, state: _TriStateEnum, value: Optional[TVal]):
        if state == _TriStateEnum.NULLIFY:
            raise ValueError("OptionalState cannot be NULLIFY")
        self._state = state
        self._value = value

    @classmethod
    def from_graphql(cls, value: Optional[TVal] | UndefinedType | UnsetType) -> OptionalState[TVal]:
        if isinstance(value, UndefinedType) or isinstance(value, UnsetType):
            return OptionalState.nop()
        if value is None:
            raise ValueError("OptionalState cannot be NULLIFY")
        return OptionalState.update(value)

    @classmethod
    def update(cls, value: TVal) -> OptionalState[TVal]:
        return cls(state=_TriStateEnum.UPDATE, value=value)

    @classmethod
    def nop(cls) -> OptionalState[TVal]:
        return cls(state=_TriStateEnum.NOP, value=None)

    def value(self) -> TVal:
        """
        Returns the value of the TriState object.
        It should only be used when the state value is unambiguously UPDATE.
        """
        if self._state != _TriStateEnum.UPDATE:
            raise ValueError("Not allowed to get value when state is not UPDATE")
        if self._value is None:
            raise ValueError("TriState value is not set when state is UPDATE")
        return self._value

    def optional_value(self) -> Optional[TVal]:
        """
        Returns the value of the TriState object.
        When state is not UPDATE, it returns None.
        This is useful for cases where you want to check if the state is UPDATE
        and get the value, or if it is NULLIFY or NOP and get None.
        """
        if self._state == _TriStateEnum.UPDATE:
            return self._value
        return None

    def update_dict(self, dict: dict[str, Any], attr_name: str) -> None:
        match self._state:
            case _TriStateEnum.UPDATE:
                dict[attr_name] = self._value
            case _TriStateEnum.NOP:
                pass


class SMTPTriggerPolicy(enum.StrEnum):
    ALL = "ALL"
    ON_ERROR = "ON_ERROR"


@dataclass
class OffsetBasedPaginationOptions:
    """Standard offset/limit pagination options."""

    offset: Optional[int] = None
    limit: Optional[int] = None


@dataclass
class ForwardPaginationOptions:
    """Forward pagination: fetch items after a given cursor."""

    after: Optional[str] = None
    first: Optional[int] = None


@dataclass
class BackwardPaginationOptions:
    """Backward pagination: fetch items before a given cursor."""

    before: Optional[str] = None
    last: Optional[int] = None


@dataclass
class PaginationOptions:
    forward: Optional[ForwardPaginationOptions] = None
    backward: Optional[BackwardPaginationOptions] = None
    offset: Optional[OffsetBasedPaginationOptions] = None
