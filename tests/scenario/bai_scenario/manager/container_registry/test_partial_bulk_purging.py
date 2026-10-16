"""컨테이너 레지스트리 여럿 영구 삭제."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.container_registry.request import (
    PartialBulkPurgeContainerRegistriesInput,
)
from ai.backend.common.dto.manager.v2.container_registry.response import ContainerRegistryNode
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.container_registry import (
    MISSING_ENTITY_ID,
    ManyRegistriesAndACaller,
    ManyRegistriesAndSomeone,
)
from bai_scenario.components.domain import Mentions
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPayload[ContainerRegistryNode]
type PurgingStep = Scenario[
    TestSeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Purged
]


@dataclass(frozen=True)
class PurgingEveryRegistry(When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Purged]):
    """미리 만들어 둔 레지스트리들을 한 번에 영구 삭제한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "admin_partial_bulk_purge"

    @override
    def describe(self, laid: ManyRegistriesAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return (
            f"{laid.caller.username}이 레지스트리 {len(laid.registries)}개{besides}를 "
            "한 번에 영구 삭제함"
        )

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ManyRegistriesAndACaller
    ) -> Purged:
        ids: list[UUID] = [registry.id for registry in laid.registries]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.admin_partial_bulk_purge(
                PartialBulkPurgeContainerRegistriesInput(ids=ids)
            )


@dataclass(frozen=True)
class EveryRegistryIsPurged(Then[ManyRegistriesAndACaller, Purged]):
    """레지스트리가 모두 지워지기 전 모습으로 처리된 목록에 오고, `missing`만 실패 목록에 온다."""

    missing: UUID

    @override
    def says(self) -> str:
        return (
            "미리 만들어 둔 레지스트리가 모두 지워지기 전 모습으로 오고, 없는 id 는 대상이 "
            "없다는 이유로 실패 목록에 온다"
        )

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.registries))
        ]
        for i, (node, registry) in enumerate(zip(payload.successes, laid.registries, strict=False)):
            at = f"successes[{i}]."
            verdicts += [
                Held[UUID](
                    f"{at}id", node.id, SameAs(registry.id, "미리 만들어 둔 레지스트리의 id")
                ),
                Same(f"{at}url", node.url, registry.url),
                Same(f"{at}registry_name", node.registry_name, registry.registry_name),
                Same(f"{at}type", node.type, registry.type),
                Same(f"{at}project", node.project, registry.project),
                Same(f"{at}username", node.username, registry.username),
                Same(f"{at}ssl_verify", node.ssl_verify, registry.ssl_verify),
                Same(f"{at}is_global", node.is_global, registry.is_global),
                Same(f"{at}extra", node.extra, registry.extra),
            ]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class NoRegistryIsPurged(Then[ManyRegistriesAndACaller, Purged]):
    """처리된 레지스트리 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "처리된 레지스트리 없이 대상이 모두 실패 목록에 온다"

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.registries)),
        ]
        for i, (failure, registry) in enumerate(zip(payload.failed, laid.registries, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(registry.id, "미리 만들어 둔 레지스트리의 id"),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts


@dataclass(frozen=True)
class TheSuperadminPurgesSeveralAndHearsOfTheMissingOne(
    Scenario[TestSeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Purged]
):
    missing: UUID = MISSING_ENTITY_ID

    @override
    def summary(self) -> str:
        return "purging-several-registries-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 레지스트리 둘과 없는 id 하나를 한 번에 영구 삭제하면, 둘은 지워지기 전 "
            "모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Purged]:
        return PurgingEveryRegistry(missing=self.missing)

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Purged]:
        return EveryRegistryIsPurged(missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-registries"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 레지스트리 여럿을 한 번에 영구 삭제하려 하면, 지워진 것 "
            "없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Purged]:
        return PurgingEveryRegistry()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Purged]:
        return NoRegistryIsPurged(reason="Insufficient permission")


SCENARIOS: list[PurgingStep] = [
    TheSuperadminPurgesSeveralAndHearsOfTheMissingOne(),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: ContainerRegistryAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
