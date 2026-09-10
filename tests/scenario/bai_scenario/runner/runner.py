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

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.data.domain.types import UserInfo
from ai.backend.manager.data.user.types import UserData as SeededUser
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.typed_scenario import TypedMatcher, TypedScenario, mismatches_of
from bai_scenario.seeds.ops import SeedOpsProvider
from bai_scenario.seeds.seeder import Given, lay, steps_of


class NoActor(Exception):
    """The scenario made a call that needs a caller and named no actor."""


def _context_of(user: SeededUser) -> UserData:
    """What ``with_user`` needs: the request-context view of the user the row laid."""
    return UserData(
        user_id=user.id,
        is_authorized=True,
        is_admin=user.role in (UserRole.ADMIN, UserRole.SUPERADMIN),
        is_superadmin=user.role == UserRole.SUPERADMIN,
        role=user.role,
        domain_name=user.domain_name,
        domain_id=user.domain_id,
    )


def _info_of(user: SeededUser) -> UserInfo:
    """What an adapter method taking the caller beside the DTO wants."""
    return UserInfo(id=user.id, role=user.role, domain_name=user.domain_name)


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

    async def _lay(self, scenario: TypedScenario[Any, Any]) -> dict[Given[Any], Any]:
        wanted = [row for row in scenario.given.rows if isinstance(row, Given)]
        if isinstance(scenario.actor, Given):
            wanted.append(scenario.actor)
        async with SeedOpsProvider(self._engine).write_ops() as ops:
            return await lay(ops, wanted)

    async def __call__(self, scenario: TypedScenario[Any, Any]) -> None:
        made = await self._lay(scenario)
        actor = made.get(scenario.actor) if isinstance(scenario.actor, Given) else None
        try:
            if actor is None:
                answered = await scenario.invoke(self._adapter, made, None)
            else:
                with with_user(_context_of(actor)):
                    answered = await scenario.invoke(self._adapter, made, _info_of(actor))
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


def scenario_steps(scenario: TypedScenario[Any, Any]) -> list[str]:
    """What laying this scenario's rows does, in order, for the report."""
    wanted = [row for row in scenario.given.rows if isinstance(row, Given)]
    if isinstance(scenario.actor, Given):
        wanted.append(scenario.actor)
    return steps_of(wanted)


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
