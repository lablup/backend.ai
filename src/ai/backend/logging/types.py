from __future__ import annotations

import enum
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any, Generic, Self, TypedDict, TypeVar, override

import trafaret as t


class CIStrEnum(enum.StrEnum):
    """
    An StrEnum variant to allow case-insenstive matching of the members while the values are
    lowercased.
    """

    @override
    @classmethod
    def _missing_(cls, value: Any) -> Self | None:
        assert isinstance(value, str)  # since this is an StrEnum
        value = value.lower()
        # To prevent infinite recursion, we don't rely on "cls(value)" but manually search the
        # members as the official stdlib example suggests.
        for member in cls:
            if member.value.lower() == value:
                return member
        return None

    # The defualt behavior of `enum.auto()` is to set the value to the lowercased member name.

    @classmethod
    def as_trafaret(cls) -> t.Trafaret:
        return CIStrEnumTrafaret(cls)


T_enum = TypeVar("T_enum", bound=enum.Enum)


class CIStrEnumTrafaret(t.Trafaret, Generic[T_enum]):
    """
    A case-insensitive version of trafaret to parse StrEnum values.
    """

    def __init__(self, enum_cls: type[T_enum]) -> None:
        self.enum_cls = enum_cls

    def check_and_return(self, value: str) -> T_enum:
        try:
            # Assume that the enum values are lowercases.
            return self.enum_cls(value.lower())
        except (KeyError, ValueError):
            self._failure(f"value is not a valid member of {self.enum_cls.__name__}", value=value)


class LogLevel(CIStrEnum):
    # The logging stdlib only accepts uppercased loglevel names,
    # so we subclass `CIStrEnum` here.
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"
    NOTSET = "NOTSET"


class LogFormat(CIStrEnum):
    SIMPLE = "simple"
    VERBOSE = "verbose"


class SimpleBinarySizeTrafaret(t.Trafaret):
    suffix_map = {
        "y": 2**80,  # yotta
        "z": 2**70,  # zetta
        "e": 2**60,  # exa
        "p": 2**50,  # peta
        "t": 2**40,  # tera
        "g": 2**30,  # giga
        "m": 2**20,  # mega
        "k": 2**10,  # kilo
        " ": 1,
    }
    endings = ("ibytes", "ibyte", "ib", "bytes", "byte", "b")

    def check_and_return(self, value: str | int) -> int:
        orig_value = value
        if isinstance(value, int):
            return value
        value = value.strip().replace("_", "")
        try:
            return int(value)
        except ValueError:
            value = value.lower()
            dec_expr: Decimal
            try:
                for ending in self.endings:
                    if (stem := value.removesuffix(ending)) != value:
                        suffix = stem[-1]
                        dec_expr = Decimal(stem[:-1])
                        break
                else:
                    # when there is suffix without scale (e.g., "2K")
                    if not str.isnumeric(value[-1]):
                        suffix = value[-1]
                        dec_expr = Decimal(value[:-1])
                    else:
                        # has no suffix and is not an integer
                        # -> fractional bytes (e.g., 1.5 byte)
                        raise ValueError("Fractional bytes are not allowed")
            except ArithmeticError:
                raise ValueError("Unconvertible value", orig_value)
            try:
                multiplier = self.suffix_map[suffix]
            except KeyError:
                raise ValueError("Unconvertible value", orig_value)
            return int(dec_expr * multiplier)


class DirPathTrafaret(t.Trafaret):
    def __init__(
        self,
        *,
        auto_create: bool = False,
    ) -> None:
        super().__init__()
        self._auto_create = auto_create

    def check_and_return(self, value: Any) -> Path:
        try:
            p = Path(value).resolve()
        except (TypeError, ValueError):
            self._failure("cannot parse value as a path", value=value)
        else:
            if self._auto_create:
                p.mkdir(parents=True, exist_ok=True)
            if not p.is_dir():
                self._failure("value is not a directory", value=value)
            return p


class MsgpackOptions(TypedDict):
    pack_opts: Mapping[str, Any]
    unpack_opts: Mapping[str, Any]
