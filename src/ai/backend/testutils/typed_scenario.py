"""A type-checked scenario surface: no method names, field names or config paths as text.

What a text-keyed surface leaves to runtime, this leaves to the type checker. An
operation is bound from the method itself, a field is named by reading it, a config
value by reading it off the config class, and an external client by its own class.
Paths for failure messages are recovered by replaying the same accessor over a
recording proxy, so nothing is written twice.

Nothing here knows any component. What rows a scenario lays down, which adapter it
calls and which config class it reads are all supplied by whoever uses it; the manager
side lives in the test kit.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import MISSING, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Concatenate, Final, cast, override
from uuid import UUID

from ai.backend.testutils.scenario_report import ScenarioRecord

__all__ = (
    "At",
    "Every",
    "Invocation",
    "Op",
    "Some",
    "TypedMatcher",
    "All",
    "OnFake",
    "Holds",
    "TypedScenario",
    "Situation",
    "Sown",
    "situation",
    "Answer",
    "FakeOf",
    "Deferred",
    "ActorBound",
    "Called",
    "Checked",
    "Exactly",
    "Ignored",
    "Taken",
    "mismatches_of",
    "config_of",
    "since",
    "fake_of",
    "op",
    "call",
    "path_of",
    "shown_for",
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
    args: tuple[Any, ...] = ()
    kwargs: Mapping[str, Any] = field(default_factory=dict)
    """What the call was given, kept raw: what it reads as depends on the rows laid."""


type Op[A, **P, R] = Callable[P, Invocation[A, R]]


def call[A, **P, R](
    method: Callable[Concatenate[A, P], Awaitable[R]], *args: P.args, **kwargs: P.kwargs
) -> Invocation[A, R]:
    """The call this row makes, named as the adapter's own method.

    ``call(DomainAdapter.get, "d1")`` is checked the way ``adapter.get("d1")`` is, and
    the row says which method it exercises without a stand-in for it.
    """
    return op(method)(*args, **kwargs)


def op[A, **P, R](method: Callable[Concatenate[A, P], Awaitable[R]]) -> Op[A, P, R]:
    """Bind an adapter method into a scenario operation.

    ``op(DomainAdapter.get)("d1")`` is checked the way ``adapter.get("d1")`` is: a
    misspelled method is an attribute error at import, a wrong argument an ``arg-type``.
    """

    def bind(*args: P.args, **kwargs: P.kwargs) -> Invocation[A, R]:
        def run(adapter: A) -> Awaitable[R]:
            return method(adapter, *args, **kwargs)

        return Invocation(run, getattr(method, "__name__", "call"), args, kwargs)

    return bind


type Naming = Callable[[object], str | None]
"""Answers with the row a value came from, or ``None`` when no row made it."""


def _shown(args: tuple[Any, ...], kwargs: Mapping[str, Any], naming: Naming) -> tuple[str, ...]:
    """What was passed, with everything the caller left alone left out.

    A request model carries a field for every option the call has, and a report that
    prints them all says nothing. What the caller wrote is what the row is about.
    """
    parts = [_shown_one(one, naming) for one in args]
    parts.extend(f"{name}={_shown_one(value, naming)}" for name, value in kwargs.items())
    return tuple(parts)


def _shown_one(value: object, naming: Naming) -> str:
    """One argument, down to the fields it was actually given.

    A value a laid row made is named by that row, so the report says which row the call
    reached for and reads the same for two runs of the same behaviour.
    """
    made_by = naming(value)
    if made_by is not None:
        return made_by
    if isinstance(value, UUID):
        return f"{type(value).__name__}(어느 행도 만들지 않은 id)"
    written = getattr(value, "model_fields_set", None)
    declared = getattr(type(value), "model_fields", None)
    if written is not None and isinstance(declared, Mapping):
        inner = ", ".join(
            f"{name}={_shown_one(getattr(value, name), naming)}"
            for name in declared
            if name in written
        )
        return f"{type(value).__name__}({inner})"
    fields = getattr(type(value), "__dataclass_fields__", None)
    if isinstance(fields, Mapping):
        inner = ", ".join(
            f"{name}={_shown_one(getattr(value, name), naming)}"
            for name, spec in fields.items()
            if not _left_alone(getattr(value, name), spec)
        )
        return f"{type(value).__name__}({inner})"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_shown_one(one, naming) for one in value) + "]"
    return repr(value)


def shown_for(invocation: Invocation[Any, Any], sown: Sown) -> tuple[str, ...]:
    """What the report says this call was given, once the rows are known."""
    return _shown(invocation.args, invocation.kwargs, _naming_of(sown))


def _naming_of(sown: Sown) -> Naming:
    """Which laid row made a value, by the id that row answered with."""
    named: dict[UUID, str] = {}
    for row, data in sown.items():
        label = getattr(row, "describe", None)
        if not isinstance(label, str):
            continue
        for candidate in (data, getattr(data, "id", None)):
            if isinstance(candidate, UUID):
                named.setdefault(UUID(int=candidate.int), label)

    def naming(value: object) -> str | None:
        if isinstance(value, UUID):
            return named.get(UUID(int=value.int))
        return None

    return naming


def _left_alone(value: object, spec: Any) -> bool:
    """Whether a dataclass field still holds what it was declared to hold."""
    if spec.default is not MISSING:
        return bool(value == spec.default)
    if spec.default_factory is not MISSING:
        return bool(value == spec.default_factory())
    return False


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

    def describe(self) -> str:
        """What this checks, for the report."""
        return "답을 확인한다"


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

    @override
    def describe(self) -> str:
        return f"{path_of(self.select)} = {self.expected!r}"


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

    @override
    def describe(self) -> str:
        return f"{path_of(self.select)} 조건 충족"


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

    @override
    def describe(self) -> str:
        return f"{path_of(self.select)} 전부: {self.item.describe()}"


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

    @override
    def describe(self) -> str:
        return f"{path_of(self.select)} 중 하나: {self.item.describe()}"


@dataclass(frozen=True)
class All[T](TypedMatcher[T]):
    parts: tuple[TypedMatcher[T], ...]

    @override
    def mismatches(self, actual: T) -> list[str]:
        return [m for part in self.parts for m in part.mismatches(actual)]

    @override
    def describe(self) -> str:
        return "; ".join(part.describe() for part in self.parts)


@dataclass(frozen=True)
class Override[C, V]:
    """One config value to change, named by reading it off the config object."""

    select: Callable[[C], V]
    value: V

    def dotted(self) -> str:
        return path_of(self.select)


@dataclass(frozen=True)
class ConfigOf[C]:
    """Names config fields of one config class.

    The class is fixed here rather than at each override: an accessor written inside a
    list has no position to read its own parameter type from, and an unread parameter
    makes the field name text again.
    """

    config_cls: type[C]

    def set[V](self, select: Callable[[C], V], value: V) -> Override[C, Any]:
        """One config field and the value to put in it, both checked against the class."""
        return Override(select, value)


def config_of[C](config_cls: type[C]) -> ConfigOf[C]:
    return ConfigOf(config_cls)


# ---------------------------------------------------------------------------
# Setting the situation: what the outside answers, said in the outside's own types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Answer[F]:
    """What one method of an external client answers for this scenario.

    The value is checked against the return type the real client declares, so a fake
    cannot answer something the manager would never receive.
    """

    method_name: str
    value: Any = None
    error: BaseException | None = None

    def apply(self, fake: F) -> None:
        """Install this answer on the fake, replacing whatever it answered before."""
        setattr(fake, f"__scripted_{self.method_name}", self)


class FakeOf[F]:
    """Scripts one external client class. The class is fixed here so each answer is
    checked against the method it belongs to."""

    _cls: type[F]

    def __init__(self, cls: type[F]) -> None:
        self._cls = cls

    @property
    def cls(self) -> type[F]:
        return self._cls

    def answers[**P, R](
        self, method: Callable[Concatenate[F, P], Awaitable[R]], value: R
    ) -> Answer[F]:
        """This method answers ``value``. ``R`` is the client's own return type."""
        return Answer(method.__name__, value=value)

    def raises[**P, R](
        self, method: Callable[Concatenate[F, P], Awaitable[R]], error: BaseException
    ) -> Answer[F]:
        """This method refuses with ``error`` instead of answering."""
        return Answer(method.__name__, error=error)


