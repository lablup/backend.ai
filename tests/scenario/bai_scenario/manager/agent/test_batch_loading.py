"""에이전트를 이름이나 id 로 한 번에 읽기 — 자리마다 노드, 거부, 빈 값이 온다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.dto.manager.v2.agent.response import AgentNode
from ai.backend.common.types import AgentId
from ai.backend.manager.api.adapters.agent.adapter import AgentAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Given,
    Says,
    Scenario,
    Then,
    When,
)
from bai_scenario.components.agent import (
    UNKNOWN_AGENT,
    AgentsAndACaller,
    AgentsAndSomeone,
    TheAgentsComeBackInOrder,
    TheContainerCountsComeBack,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MISSING = UUID(int=9)
"""어떤 에이전트도 갖지 않은 id."""

type Loaded = list[AgentNode | Exception | None]
type Counted = list[int | Exception]
type LoadStep = Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, Loaded]
type CountStep = Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, Counted]


@dataclass(frozen=True)
class LoadingByIds(When[AgentsAndACaller, AgentAdapter, Loaded]):
    """미리 등록한 에이전트들의 이름을 한 번에 읽는다. ``unknown`` 이면 없는 이름을 뒤에 붙인다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AgentsAndACaller) -> str:
        ordered = (*laid.agents, *laid.unreadable)
        if self.unknown:
            return Says(
                f"{laid.caller.username}이 에이전트 {len(ordered)}개의 이름과 없는 이름 하나를 "
                "한 번에 조회합니다",
                english=(
                    f"{laid.caller.username} loads the names of {len(ordered)} agents and one "
                    "unknown name at once"
                ),
            )
        return Says(
            f"{laid.caller.username}이 에이전트 {len(ordered)}개의 이름을 한 번에 조회합니다",
            english=f"{laid.caller.username} loads the names of {len(ordered)} agents at once",
        )

    @override
    async def call(self, adapter: AgentAdapter, laid: AgentsAndACaller) -> Loaded:
        ids = [AgentId(agent.agent_id) for agent in (*laid.agents, *laid.unreadable)]
        if self.unknown:
            ids.append(AgentId(UNKNOWN_AGENT))
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class LoadingByUuids(When[AgentsAndACaller, AgentAdapter, Loaded]):
    """미리 등록한 에이전트들의 id 를 한 번에 읽는다. ``unknown`` 이면 없는 id 를 뒤에 붙인다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_by_uuids"

    @override
    def describe(self, laid: AgentsAndACaller) -> str:
        ordered = (*laid.agents, *laid.unreadable)
        if self.unknown:
            return Says(
                f"{laid.caller.username}이 에이전트 {len(ordered)}개의 id 와 없는 id 하나를 한 "
                "번에 조회합니다",
                english=(
                    f"{laid.caller.username} loads the ids of {len(ordered)} agents and one "
                    "unknown id at once"
                ),
            )
        return Says(
            f"{laid.caller.username}이 에이전트 {len(ordered)}개의 id 를 한 번에 조회합니다",
            english=f"{laid.caller.username} loads the ids of {len(ordered)} agents at once",
        )

    @override
    async def call(self, adapter: AgentAdapter, laid: AgentsAndACaller) -> Loaded:
        uuids = [AgentUUID(agent.uuid) for agent in (*laid.agents, *laid.unreadable)]
        if self.unknown:
            uuids.append(AgentUUID(MISSING))
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_uuids(uuids)


@dataclass(frozen=True)
class CountingContainers(When[AgentsAndACaller, AgentAdapter, Counted]):
    """미리 등록한 에이전트들의 컨테이너 수를 한 번에 센다. ``unknown`` 이면 없는 이름을 뒤에 붙인다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_container_counts"

    @override
    def describe(self, laid: AgentsAndACaller) -> str:
        ordered = (*laid.agents, *laid.unreadable)
        if self.unknown:
            return Says(
                f"{laid.caller.username}이 에이전트 {len(ordered)}개의 컨테이너 수와 없는 이름 "
                "하나의 수를 한 번에 조회합니다",
                english=(
                    f"{laid.caller.username} counts the containers of {len(ordered)} agents and "
                    "one unknown name at once"
                ),
            )
        return Says(
            f"{laid.caller.username}이 에이전트 {len(ordered)}개의 컨테이너 수를 한 번에 조회합니다",
            english=(
                f"{laid.caller.username} counts the containers of {len(ordered)} agents at once"
            ),
        )

    @override
    async def call(self, adapter: AgentAdapter, laid: AgentsAndACaller) -> Counted:
        ids = [AgentId(agent.agent_id) for agent in (*laid.agents, *laid.unreadable)]
        if self.unknown:
            ids.append(AgentId(UNKNOWN_AGENT))
        with ActingAs(laid.caller):
            return await adapter.batch_load_container_counts(ids)


@dataclass(frozen=True)
class LoadingRow(
    Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, Loaded]
):
    named: str
    guarantees: str
    situation: AgentsAndSomeone
    started: datetime
    unknown: bool = False
    unknown_denied: bool = False
    denied_after: int | None = None
    by_uuid: bool = False

    @override
    def summary(self) -> str:
        return self.named

    @override
    def describe(self) -> str:
        return self.guarantees

    @override
    def given(self) -> Given[TestSeedingSession, AgentsAndACaller]:
        return self.situation

    @override
    def when(self) -> When[AgentsAndACaller, AgentAdapter, Loaded]:
        if self.by_uuid:
            return LoadingByUuids(unknown=self.unknown)
        return LoadingByIds(unknown=self.unknown)

    @override
    def then(self) -> Then[AgentsAndACaller, Loaded]:
        return TheAgentsComeBackInOrder(
            started=self.started,
            unknown=self.unknown,
            unknown_denied=self.unknown_denied,
            denied_after=self.denied_after,
        )


