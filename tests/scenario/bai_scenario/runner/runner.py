"""Running one typed scenario against an adapter the fixtures already built.

The runner knows nothing about which component it is running: it lays the rows the
situation names, makes the call as the actor, and checks the answer. How the adapter
was assembled is the component's own fixture.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai.backend.common.contexts.user import with_user
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.scenario import Persona
from ai.backend.testutils.typed_scenario import (
    Seed,
    TypedMatcher,
    TypedScenario,
    mismatches_of,
)
from bai_scenario.infra.monitors import ActionRecorder
from bai_scenario.infra.personas import SUPERADMIN, user_data, user_info
from bai_scenario.infra.world import World
from bai_scenario.seeds.seeding import SeedRoom


class ScenarioRunner:
    """Run a :class:`TypedScenario` against one adapter with a real database."""

    def __init__(
        self,
        adapter: Any,
        engine: ExtendedAsyncSAEngine,
        world: World,
        recorder: ActionRecorder,
        fakes: Sequence[object] = (),
        default_actor: Persona = SUPERADMIN,
    ) -> None:
        self._adapter = adapter
        self._engine = engine
        self._world = world
        self._recorder = recorder
        self._fakes = fakes
        self._default_actor = default_actor

    def _room(self) -> SeedRoom:
        ops: OpsRepository[Any] = OpsRepository(V2DBOpsProvider(self._engine))
        return SeedRoom(engine=self._engine, world=self._world, ops=ops)

    async def _hand_over(self, scenario: TypedScenario[Any, Any], actor: Persona) -> None:
        """Give the actor what the scenario says they hold, before any row is laid."""
        room = self._room()
        for item in scenario.holding:
            await item.apply(room, item.holder or actor)

    async def _sow(
        self, scenario: TypedScenario[Any, Any], actor: Persona
    ) -> dict[Seed[Any, Any], Any]:
        room = self._room()
        sown: dict[Seed[Any, Any], Any] = {}
        for seed in scenario.given.rows():
            owner = seed.owner or actor
            with with_user(user_data(self._world, owner)):
                sown[seed] = await seed.make(room)
        return sown

    async def __call__(self, scenario: TypedScenario[Any, Any]) -> None:
        actor = scenario.actor or self._default_actor
        await self._hand_over(scenario, actor)
        sown = await self._sow(scenario, actor)
        with with_user(user_data(self._world, actor)):
            try:
                answered = await scenario.invoke(self._adapter, sown, user_info(self._world, actor))
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


def typed_matcher_problems(matcher: TypedMatcher[Any], answered: Any) -> list[str]:
    """What a matcher says about one answer, for the surface's own tests."""
    return matcher.mismatches(answered)
