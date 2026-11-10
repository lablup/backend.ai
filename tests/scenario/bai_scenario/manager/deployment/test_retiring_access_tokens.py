"""배포가 걸린 접근 토큰 purge 하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.deployment.request import BulkDeleteAccessTokensInput
from ai.backend.common.dto.manager.v2.deployment.response import (
    BulkDeleteAccessTokensPayload,
    DeleteAccessTokenPayload,
)
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.access_token import (
    TOKEN_ID,
    TokensOfADeployment,
    TokensOfADeploymentAndACaller,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type PurgeAnswer = DeleteAccessTokenPayload
type BulkAnswer = BulkDeleteAccessTokensPayload
type PurgeStep = Scenario[
    TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, PurgeAnswer
]
type BulkStep = Scenario[
    TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, BulkAnswer
]


@dataclass(frozen=True)
class PurgingTheFirstToken(When[TokensOfADeploymentAndACaller, DeploymentAdapter, PurgeAnswer]):
    """심은 토큰 하나의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "purge_access_token"

    @override
    def describe(self, laid: TokensOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 토큰 하나를 purge 합니다",
            english=f"{laid.caller.username} purges one of the tokens seeded in advance",
        )

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: TokensOfADeploymentAndACaller
    ) -> PurgeAnswer:
        with ActingAs(laid.caller):
            return await adapter.purge_access_token(laid.tokens[0].id)


@dataclass(frozen=True)
class TheTokenIsGone(Then[TokensOfADeploymentAndACaller, PurgeAnswer]):
    """purge 한 토큰의 id 가 응답으로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "purge 한 토큰의 id 가 응답으로 옵니다",
            english="the id of the purged token comes back",
        )

    @override
    def look(
        self, laid: TokensOfADeploymentAndACaller, answered: Answered[PurgeAnswer]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Held[UUID]("id", payload.id, SameAs(laid.tokens[0].id, TOKEN_ID)),
            Held[UUID]("field_id", payload.field_id, SameAs(laid.tokens[0].id, TOKEN_ID)),
        ]


@dataclass(frozen=True)
class DeletingTokensAtOnce(When[TokensOfADeploymentAndACaller, DeploymentAdapter, BulkAnswer]):
    """토큰들의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "bulk_delete_access_tokens"

    @override
    def describe(self, laid: TokensOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 토큰 {len(laid.tokens)}개를 한 번에 purge 합니다",
            english=f"{laid.caller.username} purges {len(laid.tokens)} tokens at once",
        )

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: TokensOfADeploymentAndACaller
    ) -> BulkAnswer:
        with ActingAs(laid.caller):
            return await adapter.bulk_delete_access_tokens(
                BulkDeleteAccessTokensInput(ids=[token.id for token in laid.tokens])
            )


