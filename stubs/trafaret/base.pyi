"""
trafaret_light.py
-----------------
A lightweight trafaret-like validation library.

Features:
- Dict, List, String, Int, Bool, Enum, Type validators
- Key handling with defaults, optional fields, renaming
- And / Or composition operators
- Guard decorator for function validation
- Clear error reporting with paths

Author: James + Jimmi
"""

from __future__ import annotations
from typing import (
    Any as _Any,
    Optional,
    Hashable,
    Type as _Type,
    List as _List,
    Dict as _Dict,
    Callable as _Callable,
    Union,
    cast,
)


# --- Exceptions --------------------------------------------------------------


class DataError(Exception):
    """Raised when validation fails. Carries a message and optional path/context."""

    def __init__(self, message: str, path: Optional[_List[Hashable]] = None):
        super().__init__(message)
        self.message = message
        self.path = path or []

    def with_prefix(self, prefix: Hashable) -> DataError:
        return DataError(self.message, [prefix] + self.path)

    def __str__(self) -> str:
        if self.path:
            return f"{'.'.join(map(str, reversed(self.path)))}: {self.message}"
        return self.message


class GuardError(DataError):
    """Specialized error for guard/guarded functions."""

    pass


# --- Base trafaret ----------------------------------------------------------


class Trafaret:
    def check(self, value: _Any, context: Optional[_Any] = None) -> _Any:
        raise NotImplementedError

    def _failure(self, message: Optional[str] = None) -> None:
        raise DataError(message or "check failed")

    def __and__(self, other: Trafaret) -> Trafaret:
        return And(self, ensure_trafaret(other))

    def __or__(self, other: Trafaret) -> Trafaret:
        return Or(self, ensure_trafaret(other))

    def __rshift__(self, other: str) -> Trafaret:
        # Transformation operator (used mainly in Key)
        raise NotImplementedError

    def __call__(self, val, context=None):
        return self.check(val, context)


# --- Composition trafarets --------------------------------------------------


class And(Trafaret):
    def __init__(self, *items: Trafaret):
        self.items = [ensure_trafaret(i) for i in items]

    def check(self, value, context=None):
        v = value
        for t in self.items:
            v = t.check(v, context)
        return v


class Or(Trafaret):
    def __init__(self, *items: Trafaret):
        self.items = [ensure_trafaret(i) for i in items]

    def check(self, value, context=None):
        errors = []
        for t in self.items:
            try:
                return t.check(value, context)
            except DataError as e:
                errors.append(str(e))
        raise DataError(" or ".join(errors))


class OnError(Trafaret):
    def __init__(self, trafaret: Trafaret, message: str, code: Optional[str] = None):
        self.trafaret = ensure_trafaret(trafaret)
        self.message = message
        self.code = code

    def check(self, value, context=None):
        try:
            return self.trafaret.check(value, context)
        except DataError:
            raise DataError(self.message)


# --- Primitives -------------------------------------------------------------


class Any(Trafaret):
    def check(self, value, context=None):
        return value


class Int(Trafaret):
    def __init__(self, min_value: Optional[int] = None, max_value: Optional[int] = None):
        self.min_value = min_value
        self.max_value = max_value

    def check(self, value, context=None):
        if not isinstance(value, int) or isinstance(value, bool):
            raise DataError(f"expected int, got {type(value).__name__}")
        if self.min_value is not None and value < self.min_value:
            raise DataError(f"value {value} < {self.min_value}")
        if self.max_value is not None and value > self.max_value:
            raise DataError(f"value {value} > {self.max_value}")
        return value


class String(Trafaret):
    def __init__(
        self,
        allow_blank: bool = False,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ):
        self.allow_blank = allow_blank
        self.min_length = min_length
        self.max_length = max_length

    def check(self, value, context=None):
        if not isinstance(value, str):
            raise DataError(f"expected str, got {type(value).__name__}")
        if not self.allow_blank and value == "":
            raise DataError("empty string not allowed")
        L = len(value)
        if self.min_length is not None and L < self.min_length:
            raise DataError(f"length {L} < {self.min_length}")
        if self.max_length is not None and L > self.max_length:
            raise DataError(f"length {L} > {self.max_length}")
        return value


