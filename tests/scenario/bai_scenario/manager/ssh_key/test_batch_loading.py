"""SSH 키를 DataLoader 용으로 id 로 함께 읽기. 소유 사용자마다 권한을 본다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.ssh_key.response import SSHKeyNode
from ai.backend.manager.api.adapters.ssh_key.adapter import SSHKeyAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.errors.permission import NotEnoughPermission
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
from bai_scenario.components.ssh_key import (
    SomeoneWithSSHKeys,
    SSHKeyholder,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[SSHKeyNode | Exception | None]
type LoadingStep = Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, Answer]


def _node_verdicts(
    at: int, node: SSHKeyNode | Exception | None, seeded: SSHKeypairData, laid: SSHKeyholder
) -> list[Verdict]:
    """The node at ``at`` is the seeded key, whole."""
    if not isinstance(node, SSHKeyNode):
        return [Same(f"[{at}]", type(node).__name__, "SSHKeyNode")]
    name = Says("심어 둔 그 SSH 키", english="the seeded SSH key")
    return [
        Held(f"[{at}].id", node.id, SameAs(seeded.id, name)),
        Held(f"[{at}].field_id", node.field_id, SameAs(seeded.id, name)),
        Held[UUID](
            f"[{at}].user_id",
            node.user_id,
            SameAs(laid.caller.id, Says("호출한 사용자", english="the calling user")),
        ),
        Same(f"[{at}].public_key", node.public_key, seeded.public_key),
        Same(f"[{at}].is_default", node.is_default, seeded.is_default),
    ]


@dataclass(frozen=True)
class LoadingMyKeys(When[SSHKeyholder, SSHKeyAdapter, Answer]):
    """자기 default 키와 default 아닌 키를 id 로 함께 읽는다."""

    @override
    def operation(self) -> str:
        return "bulk_get_ids"

    @override
    def describe(self, laid: SSHKeyholder) -> str:
        return Says(
            f"{laid.caller.username}이 자기 SSH 키 둘을 id 로 함께 읽습니다",
            english=f"{laid.caller.username} loads two of their own SSH keys by id together",
        )

    @override
    async def call(self, adapter: SSHKeyAdapter, laid: SSHKeyholder) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.bulk_get_ids([laid.default_key().id, laid.extra_key().id])


@dataclass(frozen=True)
class LoadingMineAndAnothers(When[SSHKeyholder, SSHKeyAdapter, Answer]):
    """자기 default 키와 다른 사용자의 키를 id 로 함께 읽는다."""

    @override
    def operation(self) -> str:
        return "bulk_get_ids"

    @override
    def describe(self, laid: SSHKeyholder) -> str:
        return Says(
            f"{laid.caller.username}이 자기 SSH 키와 다른 사용자의 SSH 키를 id 로 함께 읽습니다",
            english=(
                f"{laid.caller.username} loads their own SSH key and another user's SSH key by "
                "id together"
            ),
        )

    @override
    async def call(self, adapter: SSHKeyAdapter, laid: SSHKeyholder) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.bulk_get_ids([laid.default_key().id, laid.stranger_key().id])


@dataclass(frozen=True)
class BothKeys(Then[SSHKeyholder, Answer]):
    @override
    def says(self) -> str:
        return Says(
            "두 SSH 키가 요청한 순서대로 옵니다",
            english="both SSH keys come back in the order asked",
        )

    @override
    def look(self, laid: SSHKeyholder, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 2)]
        if len(loaded) == 2:
            seen.extend(_node_verdicts(0, loaded[0], laid.default_key(), laid))
            seen.extend(_node_verdicts(1, loaded[1], laid.extra_key(), laid))
        return seen


@dataclass(frozen=True)
class MineAndADenial(Then[SSHKeyholder, Answer]):
    @override
    def says(self) -> str:
        return Says(
            "자기 SSH 키는 오고, 다른 사용자의 SSH 키 자리에는 거부가 옵니다",
            english=(
                "their own SSH key comes back, and a rejection stands in the place of the other "
                "user's SSH key"
            ),
        )

    @override
    def look(self, laid: SSHKeyholder, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 2)]
        if len(loaded) == 2:
            seen.extend(_node_verdicts(0, loaded[0], laid.default_key(), laid))
            second = loaded[1]
            seen.append(
                Refused(NotEnoughPermission, second if isinstance(second, Exception) else None)
            )
        return seen


@dataclass(frozen=True)
class AUserGrantedReadLoadsTheirKeys(
    Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-loads-their-own-keys"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 권한을 받은 사용자가 자기 SSH 키 둘을 id 로 함께 읽으면 둘 다 옵니다",
            english=(
                "when a user granted READ on their own user loads two of their own SSH keys by "
                "id, both come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SSHKeyholder]:
        return SomeoneWithSSHKeys(permissions=(Permission.READ,))

    @override
    def when(self) -> When[SSHKeyholder, SSHKeyAdapter, Answer]:
        return LoadingMyKeys()

    @override
    def then(self) -> Then[SSHKeyholder, Answer]:
        return BothKeys()


@dataclass(frozen=True)
class AUserGrantedReadIsDeniedAnothersKey(
    Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-is-denied-another-users-key"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 권한을 받은 사용자가 자기 SSH 키와 다른 사용자의 SSH 키를 함께 "
            "읽으면, 다른 사용자의 키만 거부됩니다",
            english=(
                "when a user granted READ on their own user loads their own SSH key together "
                "with another user's, only the other user's key is rejected"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SSHKeyholder]:
        return SomeoneWithSSHKeys(permissions=(Permission.READ,), with_stranger=True)

    @override
    def when(self) -> When[SSHKeyholder, SSHKeyAdapter, Answer]:
        return LoadingMineAndAnothers()

    @override
    def then(self) -> Then[SSHKeyholder, Answer]:
        return MineAndADenial()


SCENARIOS: list[LoadingStep] = [
    AUserGrantedReadLoadsTheirKeys(),
    AUserGrantedReadIsDeniedAnothersKey(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: LoadingStep, adapter: SSHKeyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