def fake_of[F](cls: type[F]) -> FakeOf[F]:
    return FakeOf(cls)


type Sown = Mapping[Any, Any]
"""What the seeds made, reached by holding the seed itself."""


@dataclass(frozen=True)
class Situation[C]:
    """What is already true when the call is made, on three axes: the rows in the
    database, what the config says, and what the outside answers.

    A row is a handle the component's own seeder made. Nothing here knows what writing
    one involves; the runner hands them back to that seeder.
    """

    rows: Sequence[object] = ()
    config: Sequence[Override[C, Any]] = ()
    answers: Sequence[Answer[Any]] = ()

    def dotted_config(self) -> dict[str, Any]:
        return {o.dotted(): o.value for o in self.config}


def situation[C](
    *,
    rows: Sequence[object] = (),
    config: Sequence[Override[C, Any]] = (),
    answers: Sequence[Answer[Any]] = (),
) -> Situation[C]:
    return Situation(tuple(rows), tuple(config), tuple(answers))


@dataclass(frozen=True)
class OnFake[T, F](TypedMatcher[T]):
    """A matcher over an external fake rather than the payload.

    The fake names itself by its class, so what is read off it is checked the way the
    payload is: ``on_fake(FakeStorage, at(lambda s: s.calls, [...]))``.
    """

    fake: type[F]
    matcher: TypedMatcher[F]

    @override
    def mismatches(self, actual: T) -> list[str]:
        raise TypeError("on_fake needs the run's fakes; the runner resolves it")

    @override
    def describe(self) -> str:
        return f"{self.fake.__name__}에서: {self.matcher.describe()}"


