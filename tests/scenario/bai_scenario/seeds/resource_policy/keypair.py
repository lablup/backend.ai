"""Write specs for the resource policy a keypair is held to."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override
from uuid import uuid4

from ai.backend.common.data.entity.resource_policy import KeyPairResourcePolicyUUID
from ai.backend.common.types import (
    DefaultForUnspecified,
    ResourceSlot,
    VFolderHostPermission,
    VFolderHostPermissionMap,
)
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.creators import KeyPairResourcePolicyCreator
from ai.backend.manager.models.resource_policy.upserters import KeyPairResourcePolicyUpserter
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRow, joined


@dataclass(frozen=True)
class TestSeedKeypairPolicy(TestSeedRow[KeyPairResourcePolicyData]):
    """What a keypair is allowed. The session limits a scenario varies live here.

    The row also carries an ``is_default`` flag, which decides the policy a keypair
    gets when nothing names one. Creation here leaves it false; a scenario that needs
    a default policy lays :class:`TestSeedDefaultKeypairPolicy`.
    """

    name_hint: str = "keypair-policy"
    max_concurrent_sessions: int = 5
    max_pending_session_count: int | None = None
    vfolder_hosts: Sequence[str] = field(default_factory=tuple)

    @override
    def kind(self) -> str:
        return Says("키페어 정책", english="Keypair policy")

    @override
    def detail(self) -> str:
        allows = [
            Says(
                f"동시 세션 {self.max_concurrent_sessions}개까지",
                english=f"up to {self.max_concurrent_sessions} concurrent sessions",
            )
        ]
        if self.max_pending_session_count is not None:
            allows.append(
                Says(
                    f"그중 대기 {self.max_pending_session_count}개까지",
                    english=f"up to {self.max_pending_session_count} of them pending",
                )
            )
        if self.vfolder_hosts:
            hosts = ", ".join(self.vfolder_hosts)
            allows.append(
                Says(
                    f"vfolder 는 {hosts}에 놓을 수 있습니다",
                    english=f"folders can be placed on {hosts}",
                )
            )
        return joined(allows)

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> KeyPairResourcePolicyCreator:
        return KeyPairResourcePolicyCreator(
            name=name,
            allowed_vfolder_hosts=VFolderHostPermissionMap({
                host: set(VFolderHostPermission) for host in self.vfolder_hosts
            }),
            default_for_unspecified=DefaultForUnspecified.UNLIMITED,
            idle_timeout=3600,
            max_concurrent_sessions=self.max_concurrent_sessions,
            max_containers_per_session=1,
            max_pending_session_count=self.max_pending_session_count,
            max_pending_session_resource_slots=None,
            max_priority=None,
            max_concurrent_sftp_sessions=1,
            max_session_lifetime=0,
            total_resource_slots=ResourceSlot(),
        )


@dataclass(frozen=True)
class TestSeedDefaultKeypairPolicy(TestSeedRow[KeyPairResourcePolicyData]):
    """The policy a keypair gets when nothing names one.

    The upsert spec is the only one that carries ``is_default``, so it is the only way
    to lay a default policy.
    """

    name_hint: str = "default-keypair-policy"

    @override
    def kind(self) -> str:
        return Says("기본 키페어 정책", english="Default keypair policy")

    @override
    def detail(self) -> str:
        return Says(
            "키페어가 정책을 대지 않으면 이 정책을 받습니다",
            english="a keypair that names no policy gets this one",
        )

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> KeyPairResourcePolicyUpserter:
        return KeyPairResourcePolicyUpserter(
            uuid=KeyPairResourcePolicyUUID(uuid4()),
            name=name,
            is_default=True,
            allowed_vfolder_hosts={},
            default_for_unspecified=DefaultForUnspecified.UNLIMITED,
            idle_timeout=3600,
            max_concurrent_sessions=5,
            max_containers_per_session=1,
            max_pending_session_count=None,
            max_pending_session_resource_slots=None,
            max_priority=None,
            max_concurrent_sftp_sessions=1,
            max_session_lifetime=0,
            total_resource_slots=ResourceSlot(),
        )
