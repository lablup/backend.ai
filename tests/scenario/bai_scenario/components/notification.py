"""What a notification scenario table says besides the call.

A channel and a rule are both created in no scope. A table needs the caller, and the
channel or rule the call reads; a rule's table needs the channel it dispatches through
as well.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.notification import NotificationChannelType, NotificationRuleType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.notification.response import (
    NotificationChannelNode,
    NotificationRuleNode,
    SearchNotificationChannelsPayload,
    SearchNotificationRulesPayload,
    ValidateNotificationRulePayload,
)
from ai.backend.common.dto.manager.v2.notification.types import (
    EmailSpecInfo,
    NotificationChannelTypeDTO,
    WebhookSpecInfo,
)
from ai.backend.manager.data.notification.types import NotificationChannelData, NotificationRuleData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Language,
    Refused,
    Same,
    SameAs,
    Says,
    Skipped,
    Then,
    Verdict,
    in_language,
)
from bai_scenario.components.domain import Mentions, WrittenByThisRun
from bai_scenario.components.system import KEPT, Kept, lay_a_caller, role_named
from bai_scenario.seeds.notification.channel import (
    FROM_EMAIL,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USERNAME,
    TO_EMAIL,
    WEBHOOK_URL,
    TestSeedEmailChannel,
    TestSeedWebhookChannel,
)
from bai_scenario.seeds.notification.rule import TEMPLATE, TestSeedRuleOf, TestSeedRuleOfNoChannel

type LoadedChannels = list[NotificationChannelNode | Exception | None]
type LoadedRules = list[NotificationRuleNode | Exception | None]


# ------------------------------------------------------------------ situations


@dataclass(frozen=True)
class AChannelAndACaller:
    """채널 하나와, 그것을 호출할 사용자. 채널은 그 사용자가 만든 것으로 기록되어 있다."""

    channel: NotificationChannelData
    caller: UserData


@dataclass(frozen=True)
class ManyChannelsAndACaller:
    """검색 대상 채널 여럿과, 검색을 호출할 사용자. ``laid``는 응답에 나와야 하는 것만이고 ``named``는 그중 하나다."""

    laid: tuple[NotificationChannelData, ...]
    named: NotificationChannelData
    caller: UserData


@dataclass(frozen=True)
class ARuleAndACaller:
    """규칙 하나와 그것이 가리키는 채널, 그리고 호출할 사용자."""

    rule: NotificationRuleData
    channel: NotificationChannelData
    caller: UserData


@dataclass(frozen=True)
class ManyRulesAndACaller:
    """검색 대상 규칙 여럿과, 검색을 호출할 사용자. ``laid``는 응답에 나와야 하는 것만이고 ``named``는 그중 하나다."""

    laid: tuple[NotificationRuleData, ...]
    named: NotificationRuleData
    caller: UserData


@dataclass(frozen=True)
class AChannelAndSomeone(Given[Any, AChannelAndACaller]):
    """채널 하나와 사용자 한 명. 채널은 그 사용자가 만든 것으로 기록된다."""

    role: UserRole = UserRole.USER
    channel_type: NotificationChannelType = NotificationChannelType.WEBHOOK
    description: str | None = None
    enabled: bool = True

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        channel_type = self.channel_type.value
        return Says(
            f"{channel_type} 채널 하나와, {who} 한 명",
            english=f"one {channel_type} channel and one {in_language(who, Language.ENGLISH)}",
        )

    @override
    async def lay(self, seeding: Any) -> AChannelAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        channel = await seeding.creating_from(_channel_seed(self, "channel"), caller)
        return AChannelAndACaller(seeding.made(channel), seeding.made(caller))


@dataclass(frozen=True)
class AChannelARuleAndSomeone(Given[Any, AChannelAndACaller]):
    """채널 하나와 그것을 가리키는 규칙 하나, 그리고 사용자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        return Says(
            f"채널 하나와 그것을 가리키는 규칙 하나, 그리고 {who} 한 명",
            english=(
                f"one channel and one rule pointing at it, and one "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AChannelAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        channel = await seeding.creating_from(TestSeedWebhookChannel(), caller)
        await seeding.creating_from_two(TestSeedRuleOf(), channel, caller)
        return AChannelAndACaller(seeding.made(channel), seeding.made(caller))


@dataclass(frozen=True)
class TwoChannelsAndSomeone(Given[Any, ManyChannelsAndACaller]):
    """webhook 채널 둘과 사용자 한 명. ``named``는 앞의 것이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        return Says(
            f"webhook 채널 둘과, {who} 한 명",
            english=f"two webhook channels and one {in_language(who, Language.ENGLISH)}",
        )

    @override
    async def lay(self, seeding: Any) -> ManyChannelsAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        wanted = await seeding.creating_from(TestSeedWebhookChannel(name_hint="wanted"), caller)
        other = await seeding.creating_from(TestSeedWebhookChannel(name_hint="other"), caller)
        return ManyChannelsAndACaller(
            laid=(seeding.made(wanted), seeding.made(other)),
            named=seeding.made(wanted),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class AWebhookAndAnEmailChannel(Given[Any, ManyChannelsAndACaller]):
    """webhook 채널 하나와 email 채널 하나, 사용자 한 명. ``named``는 email 채널이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        return Says(
            f"webhook 채널 하나와 email 채널 하나, 그리고 {who} 한 명",
            english=(
                f"one webhook channel and one email channel, and one "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ManyChannelsAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        webhook = await seeding.creating_from(TestSeedWebhookChannel(), caller)
        email = await seeding.creating_from(TestSeedEmailChannel(), caller)
        return ManyChannelsAndACaller(
            laid=(seeding.made(webhook), seeding.made(email)),
            named=seeding.made(email),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class AnEnabledAndADisabledChannel(Given[Any, ManyChannelsAndACaller]):
    """활성 채널 하나와 비활성 채널 하나, 사용자 한 명. ``laid``는 활성인 것뿐이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        return Says(
            f"활성 webhook 채널 하나와 비활성 하나, 그리고 {who} 한 명",
            english=(
                f"one active webhook channel and one inactive channel, and one "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ManyChannelsAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        active = await seeding.creating_from(TestSeedWebhookChannel(), caller)
        await seeding.creating_from(TestSeedWebhookChannel(enabled=False), caller)
        return ManyChannelsAndACaller(
            laid=(seeding.made(active),),
            named=seeding.made(active),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ARuleAndSomeone(Given[Any, ARuleAndACaller]):
    """규칙 하나와 그것이 가리키는 webhook 채널, 그리고 사용자 한 명."""

    role: UserRole = UserRole.USER
    message_template: str = TEMPLATE
    description: str | None = None
    enabled: bool = True

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        return Says(
            f"규칙 하나와 그것이 가리키는 webhook 채널, 그리고 {who} 한 명",
            english=(
                f"one rule and the webhook channel it points at, and one "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ARuleAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        channel = await seeding.creating_from(TestSeedWebhookChannel(), caller)
        rule = await seeding.creating_from_two(
            TestSeedRuleOf(
                message_template=self.message_template,
                description=self.description,
                enabled=self.enabled,
            ),
            channel,
            caller,
        )
        return ARuleAndACaller(seeding.made(rule), seeding.made(channel), seeding.made(caller))


@dataclass(frozen=True)
class AnOrphanRuleAndSomeone(Given[Any, ARuleAndACaller]):
    """없는 채널 id를 가리키는 규칙 하나와 사용자 한 명. 채널 자리는 규칙과 무관한 채널 하나로 채운다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        return Says(
            f"없는 채널 id 를 가리키는 규칙 하나와, {who} 한 명",
            english=(
                f"one rule pointing at an unknown channel id and one "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ARuleAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        channel = await seeding.creating_from(TestSeedWebhookChannel(), caller)
        rule = await seeding.creating_from(TestSeedRuleOfNoChannel(), caller)
        return ARuleAndACaller(seeding.made(rule), seeding.made(channel), seeding.made(caller))


@dataclass(frozen=True)
class TwoRulesAndSomeone(Given[Any, ManyRulesAndACaller]):
    """같은 채널을 가리키는 규칙 둘과 사용자 한 명. ``named``는 앞의 것이다."""

    role: UserRole = UserRole.USER
    other_rule_type: NotificationRuleType = NotificationRuleType.SESSION_STARTED

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        return Says(
            f"같은 webhook 채널을 가리키는 규칙 둘과, {who} 한 명",
            english=(
                f"two rules pointing at the same webhook channel and one "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ManyRulesAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        channel = await seeding.creating_from(TestSeedWebhookChannel(), caller)
        wanted = await seeding.creating_from_two(
            TestSeedRuleOf(name_hint="wanted"), channel, caller
        )
        other = await seeding.creating_from_two(
            TestSeedRuleOf(name_hint="other", rule_type=self.other_rule_type), channel, caller
        )
        return ManyRulesAndACaller(
            laid=(seeding.made(wanted), seeding.made(other)),
            named=seeding.made(wanted),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class AnEnabledAndADisabledRule(Given[Any, ManyRulesAndACaller]):
    """활성 규칙 하나와 비활성 규칙 하나, 사용자 한 명. ``laid``는 활성인 것뿐이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        return Says(
            f"활성 규칙 하나와 비활성 하나, 그리고 {who} 한 명",
            english=(
                f"one active rule and one inactive rule, and one "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ManyRulesAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        channel = await seeding.creating_from(TestSeedWebhookChannel(), caller)
        active = await seeding.creating_from_two(TestSeedRuleOf(), channel, caller)
        await seeding.creating_from_two(TestSeedRuleOf(enabled=False), channel, caller)
        return ManyRulesAndACaller(
            laid=(seeding.made(active),),
            named=seeding.made(active),
            caller=seeding.made(caller),
        )


def _channel_seed(
    given: AChannelAndSomeone, name_hint: str
) -> TestSeedWebhookChannel | TestSeedEmailChannel:
    match given.channel_type:
        case NotificationChannelType.WEBHOOK:
            return TestSeedWebhookChannel(
                name_hint=name_hint, description=given.description, enabled=given.enabled
            )
        case NotificationChannelType.EMAIL:
            return TestSeedEmailChannel(name_hint=name_hint, enabled=given.enabled)


# ------------------------------------------------------------------ verdicts


def webhook_spec_verdicts(prefix: str, spec: object, *, url: str) -> list[Verdict]:
    if not isinstance(spec, WebhookSpecInfo):
        return [Same(f"{prefix}spec", type(spec).__name__, WebhookSpecInfo.__name__)]
    return [
        Same(f"{prefix}spec.channel_type", spec.channel_type, NotificationChannelTypeDTO.WEBHOOK),
        Same(f"{prefix}spec.url", spec.url, url),
    ]


def email_spec_verdicts(prefix: str, spec: object) -> list[Verdict]:
    if not isinstance(spec, EmailSpecInfo):
        return [Same(f"{prefix}spec", type(spec).__name__, EmailSpecInfo.__name__)]
    return [
        Same(f"{prefix}spec.channel_type", spec.channel_type, NotificationChannelTypeDTO.EMAIL),
        Same(f"{prefix}spec.smtp.host", spec.smtp.host, SMTP_HOST),
        Same(f"{prefix}spec.smtp.port", spec.smtp.port, SMTP_PORT),
        Same(f"{prefix}spec.smtp.use_tls", spec.smtp.use_tls, True),
        Same(f"{prefix}spec.smtp.timeout", spec.smtp.timeout, 30),
        Same(f"{prefix}spec.message.from_email", spec.message.from_email, FROM_EMAIL),
        Same(f"{prefix}spec.message.to_emails", spec.message.to_emails, [TO_EMAIL]),
        Same(f"{prefix}spec.message.subject_template", spec.message.subject_template, None),
        Same(
            f"{prefix}spec.auth.username",
            spec.auth.username if spec.auth is not None else None,
            SMTP_USERNAME,
        ),
        Skipped(
            f"{prefix}spec.auth.password",
            Says("응답 타입에 그 자리가 없습니다", english="the response type has no such place"),
        ),
    ]


def channel_verdicts(
    prefix: str,
    node: NotificationChannelNode,
    *,
    name: str,
    description: str | None,
    channel_type: NotificationChannelType,
    url: str,
    enabled: bool,
    created_by: UUID,
    written: WrittenByThisRun,
) -> list[Verdict]:
    """Every place of one channel node."""
    spec: list[Verdict]
    match channel_type:
        case NotificationChannelType.WEBHOOK:
            spec = webhook_spec_verdicts(prefix, node.spec, url=url)
        case NotificationChannelType.EMAIL:
            spec = email_spec_verdicts(prefix, node.spec)
    return [
        Skipped(
            f"{prefix}id", Says("데이터베이스가 생성합니다", english="the database generates it")
        ),
        Same(f"{prefix}name", node.name, name),
        Same(f"{prefix}description", node.description, description),
        Same(f"{prefix}channel_type", node.channel_type.value, channel_type.value),
        *spec,
        Same(f"{prefix}enabled", node.enabled, enabled),
        Held[UUID](
            f"{prefix}created_by",
            node.created_by,
            SameAs[UUID](created_by, Says("만든 사람", english="the user who created it")),
        ),
        Held(f"{prefix}created_at", node.created_at, written),
        Held(f"{prefix}updated_at", node.updated_at, written),
    ]


def rule_verdicts(
    prefix: str,
    node: NotificationRuleNode,
    *,
    name: str,
    description: str | None,
    rule_type: NotificationRuleType,
    channel_id: UUID,
    message_template: str,
    enabled: bool,
    created_by: UUID,
    written: WrittenByThisRun,
) -> list[Verdict]:
    """Every place of one rule node."""
    return [
        Skipped(
            f"{prefix}id", Says("데이터베이스가 생성합니다", english="the database generates it")
        ),
        Same(f"{prefix}name", node.name, name),
        Same(f"{prefix}description", node.description, description),
        Same(f"{prefix}rule_type", node.rule_type.value, rule_type.value),
        Held[UUID](
            f"{prefix}channel_id",
            node.channel_id,
            SameAs[UUID](
                channel_id,
                Says("가리키는 채널", english="the channel it points at"),
            ),
        ),
        Same(f"{prefix}message_template", node.message_template, message_template),
        Same(f"{prefix}enabled", node.enabled, enabled),
        Held[UUID](
            f"{prefix}created_by",
            node.created_by,
            SameAs[UUID](created_by, Says("만든 사람", english="the user who created it")),
        ),
        Held(f"{prefix}created_at", node.created_at, written),
        Held(f"{prefix}updated_at", node.updated_at, written),
    ]


@dataclass(frozen=True)
class TheNewChannelNode(Then[Any, NotificationChannelNode]):
    """방금 생성한 채널이 통째로 반환된다. 기대값은 요청이 지정한 값에서 읽는다."""

    started: datetime
    named: str
    channel_type: NotificationChannelType = NotificationChannelType.WEBHOOK
    url: str = WEBHOOK_URL
    enabled: bool = True

    @override
    def says(self) -> str:
        return Says(
            "생성한 채널 전체가 반환됩니다",
            english="the whole channel just created comes back",
        )

    @override
    def look(self, laid: Any, answered: Answered[NotificationChannelNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return channel_verdicts(
            "",
            node,
            name=self.named,
            description=None,
            channel_type=self.channel_type,
            url=self.url,
            enabled=self.enabled,
            created_by=laid.caller.id,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class TheChannelNode(Then[AChannelAndACaller, NotificationChannelNode]):
    """미리 만들어 둔 채널이 통째로 반환된다. 수정 요청은 바뀌어야 하는 필드만 인자로 준다."""

    started: datetime
    named: str | Kept = KEPT
    described: str | None | Kept = KEPT
    url: str | Kept = KEPT
    enabled: bool | Kept = KEPT

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 채널 전체가 반환됩니다",
            english="the whole channel created in advance comes back",
        )

    @override
    def look(
        self, laid: AChannelAndACaller, answered: Answered[NotificationChannelNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        seed = laid.channel
        return channel_verdicts(
            "",
            node,
            name=seed.name if isinstance(self.named, Kept) else self.named,
            description=seed.description if isinstance(self.described, Kept) else self.described,
            channel_type=seed.channel_type,
            url=WEBHOOK_URL if isinstance(self.url, Kept) else self.url,
            enabled=seed.enabled if isinstance(self.enabled, Kept) else self.enabled,
            created_by=seed.created_by,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class TheLaidChannelsAreLeft(Then[ManyChannelsAndACaller, SearchNotificationChannelsPayload]):
    """응답에 나와야 하는 채널이 모두, 그리고 그것만 반환된다."""

    @override
    def says(self) -> str:
        return Says(
            "응답에 나와야 하는 채널만 반환됩니다",
            english="only the channels that must appear in the response come back",
        )

    @override
    def look(
        self, laid: ManyChannelsAndACaller, answered: Answered[SearchNotificationChannelsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same(
                "items",
                sorted(one.name for one in page.items),
                sorted(one.name for one in laid.laid),
            ),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheNamedChannelIsLeft(Then[ManyChannelsAndACaller, SearchNotificationChannelsPayload]):
    """필터에 맞는 그 하나만 반환된다."""

    @override
    def says(self) -> str:
        return Says(
            "필터에 맞는 채널 하나만 반환됩니다",
            english="only the one channel matching the filter comes back",
        )

    @override
    def look(
        self, laid: ManyChannelsAndACaller, answered: Answered[SearchNotificationChannelsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("items", [one.name for one in page.items], [laid.named.name]),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheFirstChannelPage(Then[ManyChannelsAndACaller, SearchNotificationChannelsPayload]):
    """한 건짜리 첫 페이지. 한 건이 반환되고 다음 페이지가 있다고 응답한다."""

    @override
    def says(self) -> str:
        return Says(
            "한 건짜리 첫 페이지가 반환됩니다",
            english="the first page holding one item comes back",
        )

    @override
    def look(
        self, laid: ManyChannelsAndACaller, answered: Answered[SearchNotificationChannelsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("len(items)", len(page.items), 1),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, True),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheChannelsInTheOrderAsked(Then[ManyChannelsAndACaller, LoadedChannels]):
    """요청한 순서대로 한 항목씩 반환된다. 미리 만들어 둔 것은 노드로, 없는 id는 빈 항목으로."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "요청한 순서대로 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다",
            english="they come back in the order asked and the item for an unknown id is empty",
        )

    @override
    def look(
        self, laid: ManyChannelsAndACaller, answered: Answered[LoadedChannels]
    ) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        written = WrittenByThisRun(self.started)
        asked = len(laid.laid) + 1
        seen: list[Verdict] = [Same("len(items)", len(items), asked)]
        for i, expected in enumerate(laid.laid):
            got = items[i] if i < len(items) else None
            if not isinstance(got, NotificationChannelNode):
                seen.append(Same(f"items[{i}]", got, Says("노드", english="a node")))
                continue
            seen.extend(
                channel_verdicts(
                    f"items[{i}].",
                    got,
                    name=expected.name,
                    description=expected.description,
                    channel_type=expected.channel_type,
                    url=WEBHOOK_URL,
                    enabled=expected.enabled,
                    created_by=expected.created_by,
                    written=written,
                )
            )
        last = items[asked - 1] if len(items) >= asked else Says("없음", english="none")
        seen.append(Same(f"items[{asked - 1}]", last, None))
        return seen


@dataclass(frozen=True)
class EachItemIsRefused(Then[Any, list[Any]]):
    """요청한 id마다 권한 부족 거부가 담긴다."""

    asked: int

    @override
    def says(self) -> str:
        return Says(
            "항목마다 권한 부족 거부가 담깁니다",
            english="each item carries a rejection for not enough permission",
        )

    @override
    def look(self, laid: Any, answered: Answered[list[Any]]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        seen: list[Verdict] = [Same("len(items)", len(items), self.asked)]
        for i in range(self.asked):
            got = items[i] if i < len(items) else None
            seen.append(
                Same(
                    f"items[{i}]",
                    type(got).__name__ if got is not None else None,
                    NotEnoughPermission.__name__,
                )
            )
        return seen


@dataclass(frozen=True)
class NothingComesBack(Then[Any, list[Any]]):
    """빈 응답이 반환된다."""

    @override
    def says(self) -> str:
        return Says("빈 응답이 반환됩니다", english="an empty response comes back")

    @override
    def look(self, laid: Any, answered: Answered[list[Any]]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same("items", items, [])]


@dataclass(frozen=True)
class TheDeletedChannelId(Then[AChannelAndACaller, Any]):
    """삭제한 채널의 id를 담은 응답."""

    @override
    def says(self) -> str:
        return Says(
            "삭제한 채널의 id 가 반환됩니다",
            english="the id of the deleted channel comes back",
        )

    @override
    def look(self, laid: AChannelAndACaller, answered: Answered[Any]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Held[UUID](
                "id",
                payload.id,
                SameAs[UUID](
                    laid.channel.id,
                    Says("미리 저장한 채널", english="the channel created in advance"),
                ),
            )
        ]


@dataclass(frozen=True)
class TheValidatedChannelId(Then[AChannelAndACaller, Any]):
    """검증한 채널의 id를 담은 응답."""

    @override
    def says(self) -> str:
        return Says(
            "검증한 채널의 id 가 반환됩니다",
            english="the id of the validated channel comes back",
        )

    @override
    def look(self, laid: AChannelAndACaller, answered: Answered[Any]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Held[UUID](
                "id",
                payload.id,
                SameAs[UUID](
                    laid.channel.id,
                    Says("미리 저장한 채널", english="the channel created in advance"),
                ),
            )
        ]


@dataclass(frozen=True)
class TheNewRuleNode(Then[AChannelAndACaller, NotificationRuleNode]):
    """방금 생성한 규칙이 통째로 반환된다. 기대값은 요청이 지정한 값에서 읽는다."""

    started: datetime
    named: str
    channel_id: UUID | None = None
    """None이면 미리 만들어 둔 채널을 가리킨다."""
    rule_type: NotificationRuleType = NotificationRuleType.SESSION_STARTED
    message_template: str = TEMPLATE
    enabled: bool = True

    @override
    def says(self) -> str:
        return Says(
            "생성한 규칙 전체가 반환됩니다",
            english="the whole rule just created comes back",
        )

    @override
    def look(
        self, laid: AChannelAndACaller, answered: Answered[NotificationRuleNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return rule_verdicts(
            "",
            node,
            name=self.named,
            description=None,
            rule_type=self.rule_type,
            channel_id=laid.channel.id if self.channel_id is None else self.channel_id,
            message_template=self.message_template,
            enabled=self.enabled,
            created_by=laid.caller.id,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class TheRuleNode(Then[ARuleAndACaller, NotificationRuleNode]):
    """미리 만들어 둔 규칙이 통째로 반환된다. 수정 요청은 바뀌어야 하는 필드만 인자로 준다."""

    started: datetime
    named: str | Kept = KEPT
    described: str | None | Kept = KEPT
    message_template: str | Kept = KEPT
    enabled: bool | Kept = KEPT

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 규칙 전체가 반환됩니다",
            english="the whole rule created in advance comes back",
        )

    @override
    def look(
        self, laid: ARuleAndACaller, answered: Answered[NotificationRuleNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        seed = laid.rule
        return rule_verdicts(
            "",
            node,
            name=seed.name if isinstance(self.named, Kept) else self.named,
            description=seed.description if isinstance(self.described, Kept) else self.described,
            rule_type=seed.rule_type,
            channel_id=seed.channel_id,
            message_template=(
                seed.message_template
                if isinstance(self.message_template, Kept)
                else self.message_template
            ),
            enabled=seed.enabled if isinstance(self.enabled, Kept) else self.enabled,
            created_by=seed.created_by,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class TheLaidRulesAreLeft(Then[ManyRulesAndACaller, SearchNotificationRulesPayload]):
    """응답에 나와야 하는 규칙이 모두, 그리고 그것만 반환된다."""

    @override
    def says(self) -> str:
        return Says(
            "응답에 나와야 하는 규칙만 반환됩니다",
            english="only the rules that must appear in the response come back",
        )

    @override
    def look(
        self, laid: ManyRulesAndACaller, answered: Answered[SearchNotificationRulesPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same(
                "items",
                sorted(one.name for one in page.items),
                sorted(one.name for one in laid.laid),
            ),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheNamedRuleIsLeft(Then[ManyRulesAndACaller, SearchNotificationRulesPayload]):
    """필터에 맞는 그 하나만 반환된다."""

    @override
    def says(self) -> str:
        return Says(
            "필터에 맞는 규칙 하나만 반환됩니다",
            english="only the one rule matching the filter comes back",
        )

    @override
    def look(
        self, laid: ManyRulesAndACaller, answered: Answered[SearchNotificationRulesPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("items", [one.name for one in page.items], [laid.named.name]),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheRulesInTheOrderAsked(Then[ManyRulesAndACaller, LoadedRules]):
    """요청한 순서대로 한 항목씩 반환된다. 미리 만들어 둔 것은 노드로, 없는 id는 빈 항목으로."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "요청한 순서대로 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다",
            english="they come back in the order asked and the item for an unknown id is empty",
        )

    @override
    def look(self, laid: ManyRulesAndACaller, answered: Answered[LoadedRules]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        written = WrittenByThisRun(self.started)
        asked = len(laid.laid) + 1
        seen: list[Verdict] = [Same("len(items)", len(items), asked)]
        for i, expected in enumerate(laid.laid):
            got = items[i] if i < len(items) else None
            if not isinstance(got, NotificationRuleNode):
                seen.append(Same(f"items[{i}]", got, Says("노드", english="a node")))
                continue
            seen.extend(
                rule_verdicts(
                    f"items[{i}].",
                    got,
                    name=expected.name,
                    description=expected.description,
                    rule_type=expected.rule_type,
                    channel_id=expected.channel_id,
                    message_template=expected.message_template,
                    enabled=expected.enabled,
                    created_by=expected.created_by,
                    written=written,
                )
            )
        last = items[asked - 1] if len(items) >= asked else Says("없음", english="none")
        seen.append(Same(f"items[{asked - 1}]", last, None))
        return seen


@dataclass(frozen=True)
class TheDeletedRuleId(Then[ARuleAndACaller, Any]):
    """삭제한 규칙의 id를 담은 응답."""

    @override
    def says(self) -> str:
        return Says(
            "삭제한 규칙의 id 가 반환됩니다",
            english="the id of the deleted rule comes back",
        )

    @override
    def look(self, laid: ARuleAndACaller, answered: Answered[Any]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Held[UUID](
                "id",
                payload.id,
                SameAs[UUID](
                    laid.rule.id,
                    Says("미리 저장한 규칙", english="the rule created in advance"),
                ),
            )
        ]


@dataclass(frozen=True)
class TheRenderedMessage(Then[ARuleAndACaller, ValidateNotificationRulePayload]):
    """템플릿에 시험 데이터를 넣어 만든 문자열이 반환된다."""

    rendered: str

    @override
    def says(self) -> str:
        return Says(
            "템플릿에 데이터를 넣어 만든 문자열이 반환됩니다",
            english="the string made by putting the data into the template comes back",
        )

    @override
    def look(
        self, laid: ARuleAndACaller, answered: Answered[ValidateNotificationRulePayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same("message", payload.message, self.rendered)]


@dataclass(frozen=True)
class TheChannelsComeBack(
    Then[ManyChannelsAndACaller, PartialBulkPayload[NotificationChannelNode]]
):
    """미리 만들어 둔 채널이 모두 처리된 목록에 온다. ``missing``이 있으면 그 id 만 실패 목록에 온다."""

    started: datetime
    described: str | None | Kept = KEPT
    missing: UUID | None = None

    @override
    def says(self) -> str:
        if self.missing is None:
            return Says(
                "미리 저장한 채널이 모두 처리된 목록에 오고, 실패한 것은 없습니다",
                english=(
                    "every channel created in advance comes back in the processed list "
                    "and nothing failed"
                ),
            )
        return Says(
            "미리 저장한 채널이 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 "
            "실패 목록에 옵니다",
            english=(
                "every channel created in advance comes back in the processed list and an unknown "
                "id comes back in the failed list because no target answers to it"
            ),
        )

    @override
    def look(
        self,
        laid: ManyChannelsAndACaller,
        answered: Answered[PartialBulkPayload[NotificationChannelNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.laid))]
        for i, (node, seed) in enumerate(zip(payload.successes, laid.laid, strict=False)):
            verdicts += channel_verdicts(
                f"successes[{i}].",
                node,
                name=seed.name,
                description=(
                    seed.description if isinstance(self.described, Kept) else self.described
                ),
                channel_type=seed.channel_type,
                url=WEBHOOK_URL,
                enabled=seed.enabled,
                created_by=seed.created_by,
                written=written,
            )
        return verdicts + failed_verdicts(payload, self.missing)


@dataclass(frozen=True)
class TheRulesComeBack(Then[ManyRulesAndACaller, PartialBulkPayload[NotificationRuleNode]]):
    """미리 만들어 둔 규칙이 모두 처리된 목록에 온다. ``missing``이 있으면 그 id 만 실패 목록에 온다."""

    started: datetime
    described: str | None | Kept = KEPT
    missing: UUID | None = None

    @override
    def says(self) -> str:
        if self.missing is None:
            return Says(
                "미리 저장한 규칙이 모두 처리된 목록에 오고, 실패한 것은 없습니다",
                english=(
                    "every rule created in advance comes back in the processed list "
                    "and nothing failed"
                ),
            )
        return Says(
            "미리 저장한 규칙이 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 "
            "실패 목록에 옵니다",
            english=(
                "every rule created in advance comes back in the processed list and an unknown id "
                "comes back in the failed list because no target answers to it"
            ),
        )

    @override
    def look(
        self,
        laid: ManyRulesAndACaller,
        answered: Answered[PartialBulkPayload[NotificationRuleNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.laid))]
        for i, (node, seed) in enumerate(zip(payload.successes, laid.laid, strict=False)):
            verdicts += rule_verdicts(
                f"successes[{i}].",
                node,
                name=seed.name,
                description=(
                    seed.description if isinstance(self.described, Kept) else self.described
                ),
                rule_type=seed.rule_type,
                channel_id=seed.channel_id,
                message_template=seed.message_template,
                enabled=seed.enabled,
                created_by=seed.created_by,
                written=written,
            )
        return verdicts + failed_verdicts(payload, self.missing)


def failed_verdicts(payload: PartialBulkPayload[Any], missing: UUID | None) -> list[Verdict]:
    """The failed list of a partial bulk answer: empty, or the one id nothing answers to."""
    if missing is None:
        return [Same("failed", payload.failed, [])]
    verdicts: list[Verdict] = [Same("failed count", len(payload.failed), 1)]
    for failure in payload.failed:
        verdicts += [
            Held[UUID](
                "failed[0].id",
                failure.id,
                SameAs(
                    missing,
                    Says("요청에 넣은 없는 id", english="the unknown id put in the request"),
                ),
            ),
            Held("failed[0].message", failure.message, Mentions("not found")),
        ]
    return verdicts


@dataclass(frozen=True)
class NothingIsProcessed(Then[Any, PartialBulkPayload[Any]]):
    """처리된 것 없이, 미리 만들어 둔 것이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return Says(
            "처리된 것 없이 미리 저장한 것이 모두 실패 목록에 옵니다",
            english=(
                "nothing is processed and everything created in advance comes back in the "
                "failed list"
            ),
        )

    @override
    def look(self, laid: Any, answered: Answered[PartialBulkPayload[Any]]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        targets = laid.laid
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(targets)),
        ]
        for i, (failure, seed) in enumerate(zip(payload.failed, targets, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(
                        seed.id,
                        Says(
                            "미리 저장한 것의 id",
                            english="the id of the thing created in advance",
                        ),
                    ),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