@dataclass(frozen=True)
class ActorBound[A, R, I]:
    """A call that cannot be written until the actor is known, because the method takes
    something about the caller beside the request.

    ``I`` is whatever the runner knows about the actor; nothing here says what that is.
    """

    build: Callable[[I], Invocation[A, R]]
    label: str = ""


def needs_actor[A, R, I](
    build: Callable[[I], Invocation[A, R]], label: str = ""
) -> ActorBound[A, R, I]:
    """Say the call needs the actor, and how to make it once the runner supplies one.

    ``label`` names the method for a report, which cannot read it off a call that has
    not been built yet.
    """
    return ActorBound(build, label)


@dataclass(frozen=True)
class Deferred[A, R]:
    """A call that cannot be written until a seeded row exists, because it names
    something the database generated.

    What it builds may itself still need the actor, so a call that wants both the row
    and the caller is one of these too.
    """

    rows: tuple[object, ...]
    build: Callable[..., Invocation[A, R] | ActorBound[A, R, Any]]


# ---------------------------------------------------------------------------
# Checking the whole answer, with the generated fields taken over rather than dropped
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Checked[T, V]:
    """One field the expected value cannot state, checked by a condition instead.

    A generated id or a timestamp is not written into the expected payload, but it is
    not skipped either: whatever the field holds still has to satisfy this.
    """

    select: Callable[[T], V]
    condition: Callable[[V], bool]
    describe: str = ""

    def path(self) -> str:
        return path_of(self.select)

    def failure(self, value: V) -> str:
        wanted = f" ({self.describe})" if self.describe else ""
        return f"{self.path()}: {value!r} does not hold{wanted}"


@dataclass(frozen=True)
class Ignored[T, V]:
    """One field left out of the comparison entirely, with the reason written down.

    For a value whose type is already the whole guarantee: a generated id arrives as an
    id, and how it was generated is the writer's business, not the test's. A field that
    could hold something wrong belongs in :func:`checked` instead.
    """

    select: Callable[[T], V]
    why: str

    def path(self) -> str:
        return path_of(self.select)


type Taken[T] = Checked[T, Any] | Ignored[T, Any]


def _taken_says(rule: Taken[Any]) -> str:
    """What was said about a field the expected value could not state."""
    if isinstance(rule, Ignored):
        return f"{rule.path()} 무시({rule.why})"
    return f"{rule.path()} 조건({rule.describe})" if rule.describe else f"{rule.path()} 조건"


SKEW: Final = timedelta(seconds=30)
"""두 시계가 어긋나 있어도 봐주는 폭."""


def since(start: datetime, *, skew: timedelta = SKEW) -> Callable[[datetime], bool]:
    """``start`` 뒤에, 그리고 지금보다 뒤가 아닌 시각.

    타임스탬프에 거는 조건은 값 자체가 아니라 그 값이 이 실행이 쓴 것인가이다. 시각은
    데이터베이스 서버가 찍고 비교는 이 프로세스가 하므로, 두 시계가 어긋난 만큼은 봐준다.
    """

    def condition(moment: datetime) -> bool:
        if moment.tzinfo is None:
            return False
        return start - skew <= moment <= datetime.now(UTC) + skew

    return condition


