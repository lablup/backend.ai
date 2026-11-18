"""What a storage host scenario table says besides the call."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.storage_host.response import (
    MyStorageHostPermissionsPayload,
)
from ai.backend.common.types import VFolderHostPermission
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Says,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.vfolder import STORAGE_HOST, SomeoneHoldingFolderPermissions
from bai_scenario.seeds.domain.domain import TestSeedDomain

ALL_HOST_PERMISSIONS = sorted(VFolderHostPermission, key=lambda one: one.value)
"""What a domain and a keypair policy grant on a host they both name."""


@dataclass(frozen=True)
class AViewerAndTheirHosts:
    """부를 사람과, 그 사람이 볼 수 있어야 하는 호스트."""

    domain: DomainData
    caller: UserData


@dataclass(frozen=True)
class HostsOfSomeone(Given[Any, AViewerAndTheirHosts]):
    """도메인과 키페어 정책이 각각 허용하는 호스트가 다른 사용자.

    저장소가 등록한 볼륨은 ``local:volume1`` 하나뿐이다. ``granted``이면 그 사용자가
    자기 스코프에서 vfolder 읽기 권한을 받는다.
    """

    domain_hosts: Sequence[str] = (STORAGE_HOST, "local:volume2")
    policy_hosts: Sequence[str] = (STORAGE_HOST,)
    granted: bool = True

    @override
    def describe(self) -> str:
        grant_ko = "vfolder 읽기 권한을 받은" if self.granted else "아무 권한도 받지 않은"
        grant_en = (
            "granted vfolder read in their own scope" if self.granted else "holding no permission"
        )
        return Says(
            f"도메인이 {', '.join(self.domain_hosts)} 를 허용하고 키페어 정책이 "
            f"{', '.join(self.policy_hosts)} 를 허용하는 자리의, {grant_ko} 사용자 한 명",
            english=(
                f"one user {grant_en} in a place where the domain allows "
                f"{', '.join(self.domain_hosts)} and the keypair policy allows "
                f"{', '.join(self.policy_hosts)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AViewerAndTheirHosts:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=self.domain_hosts)
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=self.policy_hosts))
        if self.granted:
            await seeding.within(
                SomeoneHoldingFolderPermissions(
                    caller, (Permission.READ,), name_hint="storage-host-reader"
                )
            )
        return AViewerAndTheirHosts(seeding.made(domain), seeding.made(caller))


@dataclass(frozen=True)
class TheHostsOnTheList(Then[AViewerAndTheirHosts, MyStorageHostPermissionsPayload]):
    """응답에 이 호스트들이 이 순서로, 각각 모든 권한과 함께 온다."""

    hosts: Sequence[str]

    @override
    def says(self) -> str:
        if not self.hosts:
            return Says("응답은 비어 있습니다", english="the answer is empty")
        return Says(
            f"{', '.join(self.hosts)} 만 응답으로 옵니다",
            english=f"only {', '.join(self.hosts)} come back",
        )

    @override
    def look(
        self, laid: AViewerAndTheirHosts, answered: Answered[MyStorageHostPermissionsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("items.length", len(payload.items), len(self.hosts))]
        for i, host in enumerate(self.hosts):
            if i >= len(payload.items):
                break
            verdicts.extend([
                Same(f"items[{i}].host", payload.items[i].host, host),
                Same(
                    f"items[{i}].permissions",
                    payload.items[i].permissions,
                    ALL_HOST_PERMISSIONS,
                ),
            ])
        return verdicts
