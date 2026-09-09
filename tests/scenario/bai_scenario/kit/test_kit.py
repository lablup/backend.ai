"""The kit's own tests: matchers, the runner's dispatch, and what the World seeded."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest
import sqlalchemy as sa
from bai_kit.manager.db import TemplateDatabase
from bai_kit.manager.monitors import ActionRecorder
from bai_kit.manager.personas import ALL_PERSONAS, MEMBER, SUPERADMIN
from bai_kit.manager.runner import AdapterRunner, Wired, WiringDeps
from bai_kit.manager.typed import (
    At,
    Checked,
    Every,
    Exactly,
    at,
    checked,
    every,
    exactly,
    path_of,
)

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
    each,
    has,
    length,
    mismatches_for,
    on_extra,
    scenario_id,
    snapshot,
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


# --- runner dispatch (no database: a stand-in adapter) --------------------------------


@dataclass
class _Body:
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
            await runner(Scenario.ok("nope", when=_Inner("a", 1)))

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
