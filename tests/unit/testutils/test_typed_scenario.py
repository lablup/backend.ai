"""The scenario surface's own tests: matchers and comparison, with no database.

What is checked here belongs to ``ai.backend.testutils.typed_scenario`` and knows no
component. The parts that need the manager's world are tested beside the kit.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from ai.backend.testutils.scenario import (
    all_of,
    contains,
    each,
    has,
    length,
    mismatches_for,
    on_extra,
    snapshot,
)
from ai.backend.testutils.typed_scenario import (
    At,
    Checked,
    Every,
    Exactly,
    Ignored,
    at,
    checked,
    every,
    exactly,
    ignored,
    path_of,
    recent,
)

# --- matchers ------------------------------------------------------------------------


@dataclass
class _Inner:
    name: str
    n: int


@dataclass
class _Outer:
    inner: _Inner
    items: list[_Inner]


def _outer() -> _Outer:
    return _Outer(_Inner("a", 1), [_Inner("x", 1), _Inner("y", 2)])


class TestMatchers:
    def test_has_matches_named_fields_only(self) -> None:
        assert has(inner=has(name="a")).mismatches(_outer()) == []

    def test_has_reports_every_mismatch_with_a_path(self) -> None:
        problems = has(inner=has(name="b", n=2)).mismatches(_outer())
        assert problems == ["inner.name: expected 'b', got 'a'", "inner.n: expected 2, got 1"]

    def test_has_reports_missing_field(self) -> None:
        assert has(nope=1).mismatches(_outer()) == ["nope: missing on _Outer"]

    def test_each_contains_length(self) -> None:
        assert has(items=each(has(n=lambda v: v >= 1))).mismatches(_outer()) == []
        assert has(items=contains(has(name="y"))).mismatches(_outer()) == []
        assert has(items=length(2)).mismatches(_outer()) == []
        assert has(items=contains(has(name="z"))).mismatches(_outer())[0].startswith("items:")

    def test_snapshot_strips_volatile_paths(self) -> None:
        got = {"a": {"id": "random", "name": "n"}, "b": 1}
        assert snapshot({"a": {"name": "n"}, "b": 1}, volatile=("a.id",)).mismatches(got) == []
        assert snapshot({"a": {"name": "m"}, "b": 1}, volatile=("a.id",)).mismatches(got)

    def test_on_extra_reads_the_named_extra(self) -> None:
        then = all_of(has(inner=has(name="a")), on_extra("fake", has(items=length(1))))
        extras: dict[str, Any] = {"fake": _Outer(_Inner("f", 0), [_Inner("c", 1)])}
        assert mismatches_for(then, _outer(), extras) == []
        assert mismatches_for(on_extra("missing", has()), _outer(), extras)[0].startswith("extra")


# --- typed matchers: the accessor is read twice, for the value and for the path -------
# Written outside a scenario, an accessor has no position to read its parameter type
# from, so each matcher below is annotated. Inside a table the ``when`` supplies it.


class TestTypedMatchers:
    def test_path_is_recovered_from_the_accessor(self) -> None:
        select: Callable[[_Outer], object] = lambda o: o.inner.name
        assert path_of(select) == "inner.name"

    def test_at_reports_the_path_it_read(self) -> None:
        matcher: At[_Outer, str] = at(lambda o: o.inner.name, "b")
        assert matcher.mismatches(_outer()) == ["inner.name: expected 'b', got 'a'"]

    def test_at_passes_when_the_value_matches(self) -> None:
        matcher: At[_Outer, int] = at(lambda o: o.inner.n, 1)
        assert matcher.mismatches(_outer()) == []

    def test_every_reports_the_index_and_the_field(self) -> None:
        item: At[_Inner, int] = at(lambda i: i.n, 1)
        matcher: Every[_Outer, _Inner] = every(lambda o: o.items, item)
        assert matcher.mismatches(_outer()) == ["items[1].n: expected 1, got 2"]

    def test_a_computed_accessor_still_answers_a_path(self) -> None:
        select: Callable[[_Outer], object] = lambda o: len(o.items)
        assert path_of(select) == "<computed>"


# --- exhaustive comparison: everything is compared unless a condition takes it over ---


@dataclass
class _Stamped:
    name: str
    n: int
    at: datetime


_MOMENT = datetime.now(UTC)


class TestExactly:
    def test_a_full_match_passes(self) -> None:
        moment = datetime.now(UTC)
        matcher: Exactly[_Stamped] = exactly(_Stamped("a", 1, moment))
        assert matcher.mismatches(_Stamped("a", 1, moment)) == []

    def test_a_field_the_expected_value_got_wrong_is_reported(self) -> None:
        moment = datetime.now(UTC)
        matcher: Exactly[_Stamped] = exactly(_Stamped("a", 2, moment))
        assert matcher.mismatches(_Stamped("a", 1, moment)) == ["n: expected 2, got 1"]

    def test_a_generated_field_is_taken_over_by_a_condition_not_ignored(self) -> None:
        rule: Checked[_Stamped, datetime] = checked(
            lambda s: s.at, lambda t: t.tzinfo is not None, "an aware moment"
        )
        matcher: Exactly[_Stamped] = exactly(_Stamped("a", 1, datetime.now(UTC)), where=(rule,))
        # A different moment passes, because the condition is what is checked.
        assert matcher.mismatches(_Stamped("a", 1, datetime.now(UTC))) == []

    def test_a_taken_over_field_that_fails_its_condition_is_reported(self) -> None:
        rule: Checked[_Stamped, datetime] = checked(
            lambda s: s.at, lambda t: t.tzinfo is not None, "an aware moment"
        )
        matcher: Exactly[_Stamped] = exactly(_Stamped("a", 1, datetime.now(UTC)), where=(rule,))
        naive = datetime.now(UTC).replace(tzinfo=None)
        problems = matcher.mismatches(_Stamped("a", 1, naive))
        assert len(problems) == 1
        assert problems[0].startswith("at: ")
        assert problems[0].endswith("does not hold (an aware moment)")

    def test_every_other_field_is_still_compared_while_one_is_taken_over(self) -> None:
        rule: Checked[_Stamped, datetime] = checked(lambda s: s.at, lambda t: True)
        matcher: Exactly[_Stamped] = exactly(_Stamped("a", 1, datetime.now(UTC)), where=(rule,))
        naive = datetime.now(UTC).replace(tzinfo=None)
        assert matcher.mismatches(_Stamped("b", 1, naive)) == ["name: expected 'a', got 'b'"]

    def test_a_field_can_be_left_out_with_a_reason(self) -> None:
        rule: Ignored[_Stamped, int] = ignored(lambda s: s.n, "assigned by the writer")
        matcher: Exactly[_Stamped] = exactly(_Stamped("a", 1, _MOMENT), where=(rule,))
        # A different n passes; nothing else does.
        assert matcher.mismatches(_Stamped("a", 99, _MOMENT)) == []
        assert matcher.mismatches(_Stamped("b", 99, _MOMENT)) == ["name: expected 'a', got 'b'"]

    def test_recent_accepts_now_and_refuses_a_naive_or_old_moment(self) -> None:
        condition = recent(timedelta(minutes=1))
        assert condition(datetime.now(UTC)) is True
        assert condition(datetime.now(UTC).replace(tzinfo=None)) is False
        assert condition(datetime.now(UTC) - timedelta(days=1)) is False
        assert condition(datetime.now(UTC) + timedelta(days=1)) is False
