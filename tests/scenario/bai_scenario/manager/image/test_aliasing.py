"""별칭 등록과 해제 — 이미지에 딸린 값이지만 전역 역할로 보호된다."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.image import (
    AnAliasAndACaller,
    AnAliasAndSomeone,
    AnIdThatHoldsNothing,
    AnImageAndACaller,
    AnImageAndSomeone,
    AnImageTheCallerMade,
    Filled,
    Target,
    TheLaidImage,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.image.request import AliasImageInput, DealiasImageInput
from ai.backend.common.dto.manager.v2.image.response import AliasImagePayload
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.image import ImageAliasNotFound, ImageNotFound
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)

A_NEW_ALIAS = "made-alias"
A_NAME_NO_IMAGE_HOLDS = "no-such-alias"


@dataclass(frozen=True)
class Aliasing(When[AnImageAndACaller, ImageAdapter, AliasImagePayload]):
    """이미지에 별칭을 등록한다."""

    at: Target = field(default_factory=TheLaidImage)
    alias: str = A_NEW_ALIAS

    @override
    def operation(self) -> str:
        return "admin_alias"

    @override
    def describe(self, laid: AnImageAndACaller) -> str:
        who = laid.caller.username
        if isinstance(self.at, AnIdThatHoldsNothing):
            return f"{who}이 {self.at.says()}에 별칭 등록"
        return f"{who}이 {laid.image.name}에 별칭 {self.alias} 등록"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnImageAndACaller) -> AliasImagePayload:
        target = self.at.id_of(laid)
        with ActingAs(laid.caller):
            return await adapter.admin_alias(AliasImageInput(image_id=target, alias=self.alias))


@dataclass(frozen=True)
class AliasingTheTaken(When[AnAliasAndACaller, ImageAdapter, AliasImagePayload]):
    """이미 다른 이미지가 사용 중인 별칭을 등록한다."""

    @override
    def operation(self) -> str:
        return "admin_alias"

    @override
    def describe(self, laid: AnAliasAndACaller) -> str:
        return f"{laid.caller.username}이 이미 사용 중인 별칭 {laid.alias.alias} 등록"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnAliasAndACaller) -> AliasImagePayload:
        with ActingAs(laid.caller):
            return await adapter.admin_alias(
                AliasImageInput(image_id=laid.image.id, alias=laid.alias.alias)
            )


@dataclass(frozen=True)
class Dealiasing(When[AnAliasAndACaller, ImageAdapter, AliasImagePayload]):
    """등록된 별칭을 해제한다. 이 호출은 id가 아니라 별칭 이름으로 대상을 지정한다."""

    named: str | None = None

    @override
    def operation(self) -> str:
        return "admin_dealias"

    @override
    def describe(self, laid: AnAliasAndACaller) -> str:
        who = laid.caller.username
        if self.named is not None:
            return f"{who}이 어느 이미지도 가리키지 않는 별칭 해제"
        return f"{who}이 별칭 {laid.alias.alias} 해제"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnAliasAndACaller) -> AliasImagePayload:
        named = self.named or laid.alias.alias
        with ActingAs(laid.caller):
            return await adapter.admin_dealias(DealiasImageInput(alias=named))


@dataclass(frozen=True)
class TheAliasAndItsImage(Then[AnImageAndACaller, AliasImagePayload]):
    """등록한 별칭과 그 별칭이 가리키는 이미지가 반환된다."""

    alias: str

    @override
    def says(self) -> str:
        return "등록한 별칭과 그 이미지의 id가 반환된다"

    @override
    def look(self, laid: AnImageAndACaller, answered: Answered[AliasImagePayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Held("응답", answered.response, Filled())]
        wanted: UUID = laid.image.id
        return [
            Same("alias", payload.alias, self.alias),
            Held("image_id", payload.image_id, SameAs(wanted, "미리 만들어 둔 이미지의 id")),
            Skipped("alias_id", "데이터베이스가 생성한다"),
        ]


@dataclass(frozen=True)
class TheRemovedAlias(Then[AnAliasAndACaller, AliasImagePayload]):
    """해제한 별칭과 그 이미지가 반환된다."""

    @override
    def says(self) -> str:
        return "해제한 별칭과 그 이미지의 id가 반환된다"

    @override
    def look(self, laid: AnAliasAndACaller, answered: Answered[AliasImagePayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Held("응답", answered.response, Filled())]
        wanted: UUID = laid.image.id
        return [
            Same("alias", payload.alias, laid.alias.alias),
            Held("image_id", payload.image_id, SameAs(wanted, "미리 만들어 둔 이미지의 id")),
            Skipped("alias_id", "데이터베이스가 생성한다"),
        ]


@dataclass(frozen=True)
class AliasingAnswersWithTheAliasAndItsImage(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, AliasImagePayload]
):
    @override
    def summary(self) -> str:
        return "aliasing-an-image-answers-with-the-alias-and-the-image-it-names"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이미지에 별칭을 등록하면 그 별칭과 가리키는 이미지가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, AliasImagePayload]:
        return Aliasing()

    @override
    def then(self) -> Then[AnImageAndACaller, AliasImagePayload]:
        return TheAliasAndItsImage(alias=A_NEW_ALIAS)


@dataclass(frozen=True)
class DealiasingAnswersWithTheRemovedAlias(
    Scenario[SeedingSession, AnAliasAndACaller, ImageAdapter, AliasImagePayload]
):
    @override
    def summary(self) -> str:
        return "dealiasing-answers-with-the-alias-it-removed"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 등록된 별칭을 해제하면 해제된 별칭과 그 이미지가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AnAliasAndACaller]:
        return AnAliasAndSomeone()

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, AliasImagePayload]:
        return Dealiasing()

    @override
    def then(self) -> Then[AnAliasAndACaller, AliasImagePayload]:
        return TheRemovedAlias()


@dataclass(frozen=True)
class AliasingWhatIsNotThere(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, AliasImagePayload]
):
    @override
    def summary(self) -> str:
        return "aliasing-an-id-that-holds-no-image-is-refused"

    @override
    def describe(self) -> str:
        return "어느 이미지도 가리키지 않는 id에 별칭을 등록하려 하면 대상을 찾을 수 없어 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, AliasImagePayload]:
        return Aliasing(at=AnIdThatHoldsNothing())

    @override
    def then(self) -> Then[AnImageAndACaller, AliasImagePayload]:
        return TheCallIsRefused(ImageNotFound)


@dataclass(frozen=True)
class AnAliasAnotherImageHolds(
    Scenario[SeedingSession, AnAliasAndACaller, ImageAdapter, AliasImagePayload]
):
    @override
    def summary(self) -> str:
        return "an-alias-another-image-already-holds-is-refused"

    @override
    def describe(self) -> str:
        return "이미 사용 중인 별칭을 등록하려 하면 유니크 제약 위반으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnAliasAndACaller]:
        return AnAliasAndSomeone()

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, AliasImagePayload]:
        return AliasingTheTaken()

    @override
    def then(self) -> Then[AnAliasAndACaller, AliasImagePayload]:
        return TheCallIsRefused(UniqueConstraintViolationError)


@dataclass(frozen=True)
class DealiasingWhatIsNotThere(
    Scenario[SeedingSession, AnAliasAndACaller, ImageAdapter, AliasImagePayload]
):
    @override
    def summary(self) -> str:
        return "dealiasing-a-name-no-image-holds-is-refused"

    @override
    def describe(self) -> str:
        return "어느 이미지도 가리키지 않는 별칭을 해제하려 하면 대상을 찾을 수 없어 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnAliasAndACaller]:
        return AnAliasAndSomeone()

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, AliasImagePayload]:
        return Dealiasing(named=A_NAME_NO_IMAGE_HOLDS)

    @override
    def then(self) -> Then[AnAliasAndACaller, AliasImagePayload]:
        return TheCallIsRefused(ImageAliasNotFound)


@dataclass(frozen=True)
class TheOwnerStillMayNotAlias(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, AliasImagePayload]
):
    @override
    def summary(self) -> str:
        return "the-maker-of-a-custom-image-still-may-not-alias-it"

    @override
    def describe(self) -> str:
        return (
            "자기가 만든 커스텀 이미지라도 별칭은 등록할 수 없다. "
            "별칭 등록은 그 이미지의 권한이 아니라 전역 역할로 보호되기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageTheCallerMade()

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, AliasImagePayload]:
        return Aliasing()

    @override
    def then(self) -> Then[AnImageAndACaller, AliasImagePayload]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class APlainUserMayNotDealias(
    Scenario[SeedingSession, AnAliasAndACaller, ImageAdapter, AliasImagePayload]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-dealias"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 별칭을 해제하려 하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnAliasAndACaller]:
        return AnAliasAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, AliasImagePayload]:
        return Dealiasing()

    @override
    def then(self) -> Then[AnAliasAndACaller, AliasImagePayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[Any] = [
    AliasingAnswersWithTheAliasAndItsImage(),
    DealiasingAnswersWithTheRemovedAlias(),
    AliasingWhatIsNotThere(),
    AnAliasAnotherImageHolds(),
    DealiasingWhatIsNotThere(),
    TheOwnerStillMayNotAlias(),
    APlainUserMayNotDealias(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_aliasing(
    scenario: Any, adapter: ImageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