def _fields_of(value: object) -> Sequence[str] | None:
    """The field names of a model or dataclass, or ``None`` when it is a plain value."""
    model_fields = getattr(type(value), "model_fields", None)
    if isinstance(model_fields, Mapping):
        return list(model_fields)
    dataclass_fields = getattr(type(value), "__dataclass_fields__", None)
    if isinstance(dataclass_fields, Mapping):
        return list(dataclass_fields)
    return None


def _compare(expected: object, actual: object, path: str, covered: frozenset[str]) -> list[str]:
    """Every field of ``expected`` against ``actual``, the covered paths left out.

    Walks the models rather than dumping them, so a condition further down receives the
    value in its own type: a datetime stays a datetime.
    """
    if path in covered:
        return []
    if type(expected) is not type(actual):
        return [
            f"{path or 'result'}: expected {type(expected).__name__}, got {type(actual).__name__}"
        ]
    names = _fields_of(expected)
    if names is not None:
        out: list[str] = []
        for name in names:
            sub = f"{path}.{name}" if path else name
            out.extend(_compare(getattr(expected, name), getattr(actual, name), sub, covered))
        return out
    if isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        if len(expected) != len(actual):
            return [f"{path}: expected {len(expected)} items, got {len(actual)}"]
        return [
            m
            for i, (e, a) in enumerate(zip(expected, actual, strict=True))
            for m in _compare(e, a, f"{path}[{i}]", covered)
        ]
    if expected != actual:
        return [f"{path or 'result'}: expected {expected!r}, got {actual!r}"]
    return []


@dataclass(frozen=True)
class Exactly[T](TypedMatcher[T]):
    """The whole answer, field by field, with named fields taken over by a condition.

    The default is exhaustive: a field the expected value does not mention is still
    compared, so a payload that grows a field fails until somebody looks at it. The
    fields a test cannot state are named in ``where``: held to a condition, or left out
    with a reason when their type already says everything.
    """

    expected: T
    where: tuple[Taken[T], ...] = ()

    @override
    def mismatches(self, actual: T) -> list[str]:
        covered = frozenset(rule.path() for rule in self.where)
        out = _compare(self.expected, actual, "", covered)
        for rule in self.where:
            if isinstance(rule, Checked):
                value = rule.select(actual)
                if not rule.condition(value):
                    out.append(rule.failure(value))
        return out

    @override
    def describe(self) -> str:
        taken = ", ".join(_taken_says(rule) for rule in self.where)
        return "답 전체 일치" + (f", 다만 {taken}" if taken else "")


@dataclass
class Called:
    """The method the run actually called.

    A call built from a seeded row cannot always be replayed over a stand-in: an input
    model that validates its fields refuses one. The run knows the name regardless, so
    it writes it here as it goes.
    """

    name: str = ""
    shows: tuple[str, ...] = ()


@dataclass(frozen=True)
class TypedScenario[A, C]:
    """A scenario over adapter ``A`` and config ``C``.

    Five parts: what it is called, what it guarantees, who asks, the situation the
    call is made in, and what the call must answer. The result type is checked where
    the row is written and dropped afterwards, so a table of rows returning different
    payloads is still one list.

    The actor is a row like any other: the user the scenario laid down, with whatever
    that user was given. Nothing about them is inherited from a shared background.
    """

    summary: str
    description: str
    invoke: Callable[[A, Sown, Any], Awaitable[Any]]
    then: TypedMatcher[Any] | type[BaseException] | None = None
    actor: object | None = None
    operation: str = ""
    given: Situation[C] = field(default_factory=Situation)
    called: Called = field(default_factory=Called)

    def describe(self) -> ScenarioRecord:
        """What this row says about itself.

        The run fills the rest of the record: where the scenario lived, how it came
        out, what laying its rows established, and what its adapter offers.
        """
        refused = isinstance(self.then, type) and issubclass(self.then, BaseException)
        actor = str(getattr(self.actor, "describe", ""))
        operation = self.called.name or self.operation
        return ScenarioRecord(
            summary=self.summary,
            description=self.description,
            actor=actor,
            caller=str(getattr(self.actor, "name", "")),
            operation=operation,
            when=f"{actor or '호출자'}의 {operation} 호출",
            shows=self.called.shows,
            then=(
                f"거부: {cast(type, self.then).__name__}"
                if refused
                else self.then.describe()
                if isinstance(self.then, TypedMatcher)
                else "호출이 통과한다"
            ),
            config=tuple(f"{path} 설정됨" for path in sorted(self.given.dotted_config())),
        )

    @classmethod
    def ok[R](
        cls,
        summary: str,
        *,
        description: str,
        when: Invocation[A, R] | Deferred[A, R] | ActorBound[A, R, Any],
        then: TypedMatcher[R] | None = None,
        actor: object | None = None,
        given: Situation[C] | None = None,
    ) -> TypedScenario[A, C]:
        called = Called()
        return cls(
            summary,
            _described(description),
            _invoker(when, called),
            then,
            actor,
            _operation_of(when),
            given or Situation(),
            called,
        )

    @classmethod
    def error[R](
        cls,
        summary: str,
        *,
        description: str,
        when: Invocation[A, R] | Deferred[A, R] | ActorBound[A, R, Any],
        then: type[BaseException],
        actor: object | None = None,
        given: Situation[C] | None = None,
    ) -> TypedScenario[A, C]:
        called = Called()
        return cls(
            summary,
            _described(description),
            _invoker(when, called),
            then,
            actor,
            _operation_of(when),
            given or Situation(),
            called,
        )