class Bool(Trafaret):
    def check(self, value, context=None):
        if not isinstance(value, bool):
            raise DataError(f"expected bool, got {type(value).__name__}")
        return value


class Enum(Trafaret):
    def __init__(self, *variants):
        self.variants = variants

    def check(self, value, context=None):
        if value not in self.variants:
            raise DataError(f"value {value!r} not in enum {self.variants}")
        return value


class Type(Trafaret):
    def __init__(self, type_: _Type):
        self.type_ = type_

    def check(self, value, context=None):
        if not isinstance(value, self.type_):
            raise DataError(
                f"expected type {self.type_.__name__}, got {type(value).__name__}"
            )
        return value


class CallableTrafaret(Trafaret):
    def check(self, value, context=None):
        if not callable(value):
            raise DataError("expected callable")
        return value


# --- Containers -------------------------------------------------------------


class ListTrafaret(Trafaret):
    def __init__(
        self, trafaret: Trafaret, min_length: int = 0, max_length: Optional[int] = None
    ):
        self.trafaret = ensure_trafaret(trafaret)
        self.min_length = min_length
        self.max_length = max_length

    def check(self, value, context=None):
        if not isinstance(value, (list, tuple)):
            raise DataError(f"expected list/tuple, got {type(value).__name__}")
        L = len(value)
        if L < self.min_length:
            raise DataError(f"length {L} < {self.min_length}")
        if self.max_length is not None and L > self.max_length:
            raise DataError(f"length {L} > {self.max_length}")
        out = []
        for i, item in enumerate(value):
            try:
                out.append(self.trafaret.check(item, context))
            except DataError as e:
                raise e.with_prefix(i)
        return out


class MappingTrafaret(Trafaret):
    def __init__(self, key_trafaret: Trafaret, value_trafaret: Trafaret):
        self.key_trafaret = ensure_trafaret(key_trafaret)
        self.value_trafaret = ensure_trafaret(value_trafaret)

    def check(self, value, context=None):
        if not isinstance(value, dict):
            raise DataError("expected dict/map")
        out = {}
        for k, v in value.items():
            try:
                kk = self.key_trafaret.check(k, context)
            except DataError as e:
                raise e.with_prefix(k)
            try:
                out[kk] = self.value_trafaret.check(v, context)
            except DataError as e:
                raise e.with_prefix(k)
        return out


# --- Key & Dict -------------------------------------------------------------


class Key:
    def __init__(
        self,
        name: Hashable,
        default: _Any = ...,
        optional: bool = False,
        to_name: Optional[Hashable] = None,
        trafaret: Optional[Trafaret] = None,
    ):
        self.name = name
        self.default = default
        self.optional = optional
        self.to_name = to_name
        self.trafaret = ensure_trafaret(trafaret) if trafaret is not None else None

    def get_name(self) -> Hashable:
        return self.name

    def __rshift__(self, other: str) -> Key:
        return Key(self.name, self.default, self.optional, other, self.trafaret)

    def with_trafaret(self, t: Trafaret) -> Key:
        return Key(
            self.name, self.default, self.optional, self.to_name, ensure_trafaret(t)
        )


def ensure_trafaret(trafaret) -> Trafaret:
    if isinstance(trafaret, Trafaret):
        return trafaret
    if isinstance(trafaret, type) and issubclass(trafaret, Trafaret):
        return trafaret()
    # allow raw python types shortcuts
    if trafaret is int:
        return Int()
    if trafaret is str:
        return String()
    if trafaret is bool:
        return Bool()
    if trafaret is dict:
        return MappingTrafaret(Any(), Any())
    if callable(trafaret):
        # if it's a function that acts as validator — wrap it
        return Call(trafaret)
    raise TypeError(f"cannot ensure trafaret from: {trafaret!r}")


