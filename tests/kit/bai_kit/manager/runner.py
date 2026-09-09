"""The adapter runner: a Scenario in, processors assembled fresh, one adapter call out.

The wiring a test file hands over says how to build its domain's adapter; the runner
supplies what every domain needs the same way (config, validators, monitors, actor).
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from pydantic import BaseModel

from ai.backend.common.contexts.user import with_user
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.testutils.scenario import (
    Call,
    Persona,
    Scenario,
    Step,
    StepContext,
    check_raised,
    check_then,
)
from bai_kit.manager.config import KitConfigProvider, make_config
from bai_kit.manager.monitors import ActionRecorder
from bai_kit.manager.personas import SUPERADMIN, user_data, user_info
from bai_kit.manager.validators import build_action_validators
from bai_kit.manager.world import World


@dataclass
class WiringDeps:
    """What a domain wiring gets to build its adapter from."""

    engine: ExtendedAsyncSAEngine
    world: World
    config_provider: ManagerConfigProvider
    validators: ActionValidators
    v2_validators: V2ActionValidators
    monitors: ActionMonitors
    extras: Mapping[str, Any]


@dataclass
class Wired:
    """One domain, assembled for one run."""

    adapter: Any
    # ``when`` DTO type -> adapter method name. Anything else goes through ``Call``.
    dispatch: Mapping[type, str]
    # The SDK v2 registry attribute the HTTP runner calls the same methods on.
    client_attr: str
    # External fakes a ``then`` may inspect through ``on_extra``.
    extras: dict[str, Any] = field(default_factory=dict)


class Wiring(Protocol):
    def __call__(self, deps: WiringDeps) -> Wired: ...


@dataclass
class SeedContext:
    engine: ExtendedAsyncSAEngine
    world: World
    ops: OpsRepository[Any]
    actor: Persona
    seeded: dict[str, Any]


class AdapterRunner:
    """Run a scenario against the transport-agnostic adapter with a real database."""

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

    def assemble(self, scenario: Scenario) -> tuple[Wired, ManagerConfigProvider]:
        config_provider = KitConfigProvider(make_config(self._base_config, scenario.setup.config))
        validators, v2_validators = build_action_validators(
            PermissionControllerRepository(self._engine), config_provider
        )
        wired = self._wiring(
            WiringDeps(
                engine=self._engine,
                world=self._world,
                config_provider=config_provider,
                validators=validators,
                v2_validators=v2_validators,
                monitors=self._recorder.monitors(),
                extras=scenario.setup.extras,
            )
        )
        return wired, config_provider

    async def __call__(self, scenario: Scenario) -> None:
        wired, _ = self.assemble(scenario)
        ctx = StepContext()
        await self.seed(scenario, ctx)
        for step in scenario.all_steps(self.name):
            await self._run_step(scenario, step, ctx, wired)

    async def seed(self, scenario: Scenario, ctx: StepContext) -> None:
        ops: OpsRepository[Any] = OpsRepository(V2DBOpsProvider(self._engine))
        for seed in scenario.given:
            owner = seed.owner or scenario.actor or self._default_actor
            with with_user(user_data(self._world, owner)):
                ctx.seeded[seed.label] = await seed.build(
                    SeedContext(self._engine, self._world, ops, owner, ctx.seeded)
                )

    def resolve_when(self, step: Step, ctx: StepContext) -> Any:
        when = step.when
        if callable(when) and not isinstance(when, (BaseModel, Call)):
            return when(ctx)
        return when

    async def invoke(self, wired: Wired, when: Any, actor: Persona) -> Any:
        if isinstance(when, Call):
            method = getattr(wired.adapter, when.method)
            args: tuple[Any, ...] = when.args
            kwargs: dict[str, Any] = dict(when.kwargs)
        else:
            name = wired.dispatch.get(type(when))
            if name is None:
                raise KeyError(
                    f"{type(wired.adapter).__name__} has no method for {type(when).__name__}; "
                    "name it with Call(...)"
                )
            method = getattr(wired.adapter, name)
            args, kwargs = (when,), {}
        if "user_info" in inspect.signature(method).parameters and "user_info" not in kwargs:
            kwargs["user_info"] = user_info(self._world, actor)
        return await method(*args, **kwargs)

    async def _run_step(
        self, scenario: Scenario, step: Step, ctx: StepContext, wired: Wired
    ) -> None:
        actor = step.actor or scenario.actor or self._default_actor
        when = self.resolve_when(step, ctx)
        with with_user(user_data(self._world, actor)):
            try:
                result = await self.invoke(wired, when, actor)
            except Exception as e:
                check_raised(step.then, e, scenario.id)
                ctx.results.append(e)
                return
        check_then(step.then, result, scenario.id, wired.extras)
        ctx.results.append(result)