def _described(description: str) -> str:
    """A row says what it guarantees, in a sentence a reviewer can hold against it."""
    if not description.strip():
        raise ValueError("a scenario must say what it guarantees")
    return description


def _invoker[A, R](
    when: Invocation[A, R] | Deferred[A, R] | ActorBound[A, R, Any],
    called: Called,
) -> Callable[[A, Sown, Any], Awaitable[R]]:
    """One shape for the three kinds of call. The runner hands over what the seeds made
    and what it knows about the actor; each kind takes what it needs."""
    if isinstance(when, Deferred):
        deferred = when

        def run_deferred(adapter: A, sown: Sown, actor: Any) -> Awaitable[R]:
            missing = [row for row in deferred.rows if row not in sown]
            if missing:
                raise LookupError(
                    f"the call reads {missing!r}, which this scenario's set-up does not lay down"
                )
            built = deferred.build(*(sown[row] for row in deferred.rows))
            if isinstance(built, ActorBound):
                invocation = built.build(actor)
            else:
                invocation = built
            called.name = invocation.label
            called.shows = shown_for(invocation, sown)
            return invocation.call(adapter)

        return run_deferred

    if isinstance(when, ActorBound):
        bound = when

        def run_bound(adapter: A, _sown: Sown, actor: Any) -> Awaitable[R]:
            invocation = bound.build(actor)
            called.name = invocation.label
            called.shows = shown_for(invocation, _sown)
            return invocation.call(adapter)

        return run_bound

    invocation = when

    def run(adapter: A, _sown: Sown, _actor: Any) -> Awaitable[R]:
        called.name = invocation.label
        called.shows = shown_for(invocation, _sown)
        return invocation.call(adapter)

    return run


def mismatches_of(matcher: TypedMatcher[Any], answered: Any, fakes: Sequence[object]) -> list[str]:
    """What a matcher says about one answer.

    A matcher over an external fake is resolved here, because only the run knows which
    fakes it wired. The fake is picked out by its class, so a renamed class is a type
    error rather than a run that quietly finds nothing.
    """
    if isinstance(matcher, OnFake):
        for candidate in fakes:
            if isinstance(candidate, matcher.fake):
                return matcher.matcher.mismatches(candidate)
        return [f"{matcher.fake.__name__} was not wired by this run"]
    if isinstance(matcher, All):
        return [m for part in matcher.parts for m in mismatches_of(part, answered, fakes)]
    return matcher.mismatches(answered)


def _deferred_operation[A, R](when: Deferred[A, R]) -> str:
    """The method a deferred call names, recovered by building it over a recorder.

    The call cannot be built until the row exists, but which method it names does not
    depend on the row: replaying the builder over a stand-in answers it.
    """
    try:
        built = when.build(*(_Recorder() for _ in when.rows))
    except Exception:
        return "a call reading a row it laid"
    if isinstance(built, ActorBound):
        return built.label or "a call needing the actor"
    return built.label


def _operation_of(when: object) -> str:
    """The name of the method a row calls, for the report.

    A deferred or actor-bound call is built later, so the name is not reachable until
    then; those say what kind of call they are instead.
    """
    if isinstance(when, Invocation):
        return when.label
    if isinstance(when, Deferred):
        return _deferred_operation(when)
    if isinstance(when, ActorBound):
        return when.label or "a call needing the actor"
    return ""
