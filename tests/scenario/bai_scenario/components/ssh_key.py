"""SSH 키를 가진 사용자 한 명과, 그 SSH 키 노드를 통째로 보는 검사."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.dto.manager.v2.ssh_key.response import SSHKeyNode
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
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
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.user import AGrant
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.ssh_key.ssh_key import TestSeedSSHKeyOf

DEFAULT_PUBLIC_KEY = (
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAII3oEkCHOFCltBkvsATl1upB3yfnsmzsvEhpbiVrYOQv"
)
"""사용자의 default SSH 키. 형식 검사를 통과하는 실제 공개키다."""

EXTRA_PUBLIC_KEY = (
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFYD/Yrss1np0I+R9f51bEJ0Jjs+d0s4JUussQhs0WBG"
)
"""default 가 아닌 SSH 키. 형식 검사를 통과하는 실제 공개키다."""


@dataclass(frozen=True)
class SSHKeyholder:
    """자기 SSH 키를 다룰 사용자와, 그 사람이 가진 default 키와 default 아닌 키."""

    caller: UserData
    default: SSHKeypairData | None
    extra: SSHKeypairData | None

    def default_key(self) -> SSHKeypairData:
        if self.default is None:
            raise LookupError("the default SSH key was not seeded")
        return self.default

    def extra_key(self) -> SSHKeypairData:
        if self.extra is None:
            raise LookupError("the extra SSH key was not seeded")
        return self.extra


@dataclass(frozen=True)
class SomeoneWithSSHKeys(Given[Any, SSHKeyholder]):
    """자기 SSH 키를 다룰 사용자 한 명. 자기 사용자에 받은 권한과 키를 가졌는지를 고른다."""

    permissions: Sequence[Permission] = ()
    holds_keys: bool = True

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
        if self.holds_keys:
            keys = Says(
                "default SSH 키 하나와 default 아닌 SSH 키 하나를 가진 사용자 한 명",
                english="one user holding one default SSH key and one SSH key that is not the default",
            )
        else:
            keys = Says("SSH 키가 없는 사용자 한 명", english="one user holding no SSH key")
        return Says(
            f"도메인 하나와 {keys}, 그 사용자는 {granted}",
            english=(
                f"one domain and {in_language(keys, Language.ENGLISH)}, and "
                f"{in_language(granted, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> SSHKeyholder:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain))
        default = extra = None
        if self.holds_keys:
            default = await seeding.adding(
                TestSeedSSHKeyOf(public_key=DEFAULT_PUBLIC_KEY, is_default=True), caller
            )
            extra = await seeding.adding(
                TestSeedSSHKeyOf(public_key=EXTRA_PUBLIC_KEY, is_default=False), caller
            )
        if self.permissions:
            await seeding.within(AGrant.on_user(caller, caller, *self.permissions))
        return SSHKeyholder(
            caller=seeding.made(caller),
            default=seeding.made(default) if default is not None else None,
            extra=seeding.made(extra) if extra is not None else None,
        )


@dataclass(frozen=True)
class TheSSHKeyNode(Then[SSHKeyholder, SSHKeyNode]):
    """방금 다룬 SSH 키가 통째로 온다.

    ``seeded`` 가 거짓이면 이번 호출이 새로 만든 키라서 id 를 견줄 행이 없다.
    """

    started: datetime
    public_key: str
    is_default: bool
    seeded: bool = True

    @override
    def says(self) -> str:
        return Says("SSH 키 전체가 응답으로 옵니다", english="the whole SSH key comes back")

    @override
    def look(self, laid: SSHKeyholder, answered: Answered[SSHKeyNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Same("raised", answered.raised, None)]
        if self.seeded:
            seeded = laid.extra_key() if self.public_key == EXTRA_PUBLIC_KEY else laid.default_key()
            id_verdict: Verdict = Held(
                "id",
                node.id,
                SameAs(seeded.id, Says("심어 둔 그 SSH 키", english="the seeded SSH key")),
            )
        else:
            id_verdict = Skipped(
                "id", Says("데이터베이스가 만듭니다", english="the database generates it")
            )
        return [
            id_verdict,
            Held[UUID](
                "field_id",
                node.field_id,
                SameAs(node.id, Says("응답의 id", english="the id in the response")),
            ),
            Held(
                "user_id",
                node.user_id,
                SameAs(laid.caller.id, Says("호출한 사용자", english="the calling user")),
            ),
            Same("public_key", node.public_key, self.public_key),
            Same("is_default", node.is_default, self.is_default),
        ]
