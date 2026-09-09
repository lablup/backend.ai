"""The manager kit's own tests: what the runner dispatches, and what the World seeded.

Both need the scenario tree's database fixtures, which is why they live here rather
than beside the generic surface in ``tests/unit/testutils``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
import sqlalchemy as sa
from bai_kit.manager.db import TemplateDatabase
from bai_kit.manager.monitors import ActionRecorder
from bai_kit.manager.personas import ALL_PERSONAS, MEMBER, SUPERADMIN
from bai_kit.manager.runner import AdapterRunner, Wired, WiringDeps

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow, ProjectType
from ai.backend.manager.models.user.row import UserRow
from ai.backend.testutils.scenario import (
    Call,
    Scenario,
    Step,
    all_of,
    contains,
    has,
    on_extra,
    scenario_id,
)

# --- runner dispatch (no database: a stand-in adapter) --------------------------------


@dataclass
class _Body:
    value: str


@dataclass
class _Unwired:
    """A value no wiring names, so the runner has to say so rather than guess."""

    value: str


class _StandInAdapter:
    def __init__(self) -> None:
        self.seen: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    async def create(self, body: _Body, user_info: Any) -> dict[str, Any]:
        self.seen.append(("create", (body,), {"user_info": user_info}))
        return {"value": body.value, "actor": current_user()}

    async def get(self, name: str) -> dict[str, Any]:
        self.seen.append(("get", (name,), {}))
        return {"value": name}


def _stand_in_wiring(deps: WiringDeps) -> Wired:
    adapter = _StandInAdapter()
    return Wired(
        adapter=adapter,
        dispatch={_Body: "create"},
        client_attr="none",
        extras={"seen": adapter.seen},
    )


class TestRunnerDispatch:
    @pytest.fixture
    def runner(self, world_template: TemplateDatabase, engine: Any) -> AdapterRunner:
        # The stand-in adapter never reads the engine; a real one is passed anyway so
        # nothing here has to be declared as something it is not.
        return AdapterRunner(
            wiring=_stand_in_wiring,
            engine=engine,
            world=world_template.world,
            base_config={},
            recorder=ActionRecorder(),
        )

    async def test_dto_picks_the_method_and_injects_user_info(self, runner: AdapterRunner) -> None:
        await runner(
            Scenario.ok(
                "dto",
                actor=MEMBER,
                when=_Body("v"),
                then=all_of(
                    has(value="v", actor=has(is_superadmin=False)),
                    on_extra(
                        "seen",
                        contains(lambda s: s[0] == "create" and s[2]["user_info"].role == "user"),
                    ),
                ),
            )
        )

    async def test_call_names_the_method(self, runner: AdapterRunner) -> None:
        await runner(Scenario.ok("call", when=Call("get", "n"), then=has(value="n")))

    async def test_unknown_dto_is_a_clear_error(self, runner: AdapterRunner) -> None:
        with pytest.raises(KeyError, match="name it with Call"):
            await runner(Scenario.ok("nope", when=_Unwired("a")))

    async def test_flow_feeds_previous_results(self, runner: AdapterRunner) -> None:
        await runner(
            Scenario.flow(
                "flow",
                steps=[
                    Step(_Body("first"), has(value="first")),
                    Step(
                        lambda ctx: Call("get", ctx.prev["value"] + "-next"),
                        has(value="first-next"),
                    ),
                ],
            )
        )

    async def test_expected_error_that_does_not_happen_fails(self, runner: AdapterRunner) -> None:
        with pytest.raises(AssertionError, match="expected KeyError"):
            await runner(Scenario.error("no-error", when=Call("get", "n"), then=KeyError))

    def test_scenario_ids_are_the_pytest_ids(self) -> None:
        assert scenario_id(Scenario.ok("member-sees-own", when=None)) == "member-sees-own"


# --- World seed --------------------------------------------------------------------------


class TestWorldSeed:
    async def test_every_persona_has_user_default_keypair_and_personal_project(
        self, world_template: TemplateDatabase, engine: Any
    ) -> None:
        world = world_template.world
        async with engine.begin_readonly_session() as sess:
            for persona in ALL_PERSONAS:
                seeded = world.users[persona]
                user = await sess.scalar(sa.select(UserRow).where(UserRow.uuid == seeded.id))
                assert user is not None and user.domain_name == world.domain_name
                keypair = await sess.scalar(
                    sa.select(KeyPairRow).where(KeyPairRow.user == seeded.id, KeyPairRow.is_default)
                )
                assert keypair is not None and keypair.access_key == seeded.access_key
                personal = await sess.scalar(
                    sa.select(sa.func.count())
                    .select_from(ProjectRow)
                    .where(
                        ProjectRow.creator_id == seeded.id, ProjectRow.type == ProjectType.PERSONAL
                    )
                )
                assert personal == 1

    async def test_the_world_holds_exactly_one_domain(self, engine: Any) -> None:
        async with engine.begin_readonly_session() as sess:
            names = (await sess.scalars(sa.select(DomainRow.name))).all()
        assert names == ["default"]

    async def test_superadmin_persona_is_a_superadmin(
        self, world_template: TemplateDatabase
    ) -> None:
        assert world_template.world.users[SUPERADMIN].role == "superadmin"
