"""Running one typed scenario against an adapter the fixtures already built.

The runner knows nothing about which component it is running. It lays the rows the
scenario named — the actor among them — makes the call as that actor, and checks the
answer. Every row is written in one session, and a row several others rest on is
written once.
"""

from __future__ import annotations

import inspect
from collections.abc import Sequence
from typing import Any

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_report import Line
from ai.backend.testutils.typed_scenario import (
    TypedMatcher,
    TypedScenario,
    mismatches_of,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.seeds.ops import SeedOpsProvider
from bai_scenario.seeds.seeder import Laid, laid_in_order, lay


class NoActor(Exception):
    """The scenario made a call that needs a caller and named no actor."""


class ScenarioRunner:
    """Run a :class:`TypedScenario` against one adapter with a real database."""

    def __init__(
        self,
        adapter: Any,
        engine: ExtendedAsyncSAEngine,
        fakes: Sequence[object] = (),
    ) -> None:
        self._adapter = adapter
        self._engine = engine
        self._fakes = fakes

    async def _lay(self, scenario: TypedScenario[Any, Any]) -> dict[Laid[Any], Any]:
        wanted = [row for row in scenario.given.rows if isinstance(row, Laid)]
        if isinstance(scenario.actor, Laid):
            wanted.append(scenario.actor)
        made: dict[Laid[Any], Any] = {}
        async with SeedOpsProvider(self._engine).write_ops() as ops:
            await lay(ops, wanted, made)
        return made

    async def __call__(self, scenario: TypedScenario[Any, Any]) -> None:
        made = await self._lay(scenario)
        actor = made.get(scenario.actor) if isinstance(scenario.actor, Laid) else None
        try:
            if actor is None:
                answered = await scenario.invoke(self._adapter, made, None)
            else:
                with ActingAs(actor) as who:
                    answered = await scenario.invoke(self._adapter, made, who)
        except Exception as raised:
            self._check_raised(scenario, raised)
            return
        self._check_answered(scenario, answered)

    def _check_raised(self, scenario: TypedScenario[Any, Any], raised: Exception) -> None:
        expected = scenario.then
        if not isinstance(expected, type) or not issubclass(expected, BaseException):
            raise raised
        if not isinstance(raised, expected):
            raise AssertionError(
                f"[{scenario.summary}] expected {expected.__name__}, "
                f"got {type(raised).__name__}: {raised}"
            ) from raised

    def _check_answered(self, scenario: TypedScenario[Any, Any], answered: Any) -> None:
        expected = scenario.then
        if isinstance(expected, type) and issubclass(expected, BaseException):
            raise AssertionError(
                f"[{scenario.summary}] expected {expected.__name__} "
                f"but the call answered {answered!r}"
            )
        if expected is None:
            return
        problems = mismatches_of(expected, answered, self._fakes)
        if problems:
            raise AssertionError(f"[{scenario.summary}] " + "; ".join(problems))


def scenario_given(scenario: TypedScenario[Any, Any]) -> tuple[Line, ...]:
    """What is already true when the call is made, in the order it was laid."""
    wanted = [row for row in scenario.given.rows if isinstance(row, Laid)]
    if isinstance(scenario.actor, Laid):
        wanted.append(scenario.actor)
    return tuple(Line(says=row.states, nest=row.nest) for row in laid_in_order(wanted))


def offered_by(adapter: object) -> frozenset[str]:
    """Every call the adapter offers, read off the class rather than listed.

    The report subtracts what the scenarios exercised from this, so a method no row
    reaches is named by the run instead of going unnoticed.
    """
    return frozenset(
        name
        for name, member in inspect.getmembers(type(adapter), inspect.isfunction)
        if not name.startswith("_") and inspect.iscoroutinefunction(member)
    )


def typed_matcher_problems(matcher: TypedMatcher[Any], answered: Any) -> list[str]:
    """What a matcher says about one answer, for the surface's own tests."""
    return matcher.mismatches(answered)
