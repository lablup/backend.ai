"""서비스 카탈로그 여럿을 한 번에 조회."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.service_catalog.response import ServiceCatalogNode
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.service_catalog.adapter import ServiceCatalogAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.service_catalog import (
    ManyServicesAndACaller,
    ManyServicesAndSomeone,
    service_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Loaded = list[ServiceCatalogNode | Exception | None]
type ReadingStep = Scenario[
    TestSeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Loaded
]


@dataclass(frozen=True)
class LoadingTheLaidAndAMissingOne(When[ManyServicesAndACaller, ServiceCatalogAdapter, Loaded]):
    """미리 저장한 서비스들의 id 뒤에 없는 id 하나를 붙여 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyServicesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 서비스 {len(laid.laid)}개와 없는 id 하나를 "
            "한 번에 조회합니다",
            english=(
                f"{laid.caller.username} batch-loads the {len(laid.laid)} services created "
                "in advance and one unknown id"
            ),
        )

    @override
    async def call(self, adapter: ServiceCatalogAdapter, laid: ManyServicesAndACaller) -> Loaded:
        ids: list[ServiceCatalogID] = [
            *(one.id for one in laid.laid),
            ServiceCatalogID(uuid4()),
        ]
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class LoadingAsNobody(When[ManyServicesAndACaller, ServiceCatalogAdapter, Loaded]):
    """사용자 컨텍스트 없이 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyServicesAndACaller) -> str:
        return Says(
            f"사용자 컨텍스트 없이 서비스 {len(laid.laid)}개를 한 번에 조회합니다",
            english=f"batch-loads {len(laid.laid)} services without a user context",
        )

    @override
    async def call(self, adapter: ServiceCatalogAdapter, laid: ManyServicesAndACaller) -> Loaded:
        return await adapter.batch_load_by_ids([one.id for one in laid.laid])


@dataclass(frozen=True)
class TheyComeBackInTheOrderAsked(Then[ManyServicesAndACaller, Loaded]):
    """요청한 순서대로 한 항목씩 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "요청한 순서대로 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다",
            english="they come back in the order asked and the item for an unknown id is empty",
        )

    @override
    def look(self, laid: ManyServicesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(UnreachableError, answered.raised)]
        asked = len(laid.laid) + 1
        seen: list[Verdict] = [Same("len(items)", len(items), asked)]
        for i, service in enumerate(laid.laid):
            got = items[i] if i < len(items) else None
            if not isinstance(got, ServiceCatalogNode):
                seen.append(Same(f"items[{i}]", got, Says("노드", english="a node")))
                continue
            seen.append(
                Held[UUID](
                    f"items[{i}].entity_id",
                    got.entity_id,
                    SameAs(
                        service.id,
                        Says("미리 저장한 서비스", english="the service created in advance"),
                    ),
                )
            )
            seen.extend(
                service_verdicts(
                    f"items[{i}].", got, laid=service, written=WrittenByThisRun(self.started)
                )
            )
        last = items[asked - 1] if len(items) >= asked else "none"
        seen.append(Same(f"items[{asked - 1}]", last, None))
        return seen


@dataclass(frozen=True)
class TheSuperadminLoadsLaidAndMissing(
    Scenario[TestSeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Loaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-leaves-a-missing-id-empty"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 미리 저장한 서비스 둘과 없는 id 하나를 한 번에 조회하면, "
            "요청한 순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다",
            english=(
                "when the superadmin batch-loads two services created in advance and one "
                "unknown id, they come back in the order asked and the item for the unknown "
                "id is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyServicesAndACaller]:
        return ManyServicesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Loaded]:
        return LoadingTheLaidAndAMissingOne()

    @override
    def then(self) -> Then[ManyServicesAndACaller, Loaded]:
        return TheyComeBackInTheOrderAsked(started=self.started)


@dataclass(frozen=True)
class ABatchLoadCarryingNoUserIsRefused(
    Scenario[TestSeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-carrying-no-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "서비스 둘이 있고 사용자 컨텍스트 없이 한 번에 조회하면, 호출자를 알 수 없어 거부됩니다",
            english=(
                "when two services exist and they are batch-loaded without a user context, "
                "it is rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyServicesAndACaller]:
        return ManyServicesAndSomeone()

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Loaded]:
        return LoadingAsNobody()

    @override
    def then(self) -> Then[ManyServicesAndACaller, Loaded]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[ReadingStep] = [
    TheSuperadminLoadsLaidAndMissing(started=datetime.now(UTC)),
    ABatchLoadCarryingNoUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: ServiceCatalogAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