@dataclass(frozen=True)
class ThePurgedTokenIdsComeBack(Then[TokensOfADeploymentAndACaller, BulkAnswer]):
    """purge 한 토큰의 id 들이 온다."""

    @override
    def says(self) -> str:
        return Says(
            "purge 한 토큰의 id 들이 옵니다",
            english="the ids of the purged tokens come back",
        )

    @override
    def look(
        self, laid: TokensOfADeploymentAndACaller, answered: Answered[BulkAnswer]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [Same("ids count", len(payload.ids), len(laid.tokens))]
        wanted: list[UUID] = [token.id for token in laid.tokens]
        for i, token_id in enumerate(payload.ids):
            verdicts.append(Held[UUID](f"ids[{i}]", token_id, SameAs(wanted[i], TOKEN_ID)))
        return verdicts


@dataclass(frozen=True)
class NoTokenIdComesBack(Then[TokensOfADeploymentAndACaller, BulkAnswer]):
    """purge 된 것 없이, 응답은 비어 온다."""

    @override
    def says(self) -> str:
        return Says(
            "purge 된 것 없이 id 목록이 비어 옵니다",
            english="nothing is purged and the id list comes back empty",
        )

    @override
    def look(
        self, laid: TokensOfADeploymentAndACaller, answered: Answered[BulkAnswer]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [Same("ids", payload.ids, [])]


@dataclass(frozen=True)
class AUserGrantedDeploymentPurgePurgesAToken(
    Scenario[TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, PurgeAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-purge-purges-a-token"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회와 영구 삭제 권한을 받은 사용자가 배포가 걸린 접근 토큰 하나를 purge 하면, "
            "그 토큰의 id 가 옵니다. 토큰 purge 는 토큰이 걸린 배포를 먼저 찾는 호출이라 "
            "조회 권한도 필요합니다",
            english=(
                "when a user granted deployment read and purge purges one of the access "
                "tokens the deployment holds, the id of that token comes back. The purge "
                "reads the deployment first, so read is also required"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TokensOfADeploymentAndACaller]:
        return TokensOfADeployment(granted=(Permission.READ, Permission.HARD_DELETE))

    @override
    def when(self) -> When[TokensOfADeploymentAndACaller, DeploymentAdapter, PurgeAnswer]:
        return PurgingTheFirstToken()

    @override
    def then(self) -> Then[TokensOfADeploymentAndACaller, PurgeAnswer]:
        return TheTokenIsGone()


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNoToken(
    Scenario[TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, PurgeAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-no-token"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포가 걸린 접근 토큰 하나를 purge 하려 하면, "
            "토큰이 걸린 배포를 찾는 조회가 거부됩니다",
            english=(
                "when a user granted nothing tries to purge one of the access tokens the "
                "deployment holds, the lookup that finds the deployment holding the "
                "token is rejected"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TokensOfADeploymentAndACaller]:
        return TokensOfADeployment()

    @override
    def when(self) -> When[TokensOfADeploymentAndACaller, DeploymentAdapter, PurgeAnswer]:
        return PurgingTheFirstToken()

    @override
    def then(self) -> Then[TokensOfADeploymentAndACaller, PurgeAnswer]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class AUserGrantedDeploymentPurgePurgesTokensAtOnce(
    Scenario[TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, BulkAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-purge-purges-tokens-at-once"

    @override
    def describe(self) -> str:
        return Says(
            "배포 영구 삭제 권한을 받은 사용자가 배포가 걸린 접근 토큰 여럿을 한 번에 purge 하면, "
            "그 토큰들의 id 가 옵니다",
            english=(
                "when a user granted deployment purge purges several access tokens the "
                "deployment holds at once, the ids of those tokens come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TokensOfADeploymentAndACaller]:
        return TokensOfADeployment(granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[TokensOfADeploymentAndACaller, DeploymentAdapter, BulkAnswer]:
        return DeletingTokensAtOnce()

    @override
    def then(self) -> Then[TokensOfADeploymentAndACaller, BulkAnswer]:
        return ThePurgedTokenIdsComeBack()


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNoTokenAtOnce(
    Scenario[TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, BulkAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-no-token-at-once"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포가 걸린 접근 토큰 여럿을 한 번에 purge 하려 하면, "
            "purge 된 것 없이 id 목록이 비어 옵니다",
            english=(
                "when a user granted nothing tries to purge several access tokens the "
                "deployment holds at once, nothing is purged and the id list comes back empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TokensOfADeploymentAndACaller]:
        return TokensOfADeployment()

    @override
    def when(self) -> When[TokensOfADeploymentAndACaller, DeploymentAdapter, BulkAnswer]:
        return DeletingTokensAtOnce()

    @override
    def then(self) -> Then[TokensOfADeploymentAndACaller, BulkAnswer]:
        return NoTokenIdComesBack()


SCENARIOS: list[PurgeStep | BulkStep] = [
    AUserGrantedDeploymentPurgePurgesAToken(),
    AUserGrantedNothingPurgesNoToken(),
    AUserGrantedDeploymentPurgePurgesTokensAtOnce(),
    AUserGrantedNothingPurgesNoTokenAtOnce(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring_access_tokens(
    scenario: PurgeStep | BulkStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
