"""Running a typed scenario: seeds, situation, the call, and what it must answer.

The string-keyed runner beside this one takes a method name and a field name as text.
This one takes what the type checker already agreed to, so a scenario that reaches the
runner has had its call, its arguments and its expectation checked at import.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ai.backend.common.contexts.user import with_user
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.testutils.scenario import Persona
from ai.backend.testutils.typed_scenario import TypedMatcher, TypedScenario, mismatches_of
from bai_kit.manager.config import KitConfigProvider, make_config
from bai_kit.manager.monitors import ActionRecorder
from bai_kit.manager.personas import SUPERADMIN, user_data, user_info
from bai_kit.manager.runner import Wired, Wiring, WiringDeps
from bai_kit.manager.validators import build_action_validators
from bai_kit.manager.world import World


class TypedRunner:
    """Run a :class:`TypedScenario` against the adapter with a real database."""

    name = "adapter"

    def __init__(
        self,
        wiring: Wiring,
        engine: ExtendedAsyncSAEngine,
        world: World,
        base_config: Mapping[str, Any],
        recorder: ActionRecorder,
        default_actor: Persona = SUPERADMIN,
    ) -> None:
        self._wiring = wiring
        self._engine = engine
        self._world = world
        self._base_config = base_config
        self._recorder = recorder
        self._default_actor = default_actor

    def _assemble(self, scenario: TypedScenario[Any, Any]) -> Wired:
        config_provider = KitConfigProvider(
            make_config(self._base_config, scenario.setup.dotted_config())
        )
        validators, v2_validators = build_action_validators(
            PermissionControllerRepository(self._engine), config_provider
        )
        return self._wiring(
            WiringDeps(
                engine=self._engine,
                world=self._world,
                config_provider=config_provider,
                validators=validators,
                v2_validators=v2_validators,
                monitors=self._recorder.monitors(),
                extras={"answers": list(scenario.setup.answers)},
            )
        )

    async def _sow(self, scenario: TypedScenario[Any, Any], actor: Persona) -> dict[str, Any]:
        ops: OpsRepository[Any] = OpsRepository(V2DBOpsProvider(self._engine))
        sown: dict[str, Any] = {}
        for seed in scenario.given:
            owner = seed.owner or actor
            with with_user(user_data(self._world, owner)):
                sown[seed.label] = await seed.make(ops)
        return sown

    async def __call__(self, scenario: TypedScenario[Any, Any]) -> None:
        wired = self._assemble(scenario)
        actor = scenario.actor or self._default_actor
        sown = await self._sow(scenario, actor)
        with with_user(user_data(self._world, actor)):
            try:
                answered = await scenario.invoke(wired.adapter, sown, user_info(self._world, actor))
            except Exception as raised:
                self._check_raised(scenario, raised)
                return
        self._check_answered(scenario, answered, wired)

    def _check_raised(self, scenario: TypedScenario[Any, Any], raised: Exception) -> None:
        expected = scenario.then
        if not isinstance(expected, type) or not issubclass(expected, BaseException):
            raise raised
        if not isinstance(raised, expected):
            raise AssertionError(
                f"[{scenario.id}] expected {expected.__name__}, "
                f"got {type(raised).__name__}: {raised}"
            ) from raised

    def _check_answered(
        self, scenario: TypedScenario[Any, Any], answered: Any, wired: Wired
    ) -> None:
        expected = scenario.then
        if isinstance(expected, type) and issubclass(expected, BaseException):
            raise AssertionError(
                f"[{scenario.id}] expected {expected.__name__} but the call answered {answered!r}"
            )
        if expected is None:
            return
        problems = mismatches_of(expected, answered, wired.extras)
        if problems:
            raise AssertionError(f"[{scenario.id}] " + "; ".join(problems))


def typed_matcher_problems(matcher: TypedMatcher[Any], answered: Any) -> list[str]:
    """What a matcher says about one answer, for the kit's own tests."""
    return matcher.mismatches(answered)
