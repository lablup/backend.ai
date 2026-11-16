"""별칭 등록과 해제 — 이미지에 딸린 값이지만 슈퍼관리자 검사로 보호된다."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

import pytest

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
    Language,
    Same,
    SameAs,
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
    in_language,
)
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
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

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
            return Says(
                f"{who}이 {self.at.says()}에 별칭을 등록합니다",
                english=f"{who} aliases {in_language(self.at.says(), Language.ENGLISH)}",
            )
        return Says(
            f"{who}이 {laid.image.name}에 별칭 {self.alias}를 등록합니다",
            english=f"{who} aliases {laid.image.name} as {self.alias}",
        )

    @override
    async def call(self, adapter: ImageAdapter, laid: AnImageAndACaller) -> AliasImagePayload:
        target = self.at.id_of(laid)
        with ActingAs(laid.caller):
            return await adapter.admin_alias(AliasImageInput(image_id=target, alias=self.alias))


@dataclass(frozen=True)
class AliasingTheTaken(When[AnAliasAndACaller, ImageAdapter, AliasImagePayload]):
    """이미 사용 중인 별칭을 등록한다."""

    @override
    def operation(self) -> str:
        return "admin_alias"

    @override
    def describe(self, laid: AnAliasAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 이미 사용 중인 별칭 {laid.alias.alias}를 등록합니다",
            english=f"{laid.caller.username} registers the already-used alias {laid.alias.alias}",
        )

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
            return Says(
                f"{who}이 어느 이미지도 가리키지 않는 별칭을 해제합니다",
                english=f"{who} dealiases a name no image holds",
            )
        return Says(
            f"{who}이 별칭 {laid.alias.alias}를 해제합니다",
            english=f"{who} dealiases {laid.alias.alias}",
        )

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
        return Says(
            "등록한 별칭과 그 이미지의 id 가 응답으로 옵니다",
            english="the alias just registered and the id of the image it names come back",
        )

    @override
    def look(self, laid: AnImageAndACaller, answered: Answered[AliasImagePayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Held("response", answered.response, Filled())]
        wanted: UUID = laid.image.id
        return [
            Same("alias", payload.alias, self.alias),
            Held(
                "image_id",
                payload.image_id,
                SameAs(
                    wanted,
                    Says(
                        "미리 저장한 이미지의 id",
                        english="the id of the image created in advance",
                    ),
                ),
            ),
            Skipped(
                "alias_id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
        ]


@dataclass(frozen=True)
class TheRemovedAlias(Then[AnAliasAndACaller, AliasImagePayload]):
    """해제한 별칭과 그 이미지가 반환된다."""

    @override
    def says(self) -> str:
        return Says(
            "해제한 별칭과 그 이미지의 id 가 응답으로 옵니다",
            english="the alias just removed and the id of the image it named come back",
        )

    @override
    def look(self, laid: AnAliasAndACaller, answered: Answered[AliasImagePayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Held("response", answered.response, Filled())]
        wanted: UUID = laid.image.id
        return [
            Same("alias", payload.alias, laid.alias.alias),
            Held(
                "image_id",
                payload.image_id,
                SameAs(
                    wanted,
                    Says(
                        "미리 저장한 이미지의 id",
                        english="the id of the image created in advance",
                    ),
                ),
            ),
            Skipped(
                "alias_id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
        ]


@dataclass(frozen=True)
class AliasingAnswersWithTheAliasAndItsImage(
    Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, AliasImagePayload]
):
    @override
    def summary(self) -> str:
        return "aliasing-an-image-answers-with-the-alias-and-the-image-it-names"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 이미지에 별칭을 등록하면 그 별칭과 가리키는 이미지가 응답으로 옵니다",
            english=(
                "when the superadmin registers an alias on an image, "
                "the alias and the image it names come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, AliasImagePayload]:
        return Aliasing()

    @override
    def then(self) -> Then[AnImageAndACaller, AliasImagePayload]:
        return TheAliasAndItsImage(alias=A_NEW_ALIAS)


@dataclass(frozen=True)
class DealiasingAnswersWithTheRemovedAlias(
    Scenario[TestSeedingSession, AnAliasAndACaller, ImageAdapter, AliasImagePayload]
):
    @override
    def summary(self) -> str:
        return "dealiasing-answers-with-the-alias-it-removed"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 등록된 별칭을 해제하면 해제된 별칭과 그 이미지가 응답으로 옵니다",
            english=(
                "when the superadmin removes a registered alias, "
                "the removed alias and its image come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnAliasAndACaller]:
        return AnAliasAndSomeone()

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, AliasImagePayload]:
        return Dealiasing()

    @override
    def then(self) -> Then[AnAliasAndACaller, AliasImagePayload]:
        return TheRemovedAlias()


@dataclass(frozen=True)
class AliasingWhatIsNotThere(
    Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, AliasImagePayload]
):
    @override
    def summary(self) -> str:
        return "aliasing-an-id-that-holds-no-image-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "어느 이미지도 가리키지 않는 id 에 별칭을 등록하려 하면 대상이 없어 거부됩니다",
            english=(
                "registering an alias on an id that points at no image is rejected as not found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, AliasImagePayload]:
        return Aliasing(at=AnIdThatHoldsNothing())

    @override
    def then(self) -> Then[AnImageAndACaller, AliasImagePayload]:
        return TheCallIsRefused(ImageNotFound)


@dataclass(frozen=True)
class AnAliasAnotherImageHolds(
    Scenario[TestSeedingSession, AnAliasAndACaller, ImageAdapter, AliasImagePayload]
):
    @override
    def summary(self) -> str:
        return "an-alias-that-is-already-in-use-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "이미 사용 중인 별칭을 등록하려 하면 유니크 제약 위반으로 거부됩니다",
            english=(
                "registering an alias that is already in use is rejected "
                "as a unique constraint violation"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnAliasAndACaller]:
        return AnAliasAndSomeone()

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, AliasImagePayload]:
        return AliasingTheTaken()

    @override
    def then(self) -> Then[AnAliasAndACaller, AliasImagePayload]:
        return TheCallIsRefused(UniqueConstraintViolationError)


@dataclass(frozen=True)
class DealiasingWhatIsNotThere(
    Scenario[TestSeedingSession, AnAliasAndACaller, ImageAdapter, AliasImagePayload]
):
    @override
    def summary(self) -> str:
        return "dealiasing-a-name-no-image-holds-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "어느 이미지도 가리키지 않는 별칭을 해제하려 하면 대상이 없어 거부됩니다",
            english="removing a name no image holds is rejected as not found",
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnAliasAndACaller]:
        return AnAliasAndSomeone()

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, AliasImagePayload]:
        return Dealiasing(named=A_NAME_NO_IMAGE_HOLDS)

    @override
    def then(self) -> Then[AnAliasAndACaller, AliasImagePayload]:
        return TheCallIsRefused(ImageAliasNotFound)


@dataclass(frozen=True)
class TheOwnerStillMayNotAlias(
    Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, AliasImagePayload]
):
    @override
    def summary(self) -> str:
        return "the-maker-of-a-custom-image-still-may-not-alias-it"

    @override
    def describe(self) -> str:
        return Says(
            "자기가 만든 커스텀 이미지라도 별칭은 등록할 수 없습니다. "
            "별칭 등록은 해당 이미지의 권한이 아니라 superadmin 검사로 보호되기 때문입니다",
            english=(
                "even the maker of a custom image may not register an alias, because "
                "the superadmin check protects alias registration, not the permission "
                "on that image"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnImageAndACaller]:
        return AnImageTheCallerMade()

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, AliasImagePayload]:
        return Aliasing()

    @override
    def then(self) -> Then[AnImageAndACaller, AliasImagePayload]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class APlainUserMayNotDealias(
    Scenario[TestSeedingSession, AnAliasAndACaller, ImageAdapter, AliasImagePayload]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-dealias"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 별칭을 해제하려 하면 superadmin 권한 부족으로 거부됩니다",
            english=(
                "when a user who is not the superadmin tries to remove an alias, "
                "the call is rejected for lack of superadmin privilege"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnAliasAndACaller]:
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
