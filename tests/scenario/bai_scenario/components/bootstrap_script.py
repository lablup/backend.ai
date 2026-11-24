"""bootstrap script 를 가진 사용자 한 명과, script 와 revision 노드를 통째로 보는 검사."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.dto.manager.v2.bootstrap_script.response import (
    BootstrapScriptNode,
    BootstrapScriptRevisionNode,
)
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptRevisionData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Language,
    Same,
    SameAs,
    Says,
    Skipped,
    Then,
    Verdict,
    in_language,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.user import AGrant
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.user.bootstrap_script import (
    TestSeedBootstrapScriptOf,
    TestSeedDefaultBootstrapScriptOf,
)

DEFAULT_SCRIPT = "echo default"
"""사용자의 default bootstrap script 의 revision 1 내용."""

EXTRA_SCRIPT = "echo extra"
"""default 가 아닌 bootstrap script 의 revision 1 내용."""

STRANGER_SCRIPT = "echo stranger"
"""같은 도메인의 다른 사용자가 가진 bootstrap script 의 revision 1 내용."""

NEW_SCRIPT = "echo new"
"""요청으로 새로 쓰는 내용."""


@dataclass(frozen=True)
class BootstrapScriptHolder:
    """자기 bootstrap script 를 다룰 사용자와, 그 사람이 가진 default script 와 default 아닌 script.

    script 는 각자의 revision 1 로 들고 있다. ``stranger`` 는 같은 도메인의 다른 사용자가 가진 script 다.
    """

    caller: UserData
    default: BootstrapScriptRevisionData
    extra: BootstrapScriptRevisionData
    stranger: BootstrapScriptRevisionData | None

    def stranger_script(self) -> BootstrapScriptRevisionData:
        if self.stranger is None:
            raise LookupError("the stranger's bootstrap script was not seeded")
        return self.stranger


@dataclass(frozen=True)
class SomeoneWithBootstrapScripts(Given[Any, BootstrapScriptHolder]):
    """자기 bootstrap script 를 다룰 사용자 한 명. 자기 사용자에 받은 권한과, 다른 사용자의 script 가 있는지를 고른다."""

    permissions: Sequence[Permission] = ()
    stranger: bool = False

    @override
    def describe(self) -> str:
        if self.permissions:
            names = ", ".join(str(one.name) for one in self.permissions)
            granted = Says(
                f"자기 사용자에 {names} 권한을 받았습니다",
                english=f"the user holds the {names} permission on their own user",
            )
        else:
            granted = Says("아무 권한도 받지 않았습니다", english="the user holds no permission")
        others = (
            Says(
                ", 같은 도메인의 다른 사용자도 bootstrap script 하나를 갖습니다",
                english=", and another user of the domain holds one bootstrap script",
            )
            if self.stranger
            else Says("", english="")
        )
        return Says(
            "도메인 하나와 default bootstrap script 하나, default 가 아닌 bootstrap script 하나를 "
            f"가진 사용자 한 명{others}, 그 사용자는 {granted}",
            english=(
                "one domain and one user holding one default bootstrap script and one that is "
                f"not the default{in_language(others, Language.ENGLISH)}, and "
                f"{in_language(granted, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> BootstrapScriptHolder:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain))
        default = await seeding.adding(TestSeedBootstrapScriptOf(script=DEFAULT_SCRIPT), caller)
        await seeding.adding(
            TestSeedDefaultBootstrapScriptOf(script_id=seeding.made(default).script_id), caller
        )
        extra = await seeding.adding(TestSeedBootstrapScriptOf(script=EXTRA_SCRIPT), caller)
        stranger = None
        if self.stranger:
            other = await seeding.within(SomeoneOf(domain))
            stranger = await seeding.adding(
                TestSeedBootstrapScriptOf(script=STRANGER_SCRIPT), other
            )
        if self.permissions:
            await seeding.within(AGrant.on_user(caller, caller, *self.permissions))
        return BootstrapScriptHolder(
            caller=seeding.made(caller),
            default=seeding.made(default),
            extra=seeding.made(extra),
            stranger=seeding.made(stranger) if stranger is not None else None,
        )


@dataclass(frozen=True)
class TheBootstrapScriptNode(Then[BootstrapScriptHolder, BootstrapScriptNode]):
    """심어 둔 script 하나가 통째로 온다. ``default`` 가 거짓이면 default 가 아닌 script 다."""

    started: datetime
    default: bool

    @override
    def says(self) -> str:
        return Says(
            "bootstrap script 전체가 응답으로 옵니다",
            english="the whole bootstrap script comes back",
        )

    @override
    def look(
        self, laid: BootstrapScriptHolder, answered: Answered[BootstrapScriptNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Same("raised", answered.raised, None)]
        return script_verdicts("", node, laid, self.started, self.default)


def script_verdicts(
    at: str,
    node: BootstrapScriptNode,
    laid: BootstrapScriptHolder,
    started: datetime,
    default: bool,
) -> list[Verdict]:
    seeded = laid.default if default else laid.extra
    which = (
        Says("심어 둔 default script", english="the seeded default script")
        if default
        else Says(
            "심어 둔 default 가 아닌 script", english="the seeded script that is not the default"
        )
    )
    return [
        Held[UUID](f"{at}id", node.id, SameAs(seeded.script_id, which)),
        Held[UUID](
            f"{at}field_id",
            node.field_id,
            SameAs(node.id, Says("응답의 id", english="the id in the response")),
        ),
        Held[UUID](
            f"{at}user_id",
            node.user_id,
            SameAs(laid.caller.id, Says("호출한 사용자", english="the calling user")),
        ),
        Held(f"{at}created_at", node.created_at, WrittenByThisRun(started)),
    ]


@dataclass(frozen=True)
class TheRevisionNode(Then[BootstrapScriptHolder, BootstrapScriptRevisionNode]):
    """이번 호출이 쓴 revision 이 통째로 온다.

    ``on_extra`` 가 참이면 default 가 아닌 script 에 붙은 revision 이고, 거짓이면 이번 호출이 새로 만든
    script 의 revision 이라 script id 를 견줄 행이 없다.
    """

    started: datetime
    revision_number: int
    on_extra: bool

    @override
    def says(self) -> str:
        return Says("revision 전체가 응답으로 옵니다", english="the whole revision comes back")

    @override
    def look(
        self, laid: BootstrapScriptHolder, answered: Answered[BootstrapScriptRevisionNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Same("raised", answered.raised, None)]
        generated = Says("데이터베이스가 만듭니다", english="the database generates it")
        script_id: Verdict = (
            Held[UUID](
                "script_id",
                node.script_id,
                SameAs(
                    laid.extra.script_id,
                    Says(
                        "심어 둔 default 가 아닌 script",
                        english="the seeded script that is not the default",
                    ),
                ),
            )
            if self.on_extra
            else Skipped("script_id", generated)
        )
        return [
            Skipped("id", generated),
            Held[UUID](
                "field_id",
                node.field_id,
                SameAs(node.id, Says("응답의 id", english="the id in the response")),
            ),
            script_id,
            Same("revision_number", node.revision_number, self.revision_number),
            Same("script", node.script, NEW_SCRIPT),
            Held[UUID | None](
                "creator_id",
                node.creator_id,
                SameAs(laid.caller.id, Says("호출한 사용자", english="the calling user")),
            ),
            Held("created_at", node.created_at, WrittenByThisRun(self.started)),
        ]


def default_revision_verdicts(
    at: str, node: BootstrapScriptRevisionNode, laid: BootstrapScriptHolder, started: datetime
) -> list[Verdict]:
    """심어 둔 default script 의 revision 1 이 통째로 왔는지."""
    return [
        Held[UUID](
            f"{at}id",
            node.id,
            SameAs(
                laid.default.id,
                Says(
                    "심어 둔 default script 의 revision 1",
                    english="revision 1 of the seeded default script",
                ),
            ),
        ),
        Held[UUID](
            f"{at}field_id",
            node.field_id,
            SameAs(node.id, Says("응답의 id", english="the id in the response")),
        ),
        Held[UUID](
            f"{at}script_id",
            node.script_id,
            SameAs(
                laid.default.script_id,
                Says("심어 둔 default script", english="the seeded default script"),
            ),
        ),
        Same(f"{at}revision_number", node.revision_number, 1),
        Same(f"{at}script", node.script, DEFAULT_SCRIPT),
        Held[UUID | None](
            f"{at}creator_id",
            node.creator_id,
            SameAs(laid.caller.id, Says("호출한 사용자", english="the calling user")),
        ),
        Held(f"{at}created_at", node.created_at, WrittenByThisRun(started)),
    ]
