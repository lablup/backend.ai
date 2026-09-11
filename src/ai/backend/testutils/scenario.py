"""Scenario-table primitives.

Generic: knows nothing about the manager. What a scenario names (actor, seed, adapter
method) is resolved by a runner that does. ``ScenarioBase`` stays for the eleven files
that already use it.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, NewType, Protocol, Self, TypeVar, runtime_checkable

import pytest

TInput = TypeVar("TInput")
TResult = TypeVar("TResult")
E = TypeVar("E", bound=BaseException)
TException = type[E] | tuple[type[E], ...]


class ScenarioBase[TInput, TResult]:
    description: str
    input: TInput
    expected: TResult | None
    expected_exception: TException | None  # type: ignore[type-arg]

    def __init__(
        self,
        description: str,
        input: TInput,
        expected: TResult | None,
        expected_exception: TException | None,  # type: ignore[type-arg]
    ) -> None:
        self.description = description
        self.input = input
        self.expected = expected
        self.expected_exception = expected_exception

    @classmethod
    def success(cls, description: str, input: TInput, expected: TResult) -> Self:
        return cls(description, input, expected, None)

    @classmethod
    def failure(cls, description: str, input: TInput, expected_exception: TException) -> Self:  # type: ignore[type-arg]
        return cls(description, input, None, expected_exception)

    async def test(self, fn: Callable[[TInput], Awaitable[TResult | None]]) -> None:
        if self.expected_exception is not None:
            with pytest.raises(self.expected_exception):
                await fn(self.input)
        else:
            result = await fn(self.input)
            if result != self.expected:
                raise AssertionError(
                    f"Expected {self.expected!r} but got {result!r} for scenario: {self.description}"
                )


# ---------------------------------------------------------------------------
# Actors and seeds
# ---------------------------------------------------------------------------

# The name of who acts. The manager kit maps a persona to a user it seeded.
Persona = NewType("Persona", str)


@dataclass(frozen=True)
class Seed:
    """A row to lay down before ``when`` runs, described lazily.

    ``build`` receives the runner's seed context (the kit decides its type) and does
    the write. ``owner`` is who the write is attributed to; ``None`` means the runner's
    default persona.
    """

    label: str
    build: Callable[[Any], Awaitable[Any]]
    owner: Persona | None = None


# ---------------------------------------------------------------------------
# Matchers (then)
# ---------------------------------------------------------------------------


@runtime_checkable
class Matcher(Protocol):
    def mismatches(self, actual: Any, path: str = "") -> list[str]:
        """Empty when ``actual`` satisfies the matcher; one line per mismatch otherwise."""
        ...


def _read(actual: Any, key: str) -> Any:
    if isinstance(actual, Mapping):
        if key not in actual:
            raise KeyError(key)
        return actual[key]
    return getattr(actual, key)


def _check(expected: Any, actual: Any, path: str) -> list[str]:
    if isinstance(expected, Matcher):
        return expected.mismatches(actual, path)
    if callable(expected) and not isinstance(expected, type):
        return [] if expected(actual) else [f"{path}: predicate rejected {actual!r}"]
    if expected != actual:
        return [f"{path}: expected {expected!r}, got {actual!r}"]
    return []


@dataclass(frozen=True)
class Has:
    """Partial match: only the named fields are compared; nested values may be matchers."""

    fields: Mapping[str, Any]

    def mismatches(self, actual: Any, path: str = "") -> list[str]:
        out: list[str] = []
        for key, expected in self.fields.items():
            sub = f"{path}.{key}" if path else key
            try:
                value = _read(actual, key)
            except (AttributeError, KeyError):
                out.append(f"{sub}: missing on {type(actual).__name__}")
                continue
            out.extend(_check(expected, value, sub))
        return out


def has(**fields: Any) -> Has:
    return Has(fields)


@dataclass(frozen=True)
class Each:
    """Every element of a sequence satisfies ``item``."""

    item: Any

    def mismatches(self, actual: Any, path: str = "") -> list[str]:
        out: list[str] = []
        for i, element in enumerate(actual):
            out.extend(_check(self.item, element, f"{path}[{i}]"))
        return out


def each(item: Any) -> Each:
    return Each(item)


@dataclass(frozen=True)
class Contains:
    """At least one element of a sequence satisfies ``item``."""

    item: Any

    def mismatches(self, actual: Any, path: str = "") -> list[str]:
        for element in actual:
            if not _check(self.item, element, path):
                return []
        return [f"{path}: no element matches {self.item!r} in {actual!r}"]


def contains(item: Any) -> Contains:
    return Contains(item)


@dataclass(frozen=True)
class Length:
    n: int

    def mismatches(self, actual: Any, path: str = "") -> list[str]:
        if len(actual) != self.n:
            return [f"{path}: expected length {self.n}, got {len(actual)}"]
        return []


def length(n: int) -> Length:
    return Length(n)


@dataclass(frozen=True)
class IsType:
    """The payload is an instance of ``cls`` and nothing else is checked (smoke)."""

    cls: type

    def mismatches(self, actual: Any, path: str = "") -> list[str]:
        if not isinstance(actual, self.cls):
            return [
                f"{path or 'result'}: expected {self.cls.__name__}, got {type(actual).__name__}"
            ]
        return []


def is_type(cls: type) -> IsType:
    return IsType(cls)


@dataclass(frozen=True)
class Snapshot:
    """Whole-shape match: the payload dumped to a dict must equal ``expected`` after the
    ``volatile`` paths (dotted) are removed from both sides."""

    expected: Mapping[str, Any]
    volatile: Sequence[str] = ()

    def mismatches(self, actual: Any, path: str = "") -> list[str]:
        dumped = actual.model_dump(mode="json") if hasattr(actual, "model_dump") else dict(actual)
        got = _strip(dumped, self.volatile)
        want = _strip(dict(self.expected), self.volatile)
        if got != want:
            return [f"{path or 'result'}: snapshot differs\n  want={want!r}\n  got ={got!r}"]
        return []


def _strip(value: Any, paths: Sequence[str]) -> Any:
    for dotted in paths:
        parts = dotted.split(".")
        cursor = value
        for part in parts[:-1]:
            if isinstance(cursor, Mapping) and part in cursor:
                cursor = cursor[part]
            else:
                cursor = None
                break
        if isinstance(cursor, dict):
            cursor.pop(parts[-1], None)
    return value


def snapshot(expected: Mapping[str, Any], *, volatile: Sequence[str] = ()) -> Snapshot:
    return Snapshot(expected, tuple(volatile))


@dataclass(frozen=True)
class AllOf:
    parts: tuple[Any, ...]

    def mismatches(self, actual: Any, path: str = "") -> list[str]:
        return [m for part in self.parts for m in _check(part, actual, path)]


def all_of(*parts: Any) -> AllOf:
    return AllOf(parts)


@dataclass(frozen=True)
class OnExtra:
    """Apply ``matcher`` to the run's extra named ``name`` (an external fake) instead of
    the result. Only a runner that hands out extras can evaluate it."""

    name: str
    matcher: Any

    def mismatches(self, actual: Any, path: str = "") -> list[str]:
        raise TypeError("on_extra() needs the runner's extras; use mismatches_for()")


def on_extra(name: str, matcher: Any) -> OnExtra:
    return OnExtra(name, matcher)


def mismatches_for(then: Any, result: Any, extras: Mapping[str, Any]) -> list[str]:
    if isinstance(then, OnExtra):
        if then.name not in extras:
            return [f"extra {then.name!r} not provided by the wiring; have {sorted(extras)}"]
        return _check(then.matcher, extras[then.name], then.name)
    if isinstance(then, AllOf):
        return [m for part in then.parts for m in mismatches_for(part, result, extras)]
    return _check(then, result, "")


@dataclass(frozen=True)
class Raises:
    exc_type: type[BaseException]
    contains: str | None = None


# ---------------------------------------------------------------------------
# when / setup / steps
# ---------------------------------------------------------------------------


@dataclass(frozen=True, init=False)
class Call:
    """Name the method when the ``when`` value alone does not pick one: a path parameter
    beside the body, or a read that takes no DTO at all."""

    method: str
    args: tuple[Any, ...]
    kwargs: Mapping[str, Any]

    def __init__(self, method: str, *args: Any, **kwargs: Any) -> None:
        object.__setattr__(self, "method", method)
        object.__setattr__(self, "args", args)
        object.__setattr__(self, "kwargs", kwargs)


@dataclass(frozen=True)
class Setup:
    """What a scenario overrides for its run: config values by dotted path, and extras
    (external fakes and their scripts) by the name the wiring gives them."""

    config: Mapping[str, Any] = field(default_factory=dict)
    extras: Mapping[str, Any] = field(default_factory=dict)


# ``when`` of a step may be computed from the results so far.
type When = Any | Callable[["StepContext"], Any]
type Then = Matcher | Raises | None


@dataclass
class StepContext:
    """Results of the steps run so far, in order."""

    results: list[Any] = field(default_factory=list)
    seeded: dict[str, Any] = field(default_factory=dict)

    @property
    def prev(self) -> Any:
        return self.results[-1]


@dataclass(frozen=True, init=False)
class Step:
    when: When
    then: Then
    actor: Persona | None

    def __init__(
        self,
        when: When,
        then: Then | type[BaseException] = None,
        actor: Persona | None = None,
    ) -> None:
        object.__setattr__(self, "when", when)
        object.__setattr__(self, "then", Raises(then) if isinstance(then, type) else then)
        object.__setattr__(self, "actor", actor)


@dataclass(frozen=True)
class Scenario:
    id: str
    when: When = None
    then: Then = None
    actor: Persona | None = None
    given: Sequence[Seed] = ()
    setup: Setup = field(default_factory=Setup)
    steps: Sequence[Step] = ()
    # A runner that sees a different outcome names it here, keyed by ``Runner.name``:
    # the HTTP path refuses a member at the route before the adapter ever runs.
    variants: Mapping[str, Then] = field(default_factory=dict)

    @classmethod
    def ok(
        cls,
        id: str,
        *,
        when: When,
        then: Matcher | None = None,
        actor: Persona | None = None,
        given: Sequence[Seed] = (),
        setup: Setup | None = None,
        variants: Mapping[str, Then | type[BaseException]] | None = None,
    ) -> Scenario:
        return cls(
            id, when, then, actor, tuple(given), setup or Setup(), variants=_variants(variants)
        )

    @classmethod
    def error(
        cls,
        id: str,
        *,
        when: When,
        then: type[BaseException] | tuple[type[BaseException], str],
        actor: Persona | None = None,
        given: Sequence[Seed] = (),
        setup: Setup | None = None,
    ) -> Scenario:
        raises = Raises(then) if isinstance(then, type) else Raises(then[0], then[1])
        return cls(id, when, raises, actor, tuple(given), setup or Setup())

    @classmethod
    def flow(
        cls,
        id: str,
        *,
        steps: Sequence[Step],
        actor: Persona | None = None,
        given: Sequence[Seed] = (),
        setup: Setup | None = None,
    ) -> Scenario:
        """Up to a few dependent calls in order. Anything longer is a plain test."""
        return cls(id, None, None, actor, tuple(given), setup or Setup(), tuple(steps))

    def all_steps(self, runner: str = "") -> Sequence[Step]:
        if self.steps:
            return self.steps
        then = self.variants.get(runner, self.then) if runner else self.then
        return (Step(self.when, then, self.actor),)


def _variants(raw: Mapping[str, Then | type[BaseException]] | None) -> dict[str, Then]:
    out: dict[str, Then] = {}
    for runner, then in (raw or {}).items():
        out[runner] = Raises(then) if isinstance(then, type) else then
    return out


def scenario_id(s: Scenario) -> str:
    return s.id


def check_then(
    then: Then, result: Any, scenario_id: str, extras: Mapping[str, Any] | None = None
) -> None:
    """Apply a non-raising ``then`` to a result, failing with every mismatch listed."""
    if then is None:
        return
    if isinstance(then, Raises):
        raise AssertionError(
            f"[{scenario_id}] expected {then.exc_type.__name__} but the call returned {result!r}"
        )
    problems = mismatches_for(then, result, extras or {})
    if problems:
        raise AssertionError(f"[{scenario_id}] " + "; ".join(problems))


def check_raised(then: Then, exc: BaseException, scenario_id: str) -> None:
    """Apply a raising ``then`` to what was raised; re-raise anything unexpected."""
    if not isinstance(then, Raises):
        raise exc
    if not isinstance(exc, then.exc_type):
        raise AssertionError(
            f"[{scenario_id}] expected {then.exc_type.__name__}, got {type(exc).__name__}: {exc}"
        ) from exc
    if then.contains is not None and then.contains not in str(exc):
        raise AssertionError(
            f"[{scenario_id}] {type(exc).__name__} lacks {then.contains!r}: {exc}"
        ) from exc


class Runner(Protocol):
    name: str

    async def __call__(self, scenario: Scenario) -> None: ...