@dataclass(frozen=True)
class CountingRow(
    Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, Counted]
):
    named: str
    guarantees: str
    situation: AgentsAndSomeone
    unknown: bool = False
    denied: bool = False

    @override
    def summary(self) -> str:
        return self.named

    @override
    def describe(self) -> str:
        return self.guarantees

    @override
    def given(self) -> Given[TestSeedingSession, AgentsAndACaller]:
        return self.situation

    @override
    def when(self) -> When[AgentsAndACaller, AgentAdapter, Counted]:
        return CountingContainers(unknown=self.unknown)

    @override
    def then(self) -> Then[AgentsAndACaller, Counted]:
        return TheContainerCountsComeBack(unknown=self.unknown, denied=self.denied)


STARTED = datetime.now(UTC)

READ = AgentsAndSomeone(readable=1, granted=True)
OTHER_GROUP = AgentsAndSomeone(readable=1, elsewhere=1, granted=True)
NOBODY = AgentsAndSomeone(readable=1)

SCENARIOS: list[LoadStep] = [
    LoadingRow(
        named="a-user-reading-the-group-loads-an-agent-by-name",
        guarantees=Says(
            "리소스 그룹의 에이전트를 읽을 수 있는 사용자가 이름으로 한 번에 조회하면 그 "
            "에이전트가 통째로 옵니다",
            english=(
                "when a user who can read the agents of the resource group loads one by name, "
                "the whole agent comes back"
            ),
        ),
        situation=READ,
        started=STARTED,
    ),
    LoadingRow(
        named="an-unknown-agent-name-answers-an-empty-value",
        guarantees=Says(
            "없는 이름은 빈 값으로 옵니다",
            english="a name nothing answers to comes back as an empty value",
        ),
        situation=READ,
        started=STARTED,
        unknown=True,
    ),
    LoadingRow(
        named="a-user-reading-one-group-gets-a-denial-for-the-agent-of-another",
        guarantees=Says(
            "한 그룹만 읽을 수 있는 사용자가 다른 그룹의 에이전트를 함께 조회하면 그 자리는 권한 "
            "부족으로 옵니다",
            english=(
                "when a user who can read one group loads an agent of another group beside it, "
                "that entry is rejected for lack of permission"
            ),
        ),
        situation=OTHER_GROUP,
        started=STARTED,
        denied_after=1,
    ),
    LoadingRow(
        named="a-user-reading-the-group-loads-an-agent-by-entity-id",
        guarantees=Says(
            "리소스 그룹의 에이전트를 읽을 수 있는 사용자가 id 로 한 번에 조회하면 그 에이전트가 "
            "통째로 옵니다",
            english=(
                "when a user who can read the agents of the resource group loads one by its "
                "entity id, the whole agent comes back"
            ),
        ),
        situation=READ,
        started=STARTED,
        by_uuid=True,
    ),
    LoadingRow(
        named="an-unknown-agent-entity-id-answers-a-denial",
        guarantees=Says(
            "id 로 조회하면 권한 검사를 거치므로, 없는 id 는 빈 값이 아니라 권한 부족으로 옵니다",
            english=(
                "a read by entity id is checked per id, so an id nothing answers to comes back "
                "as a denial rather than an empty value"
            ),
        ),
        situation=READ,
        started=STARTED,
        unknown=True,
        unknown_denied=True,
        by_uuid=True,
    ),
    LoadingRow(
        named="a-user-granted-nothing-gets-a-denial-for-the-agent-entity-id",
        guarantees=Says(
            "아무 권한도 없는 사용자가 id 로 조회하면 그 자리는 권한 부족으로 옵니다",
            english=(
                "when a user granted nothing loads an agent by its entity id, that entry is "
                "rejected for lack of permission"
            ),
        ),
        situation=NOBODY,
        started=STARTED,
        denied_after=0,
        by_uuid=True,
    ),
]


COUNTS: list[CountStep] = [
    CountingRow(
        named="a-user-reading-the-group-counts-no-container-on-the-agent",
        guarantees=Says(
            "리소스 그룹의 에이전트를 읽을 수 있는 사용자가 컨테이너 수를 조회하면 아무것도 돌지 "
            "않는 에이전트이므로 0 이 옵니다",
            english=(
                "when a user who can read the agents of the resource group counts containers, "
                "zero comes back because nothing runs on the agent"
            ),
        ),
        situation=READ,
    ),
    CountingRow(
        named="an-unknown-agent-name-counts-no-container",
        guarantees=Says(
            "없는 이름의 컨테이너 수는 0 으로 옵니다",
            english="the container count of a name nothing answers to comes back as zero",
        ),
        situation=READ,
        unknown=True,
    ),
    CountingRow(
        named="a-user-granted-nothing-gets-a-denial-for-the-container-count",
        guarantees=Says(
            "아무 권한도 없는 사용자가 컨테이너 수를 조회하면 권한 부족으로 옵니다",
            english=(
                "when a user granted nothing counts containers, the entry is rejected for lack "
                "of permission"
            ),
        ),
        situation=NOBODY,
        denied=True,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: LoadStep, adapter: AgentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", COUNTS, ids=lambda s: s.summary())
async def test_batch_loading_container_counts(
    scenario: CountStep, adapter: AgentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
