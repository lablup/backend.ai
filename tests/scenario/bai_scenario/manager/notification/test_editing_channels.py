"""채널 수정 — 지정한 필드만 바뀌고, 명세는 종류 안에서만 바뀐다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.notification.request import (
    NotificationChannelSpecInputDTO,
    UpdateNotificationChannelInput,
    WebhookSpecInputDTO,
)
from ai.backend.common.dto.manager.v2.notification.response import NotificationChannelNode
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.notification import InvalidNotificationSpec
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import (
    AChannelAndACaller,
    AChannelAndSomeone,
    TheChannelNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type EditingStep = Scenario[
    SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode
]

WAS_DESCRIBED = "이미 있던 채널"
NEW_URL = "https://hooks.example.test/elsewhere"


@dataclass(frozen=True)
class Editing(When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]):
    """지정한 필드만 바꾼다. ``unknown``이면 어느 행에도 없는 id를 쓴다.

    ``url``은 새 webhook 명세의 주소, ``empty_spec``은 webhook도 email도 없는 명세다.
    """

    named: str | None = None
    clear_description: bool = False
    url: str | None = None
    empty_spec: bool = False
    enabled: bool | None = None
    unknown: bool = False

    @override
    def operation(self) -> str:
        return "update_channel"

    @override
    def describe(self, laid: AChannelAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else f"채널 {laid.channel.name}"
        changes: list[str] = []
        if self.named is not None:
            changes.append(f"이름을 {self.named}으로")
        if self.clear_description:
            changes.append("설명을 비움")
        if self.url is not None:
            changes.append(f"주소를 {self.url}로")
        if self.empty_spec:
            changes.append("빈 명세로")
        if self.enabled is not None:
            changes.append(f"활성을 {self.enabled}로")
        what = ", ".join(changes) if changes else "아무것도 지정하지 않고"
        return f"{laid.caller.username}이 {target}을 {what} 수정"

    @override
    async def call(
        self, adapter: NotificationAdapter, laid: AChannelAndACaller
    ) -> NotificationChannelNode:
        fields: dict[str, Any] = {}
        if self.named is not None:
            fields["name"] = self.named
        if self.clear_description:
            fields["description"] = None
        if self.url is not None:
            fields["spec"] = NotificationChannelSpecInputDTO(
                webhook=WebhookSpecInputDTO(url=self.url)
            )
        if self.empty_spec:
            fields["spec"] = NotificationChannelSpecInputDTO()
        if self.enabled is not None:
            fields["enabled"] = self.enabled
        request = UpdateNotificationChannelInput(**fields)
        with ActingAs(laid.caller):
            payload = await adapter.update_channel(
                uuid4() if self.unknown else laid.channel.id, request
            )
        return payload.channel


@dataclass(frozen=True)
class TheSuperadminRenamesAChannel(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-renaming-a-channel-leaves-the-rest"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이름만 바꾸면 이름은 새 값이고 나머지는 그대로인 채널 전체가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return Editing(named="renamed")

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheChannelNode(started=self.started, named="renamed")


@dataclass(frozen=True)
class ClearingTheDescription(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "clearing-a-channel-description-leaves-it-empty"

    @override
    def describe(self) -> str:
        return "설명이 있는 채널의 설명을 비우면 설명이 비어 있는 채널이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN, description=WAS_DESCRIBED)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return Editing(clear_description=True)

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheChannelNode(started=self.started, described=None)


@dataclass(frozen=True)
class ChangingTheSpec(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "changing-a-webhook-spec-moves-the-channel-to-the-new-url"

    @override
    def describe(self) -> str:
        return "webhook 채널의 명세를 다른 주소로 바꾸면 주소가 새 값인 채널이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return Editing(url=NEW_URL)

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheChannelNode(started=self.started, url=NEW_URL)


@dataclass(frozen=True)
class DisablingAChannel(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "disabling-a-channel-answers-it-disabled"

    @override
    def describe(self) -> str:
        return "활성 채널을 비활성으로 바꾸면 비활성인 채널이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return Editing(enabled=False)

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheChannelNode(started=self.started, enabled=False)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-edit-naming-no-field-changes-nothing"

    @override
    def describe(self) -> str:
        return "아무 필드도 지정하지 않고 수정하면 아무것도 바뀌지 않은 채널이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return Editing()

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheChannelNode(started=self.started)


@dataclass(frozen=True)
class AnEmptySpecIsRefused(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    @override
    def summary(self) -> str:
        return "an-edit-with-a-spec-naming-neither-webhook-nor-email-is-refused"

    @override
    def describe(self) -> str:
        return "webhook도 email도 주지 않은 명세로 수정하려 하면 잘못된 입력으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return Editing(empty_spec=True)

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheCallIsRefused(InvalidNotificationSpec)


@dataclass(frozen=True)
class TheSuperadminEditingAnUnknownIdIsNotFound(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-editing-a-channel-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return Editing(named="nowhere", unknown=True)

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-channel"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 이름을 바꾸려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone()

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return Editing(named="by-a-user")

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[EditingStep] = [
    TheSuperadminRenamesAChannel(started=datetime.now(UTC)),
    ClearingTheDescription(started=datetime.now(UTC)),
    ChangingTheSpec(started=datetime.now(UTC)),
    DisablingAChannel(started=datetime.now(UTC)),
    AnEmptyEditChangesNothing(started=datetime.now(UTC)),
    AnEmptySpecIsRefused(),
    TheSuperadminEditingAnUnknownIdIsNotFound(),
    AUserGrantedNothingMayNotEdit(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing_channels(
    scenario: EditingStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