class DictTrafaret(Trafaret):
    def __init__(self, *args, **kw):
        self.keys: _Dict[Hashable, Key] = {}
        self.allow_extra_names = set()
        self.ignore_extra_names = set()
        for a in args:
            if isinstance(a, Key):
                self.keys[a.name] = a
            elif isinstance(a, dict):
                for k, v in a.items():
                    self.keys[k] = Key(k, trafaret=ensure_trafaret(v))
            else:
                raise TypeError("DictTrafaret args must be Key or dict")
        for k, v in kw.items():
            self.keys[k] = Key(k, trafaret=ensure_trafaret(v))

    def allow_extra(self, *names: str) -> DictTrafaret:
        self.allow_extra_names.update(names)
        return self

    def ignore_extra(self, *names: str) -> DictTrafaret:
        self.ignore_extra_names.update(names)
        return self

    def merge(self, other):
        if isinstance(other, DictTrafaret):
            for k, key in other.keys.items():
                self.keys[k] = key
        elif isinstance(other, dict):
            for k, v in other.items():
                self.keys[k] = Key(k, trafaret=ensure_trafaret(v))
        elif isinstance(other, (list, tuple)):
            for item in other:
                if isinstance(item, Key):
                    self.keys[item.name] = item
        else:
            raise TypeError(f"can't merge with {other!r}")
        return self

    def check(self, value, context=None):
        if not isinstance(value, dict):
            raise DataError("expected dict")
        out = {}
        for name, key in self.keys.items():
            if name in value:
                val = value[name]
                try:
                    if key.trafaret is not None:
                        out_name = key.to_name if key.to_name is not None else name
                        out[out_name] = key.trafaret.check(val, context)
                    else:
                        out[key.to_name or name] = val
                except DataError as e:
                    raise e.with_prefix(name)
            else:
                if key.default is not ...:
                    out_name = key.to_name if key.to_name is not None else name
                    out[out_name] = key.default
                elif key.optional:
                    continue
                else:
                    raise DataError("missing required key", path=[name])

        extras = {k: v for k, v in value.items() if k not in self.keys}
        for k, v in extras.items():
            if k in self.ignore_extra_names:
                continue
            if self.allow_extra_names and k not in self.allow_extra_names:
                raise DataError(f"unexpected key {k}", path=[k])
            out[k] = v
        return out


# --- Call wrapper -----------------------------------------------------------


class Call(Trafaret):
    def __init__(self, fn: _Callable):
        self.fn = fn

    def check(self, value, context=None):
        try:
            result = self.fn(value)
            return result
        except DataError:
            raise
        except Exception as e:
            raise DataError(str(e))


# --- Helpers ----------------------------------------------------------------


def ignore(val):
    return val


def catch(checker: Trafaret, *a, **kw):
    checker = ensure_trafaret(checker)
    try:
        return checker.check(*a, **kw)
    except DataError as e:
        return e


def extract_error(checker: Trafaret, *a, **kw):
    checker = ensure_trafaret(checker)
    try:
        checker.check(*a, **kw)
        return None
    except DataError as e:
        return e


def guard(trafaret: Optional[Trafaret] = None, **kwargs):
    """
    Decorator that validates a single argument passed to the function.
    """

    def deco(fn: _Callable):
        tf: Optional[Trafaret] = (
            ensure_trafaret(trafaret) if trafaret is not None else None
        )

        def wrapped(arg):
            if tf is None:
                return fn(arg)
            try:
                val = tf.check(arg)
            except DataError as e:
                raise GuardError(str(e))
            return fn(val)

        return wrapped

    return deco


# --- Aliases ----------------------------------------------------------------

Dict = DictTrafaret
List = ListTrafaret
TypeT = Type
IntT = Int
StrT = String
BoolT = Bool
AnyT = Any
EnumT = Enum


# --- Quick demo -------------------------------------------------------------

if __name__ == "__main__":
    schema = Dict(
        Key("name", trafaret=String(min_length=2)),
        Key("age", trafaret=Int(min_value=0), optional=True, default=0),
        Key("role", trafaret=Enum("admin", "user"), optional=True),
    ).allow_extra("metadata")

    good = {"name": "Alice", "age": 30, "metadata": {"foo": "bar"}}
    bad = {"name": "A", "age": -5}

    print("good ->", schema.check(good))
    try:
        print("bad ->", schema.check(bad))
    except DataError as e:
        print("bad failed:", e)

    lt = List(Int(min_value=0), min_length=1)
    print("list good ->", lt.check([1, 2, 3]))
    try:
        print("list bad ->", lt.check([]))
    except DataError as e:
        print("list failed:", e)

    @guard(Int(min_value=10))
    def accept_big(x):
        return x * 2

    print("guard ok:", accept_big(12))
    try:
        print("guard fail:", accept_big(5))
    except GuardError as e:
        print("guard error:", e)
