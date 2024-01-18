import json
import re
from decimal import Decimal
from typing import Any, Generic, Mapping, Optional, Protocol, TypeVar, Union

import click
import trafaret

from .types import Undefined, undefined


class BoolExprType(click.ParamType):
    name = "boolean"

    def convert(self, value, param, ctx):
        if isinstance(value, bool):
            return value
        try:
            return trafaret.ToBool().check(value)
        except trafaret.DataError:
            self.fail(f"Cannot parser/convert {value!r} as a boolean.", param, ctx)


class ByteSizeParamType(click.ParamType):
    name = "byte"

    _rx_digits = re.compile(r"^(\d+(?:\.\d*)?)([kmgtpe]?)$", re.I)
    _scales = {
        "k": 2**10,
        "m": 2**20,
        "g": 2**30,
        "t": 2**40,
        "p": 2**50,
        "e": 2**60,
    }

    def convert(self, value, param, ctx):
        if isinstance(value, int):
            return value
        if not isinstance(value, str):
            self.fail(
                f"expected string, got {value!r} of type {type(value).__name__}",
                param,
                ctx,
            )
        m = self._rx_digits.search(value)
        if m is None:
            self.fail(f"{value!r} is not a valid byte-size expression", param, ctx)
        size = float(m.group(1))
        unit = m.group(2).lower()
        return int(size * self._scales.get(unit, 1))


class ByteSizeParamCheckType(ByteSizeParamType):
    name = "byte-check"

    def convert(self, value, param, ctx):
        if isinstance(value, int):
            return value
        if not isinstance(value, str):
            self.fail(
                f"expected string, got {value!r} of type {type(value).__name__}",
                param,
                ctx,
            )
        m = self._rx_digits.search(value)
        if m is None:
            self.fail(f"{value!r} is not a valid byte-size expression", param, ctx)
        return value


class CommaSeparatedKVListParamType(click.ParamType):
    name = "comma-seperated-KVList-check"

    def convert(self, value: Union[str, Mapping[str, str]], param, ctx) -> Mapping[str, str]:
        if isinstance(value, dict):
            return value
        if not isinstance(value, str):
            self.fail(
                f"expected string, got {value!r} of type {type(value).__name__}",
                param,
                ctx,
            )
        override_map = {}
        for assignment in value.split(","):
            try:
                k, _, v = assignment.partition("=")
                if k == "" or v == "":
                    raise ValueError(f"key or value is empty. key = {k}, value = {v}")
            except ValueError:
                self.fail(
                    f"{value!r} is not a valid mapping expression",
                    param,
                    ctx,
                )
            else:
                override_map[k] = v
        return override_map


class JSONParamType(click.ParamType):
    """
    A JSON string parameter type.
    The default value must be given as a valid JSON-parsable string,
    not the Python objects.
    """

    name = "json-string"

    def __init__(self) -> None:
        super().__init__()
        self._parsed = False

    def convert(
        self,
        value: Optional[str],
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> Any:
        if self._parsed:
            # Click invokes this method TWICE
            # for a default value given as string.
            return value
        self._parsed = True
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            self.fail(f"cannot parse {value!r} as JSON", param, ctx)


def drange(start: Decimal, stop: Decimal, num: int):
    """
    A simplified version of numpy.linspace with default options
    """
    delta = stop - start
    step = delta / (num - 1)
    yield from (start + step * Decimal(tick) for tick in range(0, num))


class RangeExprOptionType(click.ParamType):
    """
    Accepts a range expression which generates a range of values for a variable.

    Linear space range: "linspace:1,2,10" (start, stop, num) as in numpy.linspace
    Pythonic range: "range:1,10,2" (start, stop[, step]) as in Python's range
    Case range: "case:a,b,c" (comma-separated strings)
    """

    _rx_range_key = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    name = "Range Expression"

    def convert(self, arg, param, ctx):
        key, value = arg.split("=", maxsplit=1)
        assert self._rx_range_key.match(key), "The key must be a valid slug string."
        try:
            if value.startswith("case:"):
                return key, value[5:].split(",")
            elif value.startswith("linspace:"):
                start, stop, num = value[9:].split(",")
                return key, tuple(drange(Decimal(start), Decimal(stop), int(num)))
            elif value.startswith("range:"):
                range_args = map(int, value[6:].split(","))
                return key, tuple(range(*range_args))
            else:
                self.fail("Unrecognized range expression type", param, ctx)
        except ValueError as e:
            self.fail(str(e), param, ctx)


class CommaSeparatedListType(click.ParamType):
    name = "List Expression"

    def convert(self, arg, param, ctx):
        try:
            if isinstance(arg, int):
                return arg
            elif isinstance(arg, str):
                return arg.split(",")
        except ValueError as e:
            self.fail(repr(e), param, ctx)


T = TypeVar("T")


class SingleValueConstructorType(Protocol):
    def __init__(self, value: Any) -> None: ...


TScalar = TypeVar("TScalar", bound=SingleValueConstructorType)


class OptionalType(click.ParamType, Generic[TScalar]):
    name = "Optional Type Wrapper"

    def __init__(self, type_: type[TScalar] | type[click.ParamType]) -> None:
        super().__init__()
        self.type_ = type_

    def convert(self, value: Any, param, ctx) -> TScalar | Undefined:
        try:
            if value is undefined:
                return undefined
            if issubclass(self.type_, click.ParamType):
                return self.type_()(value)
            return self.type_(value)
        except ValueError:
            self.fail(f"{value!r} is not valid `{self.type_}` or `undefined`", param, ctx)
