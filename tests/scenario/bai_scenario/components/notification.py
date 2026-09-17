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
from ai.backend.manager.data.notification import NotificationChannelData, NotificationRuleData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.system import KEPT, Kept, lay_a_caller, role_named
from bai_scenario.seeds.notification.channel import (
    FROM_EMAIL,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USERNAME,
    TO_EMAIL,
    WEBHOOK_URL,
    SeedEmailChannel,
    SeedWebhookChannel,
)
from bai_scenario.seeds.notification.rule import TEMPLATE, SeedRuleOf, SeedRuleOfNoChannel

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
        return f"{self.channel_type.value} 채널 하나와, {role_named(self.role)} 한 명"

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
        return f"채널 하나와 그것을 가리키는 규칙 하나, 그리고 {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> AChannelAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        channel = await seeding.creating_from(SeedWebhookChannel(), caller)
        await seeding.creating_from_two(SeedRuleOf(), channel, caller)
        return AChannelAndACaller(seeding.made(channel), seeding.made(caller))


@dataclass(frozen=True)
class TwoChannelsAndSomeone(Given[Any, ManyChannelsAndACaller]):
    """webhook 채널 둘과 사용자 한 명. ``named``는 앞의 것이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"webhook 채널 둘과, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyChannelsAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        wanted = await seeding.creating_from(SeedWebhookChannel(name_hint="wanted"), caller)
        other = await seeding.creating_from(SeedWebhookChannel(name_hint="other"), caller)
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
        return f"webhook 채널 하나와 email 채널 하나, 그리고 {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyChannelsAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        webhook = await seeding.creating_from(SeedWebhookChannel(), caller)
        email = await seeding.creating_from(SeedEmailChannel(), caller)
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
        return f"활성 webhook 채널 하나와 비활성 하나, 그리고 {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyChannelsAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        active = await seeding.creating_from(SeedWebhookChannel(), caller)
        await seeding.creating_from(SeedWebhookChannel(enabled=False), caller)
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
        return f"규칙 하나와 그것이 가리키는 webhook 채널, 그리고 {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ARuleAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        channel = await seeding.creating_from(SeedWebhookChannel(), caller)
        rule = await seeding.creating_from_two(
            SeedRuleOf(
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
        return f"없는 채널 id를 가리키는 규칙 하나와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ARuleAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        channel = await seeding.creating_from(SeedWebhookChannel(), caller)
        rule = await seeding.creating_from(SeedRuleOfNoChannel(), caller)
        return ARuleAndACaller(seeding.made(rule), seeding.made(channel), seeding.made(caller))


@dataclass(frozen=True)
class TwoRulesAndSomeone(Given[Any, ManyRulesAndACaller]):
    """같은 채널을 가리키는 규칙 둘과 사용자 한 명. ``named``는 앞의 것이다."""

    role: UserRole = UserRole.USER
    other_rule_type: NotificationRuleType = NotificationRuleType.SESSION_STARTED

    @override
    def describe(self) -> str:
        return f"같은 webhook 채널을 가리키는 규칙 둘과, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyRulesAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        channel = await seeding.creating_from(SeedWebhookChannel(), caller)
        wanted = await seeding.creating_from_two(SeedRuleOf(name_hint="wanted"), channel, caller)
        other = await seeding.creating_from_two(
            SeedRuleOf(name_hint="other", rule_type=self.other_rule_type), channel, caller
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
        return f"활성 규칙 하나와 비활성 하나, 그리고 {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyRulesAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        channel = await seeding.creating_from(SeedWebhookChannel(), caller)
        active = await seeding.creating_from_two(SeedRuleOf(), channel, caller)
        await seeding.creating_from_two(SeedRuleOf(enabled=False), channel, caller)
        return ManyRulesAndACaller(
            laid=(seeding.made(active),),
            named=seeding.made(active),
            caller=seeding.made(caller),
        )


def _channel_seed(
    given: AChannelAndSomeone, name_hint: str
) -> SeedWebhookChannel | SeedEmailChannel:
    match given.channel_type:
        case NotificationChannelType.WEBHOOK:
            return SeedWebhookChannel(
                name_hint=name_hint, description=given.description, enabled=given.enabled
            )
        case NotificationChannelType.EMAIL:
            return SeedEmailChannel(name_hint=name_hint, enabled=given.enabled)


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
        Skipped(f"{prefix}spec.auth.password", "응답 타입에 그 자리가 없다"),
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
        Skipped(f"{prefix}id", "데이터베이스가 만든다"),
        Same(f"{prefix}name", node.name, name),
        Same(f"{prefix}description", node.description, description),
        Same(f"{prefix}channel_type", node.channel_type.value, channel_type.value),
        *spec,
        Same(f"{prefix}enabled", node.enabled, enabled),
        Held[UUID](f"{prefix}created_by", node.created_by, SameAs[UUID](created_by, "만든 사람")),
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
        Skipped(f"{prefix}id", "데이터베이스가 만든다"),
        Same(f"{prefix}name", node.name, name),
        Same(f"{prefix}description", node.description, description),
        Same(f"{prefix}rule_type", node.rule_type.value, rule_type.value),
        Held[UUID](
            f"{prefix}channel_id", node.channel_id, SameAs[UUID](channel_id, "가리키는 채널")
        ),
        Same(f"{prefix}message_template", node.message_template, message_template),
        Same(f"{prefix}enabled", node.enabled, enabled),
        Held[UUID](f"{prefix}created_by", node.created_by, SameAs[UUID](created_by, "만든 사람")),
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
        return "생성한 채널 전체가 반환된다"

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
        return "미리 만들어 둔 채널 전체가 반환된다"

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
        return "응답에 나와야 하는 채널만 반환된다"

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
        return "필터에 맞는 채널 하나만 반환된다"

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
        return "한 건짜리 첫 페이지가 반환된다"

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
        return "요청한 순서대로 반환되고, 없는 id에 해당하는 항목은 비어 있다"

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
                seen.append(Same(f"items[{i}]", got, "노드"))
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
        last = items[asked - 1] if len(items) >= asked else "없음"
        seen.append(Same(f"items[{asked - 1}]", last, None))
        return seen


@dataclass(frozen=True)
class EachItemIsRefused(Then[Any, list[Any]]):
    """요청한 id마다 권한 부족 거부가 담긴다."""

    asked: int

    @override
    def says(self) -> str:
        return "항목마다 권한 부족 거부가 담긴다"

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
        return "빈 응답이 반환된다"

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
        return "삭제한 채널의 id가 반환된다"

    @override
    def look(self, laid: AChannelAndACaller, answered: Answered[Any]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Held[UUID]("id", payload.id, SameAs[UUID](laid.channel.id, "미리 만들어 둔 채널"))]


@dataclass(frozen=True)
class TheValidatedChannelId(Then[AChannelAndACaller, Any]):
    """검증한 채널의 id를 담은 응답."""

    @override
    def says(self) -> str:
        return "검증한 채널의 id가 반환된다"

    @override
    def look(self, laid: AChannelAndACaller, answered: Answered[Any]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Held[UUID]("id", payload.id, SameAs[UUID](laid.channel.id, "미리 만들어 둔 채널"))]


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
        return "생성한 규칙 전체가 반환된다"

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
        return "미리 만들어 둔 규칙 전체가 반환된다"

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
        return "응답에 나와야 하는 규칙만 반환된다"

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
        return "필터에 맞는 규칙 하나만 반환된다"

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
        return "요청한 순서대로 반환되고, 없는 id에 해당하는 항목은 비어 있다"

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
                seen.append(Same(f"items[{i}]", got, "노드"))
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
        last = items[asked - 1] if len(items) >= asked else "없음"
        seen.append(Same(f"items[{asked - 1}]", last, None))
        return seen


@dataclass(frozen=True)
class TheDeletedRuleId(Then[ARuleAndACaller, Any]):
    """삭제한 규칙의 id를 담은 응답."""

    @override
    def says(self) -> str:
        return "삭제한 규칙의 id가 반환된다"

    @override
    def look(self, laid: ARuleAndACaller, answered: Answered[Any]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Held[UUID]("id", payload.id, SameAs[UUID](laid.rule.id, "미리 만들어 둔 규칙"))]


@dataclass(frozen=True)
class TheRenderedMessage(Then[ARuleAndACaller, ValidateNotificationRulePayload]):
    """템플릿에 시험 데이터를 넣어 만든 문자열이 반환된다."""

    rendered: str

    @override
    def says(self) -> str:
        return "템플릿에 데이터를 넣어 만든 문자열이 반환된다"

    @override
    def look(
        self, laid: ARuleAndACaller, answered: Answered[ValidateNotificationRulePayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same("message", payload.message, self.rendered)]
