"""A type-checked scenario surface: no method names, field names or config paths as text.

What the string-keyed surface leaves to runtime, this leaves to the type checker.
An operation is bound from the adapter method itself, a field is named by reading it,
and an external fake is named by its class. Paths for failure messages are recovered by
replaying the same accessor over a recording proxy, so nothing is written twice.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Concatenate, cast, override

__all__ = (
    "At",
    "Every",
    "Invocation",
    "Op",
    "Some",
    "TypedMatcher",
    "TypedScenario",
    "TypedSetup",
    "at",
    "config_of",
    "every",
    "op",
    "path_of",
    "some",
)


# ---------------------------------------------------------------------------
# Naming a call: the adapter method itself, with its arguments checked
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Invocation[A, R]:
    """One adapter call with its arguments already bound.

    Carries the result type, so the ``then`` written beside it is checked against
    what the call actually returns.
    """

    call: Callable[[A], Awaitable[R]]
    label: str


type Op[A, **P, R] = Callable[P, Invocation[A, R]]


def op[A, **P, R](method: Callable[Concatenate[A, P], Awaitable[R]]) -> Op[A, P, R]:
    """Bind an adapter method into a scenario operation.

    ``op(DomainAdapter.get)("d1")`` is checked the way ``adapter.get("d1")`` is: a
    misspelled method is an attribute error at import, a wrong argument an ``arg-type``.
    """

    def bind(*args: P.args, **kwargs: P.kwargs) -> Invocation[A, R]:
        def run(adapter: A) -> Awaitable[R]:
            return method(adapter, *args, **kwargs)

        return Invocation(run, getattr(method, "__name__", "call"))

    return bind


# ---------------------------------------------------------------------------
# Naming a field: read it, and replay the read to recover its path
# ---------------------------------------------------------------------------


class _Recorder:
    """Answers any attribute with another recorder, remembering the chain."""

    _parts: tuple[str, ...]

    __slots__ = ("_parts",)

    def __init__(self, parts: tuple[str, ...] = ()) -> None:
        object.__setattr__(self, "_parts", parts)

    def __getattr__(self, name: str) -> _Recorder:
        if name == "_parts":
            raise AttributeError(name)
        return _Recorder(object.__getattribute__(self, "_parts") + (name,))

    def __getitem__(self, key: object) -> _Recorder:
        return _Recorder(object.__getattribute__(self, "_parts") + (f"[{key!r}]",))


def path_of[T](select: Callable[[T], object]) -> str:
    """The attribute chain an accessor reads, for the failure message.

    The accessor is written once and used twice: over the recorder for the path, over
    the payload for the value. An accessor that computes rather than reads answers with
    whatever it touched, which is still better than nothing.
    """
    try:
        result = select(cast(T, _Recorder()))
    except Exception:
        return "<computed>"
    if isinstance(result, _Recorder):
        return ".".join(object.__getattribute__(result, "_parts")) or "<self>"
    return "<computed>"


class TypedMatcher[T]:
    """What a payload of type ``T`` must satisfy."""

    def mismatches(self, actual: T) -> list[str]:
        raise NotImplementedError


@dataclass(frozen=True)
class At[T, V](TypedMatcher[T]):
    """One field, named by reading it, compared against a value of the field's type."""

    select: Callable[[T], V]
    expected: V

    @override
    def mismatches(self, actual: T) -> list[str]:
        got = self.select(actual)
        if got != self.expected:
            return [f"{path_of(self.select)}: expected {self.expected!r}, got {got!r}"]
        return []


def at[T, V](select: Callable[[T], V], expected: V) -> At[T, V]:
    """The field and the value it must hold, in one call.

    Both are checked from the position this sits in: the payload type comes from the
    ``when`` beside it, and the value must be what the field holds. Splitting this into
    two calls loses the payload type, so it stays one.
    """
    return At(select, expected)


@dataclass(frozen=True)
class Holds[T, V](TypedMatcher[T]):
    """One field, checked by a predicate over the field's own type."""

    select: Callable[[T], V]
    predicate: Callable[[V], bool]

    @override
    def mismatches(self, actual: T) -> list[str]:
        got = self.select(actual)
        if not self.predicate(got):
            return [f"{path_of(self.select)}: rejected {got!r}"]
        return []


