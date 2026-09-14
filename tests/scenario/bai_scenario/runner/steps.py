"""세 단계 시나리오를 도는 자리.

`given`을 돌려 값을 받고, 그 값으로 `when`을 돌리고, 답이든 예외든 `then`에 넘긴다.

`given`의 쓰기는 `when`이 시작되기 전에 닫힌다. 어댑터는 자기 연결로 읽으므로, 열린 채로
두면 심은 행을 보지 못한다.
"""

from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from typing import Any

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_report import Line, ScenarioRecord
from ai.backend.testutils.scenario_steps import Answered, Scenario, Told
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.seeds.ops import SeedOpsProvider
from bai_scenario.seeds.seeder import Seeder


def offered_by(adapter: object) -> frozenset[str]:
    """어댑터가 내놓는 호출 전부. 클래스에서 직접 읽는다.

    레포트가 여기서 실행이 부른 것을 빼므로, 아무도 부르지 않는 호출을 손으로 관리하는
    목록과 견주지 않는다.
    """
    return frozenset(
        name
        for name, member in inspect.getmembers(type(adapter), inspect.isfunction)
        if not name.startswith("_") and inspect.iscoroutinefunction(member)
    )


@dataclass(frozen=True)
class ScenarioRun:
    """한 시나리오가 실제로 무엇을 했는지, 단계별로."""

    given: Told
    when: Told
    then: Told

    def problems(self) -> list[str]:
        return self.then.every_problem()

    def lines(self) -> list[str]:
        out = ["Given"]
        out.extend(self.given.lines())
        out.extend(["", "When", *self.when.lines()])
        out.extend(["", "Then", *self.then.lines()])
        return out


async def run_scenario(
    scenario: Scenario[SeedingSession, Any, Any, Any], adapter: Any, engine: ExtendedAsyncSAEngine
) -> ScenarioRun:
    """세 단계를 순서대로 돌고, 어긋난 것이 있으면 그 자리에서 세운다."""
    given = scenario.given()
    async with SeedOpsProvider(engine).write_ops() as ops:
        seeding = SeedingSession(Seeder(), ops)
        laid = await given.lay(seeding)
        laid_told = Told(given.describe(), within=seeding.told())

    when = scenario.when()
    try:
        response = await when.call(adapter, laid)
    except Exception as raised:
        answered: Answered[Any] = Answered(raised=raised)
    else:
        answered = Answered(response=response)

    then = scenario.then()
    run = ScenarioRun(
        given=laid_told,
        when=Told(when.describe(laid)),
        then=then.told(laid, answered),
    )
    problems = run.problems()
    _record(scenario, run, adapter, failed=bool(problems))
    if problems:
        raise AssertionError(f"[{scenario.summary()}] " + "; ".join(problems))
    return run


def _flatten(told: Told, *, skip_root: bool = False) -> tuple[Line, ...]:
    """말한 것을 줄로 편다. 어느 묶음 아래였는지는 줄이 들고 간다."""
    out: list[Line] = []

    def walk(one: Told, nest: tuple[str, ...]) -> None:
        if one.within:
            for child in one.within:
                walk(child, nest + (one.says,))
        else:
            out.append(Line(says=one.says, nest=nest))

    if skip_root:
        for child in told.within:
            walk(child, ())
    else:
        walk(told, ())
    return tuple(out)


def _record(
    scenario: Scenario[SeedingSession, Any, Any, Any],
    run: ScenarioRun,
    adapter: Any,
    *,
    failed: bool,
) -> None:
    """이 행이 무엇을 했는지 한 줄로 남긴다. 남길 자리가 없으면 남기지 않는다."""
    path = os.environ.get("BACKEND_SCENARIO_LOG")
    if path is None:
        return
    record = ScenarioRecord(
        summary=scenario.summary(),
        description=scenario.describe(),
        actor="",
        caller="",
        operation=scenario.when().operation(),
        when=run.when.says,
        then=run.then.says,
        module=type(scenario).__module__,
        outcome="failed" if failed else "passed",
        adapter=type(adapter).__name__,
        given=_flatten(run.given),
        seen=_flatten(run.then, skip_root=True),
        offers=tuple(sorted(offered_by(adapter))),
    )
    with open(path, "a", encoding="utf8") as f:
        f.write(record.as_line() + "\n")