def holds[T, V](select: Callable[[T], V], predicate: Callable[[V], bool]) -> Holds[T, V]:
    return Holds(select, predicate)


@dataclass(frozen=True)
class Every[T, V](TypedMatcher[T]):
    """Every element of a sequence field satisfies ``item``."""

    select: Callable[[T], Sequence[V]]
    item: TypedMatcher[V]

    @override
    def mismatches(self, actual: T) -> list[str]:
        out: list[str] = []
        base = path_of(self.select)
        for i, element in enumerate(self.select(actual)):
            out.extend(f"{base}[{i}].{m}" for m in self.item.mismatches(element))
        return out


def every[T, V](select: Callable[[T], Sequence[V]], item: TypedMatcher[V]) -> Every[T, V]:
    return Every(select, item)


@dataclass(frozen=True)
class Some[T, V](TypedMatcher[T]):
    """At least one element of a sequence field satisfies ``item``."""

    select: Callable[[T], Sequence[V]]
    item: TypedMatcher[V]

    @override
    def mismatches(self, actual: T) -> list[str]:
        elements = self.select(actual)
        if any(not self.item.mismatches(e) for e in elements):
            return []
        return [f"{path_of(self.select)}: no element matches"]


def some[T, V](select: Callable[[T], Sequence[V]], item: TypedMatcher[V]) -> Some[T, V]:
    return Some(select, item)


@dataclass(frozen=True)
class All[T](TypedMatcher[T]):
    parts: tuple[TypedMatcher[T], ...]

    @override
    def mismatches(self, actual: T) -> list[str]:
        return [m for part in self.parts for m in part.mismatches(actual)]


def all_of_typed[T](*parts: TypedMatcher[T]) -> All[T]:
    return All(parts)


# ---------------------------------------------------------------------------
# Naming a config value and an external fake: by accessor and by class
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Override[C, V]:
    """One config value to change, named by reading it off the config object."""

    select: Callable[[C], V]
    value: V

    def dotted(self) -> str:
        return path_of(self.select)


class ConfigOf[C]:
    """Names config fields of one config class.

    The class is fixed here rather than at each override: an accessor written inside a
    list has no position to read its own parameter type from, and an unread parameter
    makes the field name text again.
    """

    def set[V](self, select: Callable[[C], V], value: V) -> Override[C, Any]:
        """One config field and the value to put in it, both checked against the class."""
        return Override(select, value)


def config_of[C](config_cls: type[C]) -> ConfigOf[C]:
    return ConfigOf()


@dataclass(frozen=True)
class TypedSetup[C]:
    """Config overrides named by accessor, external fakes keyed by their class."""

    config: Sequence[Override[C, Any]] = ()
    extras: Mapping[type[Any], Any] = field(default_factory=dict)

    def dotted_config(self) -> dict[str, Any]:
        return {o.dotted(): o.value for o in self.config}


@dataclass(frozen=True)
class OnFake[T, F](TypedMatcher[T]):
    """A matcher over an external fake rather than the payload; the fake names itself."""

    fake: type[F]
    matcher: TypedMatcher[F]


def on_fake[T, F](fake: type[F], matcher: TypedMatcher[F]) -> OnFake[T, F]:
    return OnFake(fake, matcher)


# ---------------------------------------------------------------------------
# The scenario: result type bound where it is written, erased where it is stored
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TypedScenario[A, C]:
    """A scenario over adapter ``A`` and config ``C``.

    The result type is checked where the row is written and dropped afterwards, so a
    table of rows returning different payloads is still one list.
    """

    id: str
    invoke: Callable[[A], Awaitable[Any]]
    then: TypedMatcher[Any] | type[BaseException] | None = None
    setup: TypedSetup[C] = field(default_factory=TypedSetup)

    @classmethod
    def ok[R](
        cls,
        id: str,
        *,
        when: Invocation[A, R],
        then: TypedMatcher[R] | None = None,
        setup: TypedSetup[C] | None = None,
    ) -> TypedScenario[A, C]:
        return cls(id, when.call, then, setup or TypedSetup())

    @classmethod
    def error[R](
        cls,
        id: str,
        *,
        when: Invocation[A, R],
        then: type[BaseException],
        setup: TypedSetup[C] | None = None,
    ) -> TypedScenario[A, C]:
        return cls(id, when.call, then, setup or TypedSetup())
