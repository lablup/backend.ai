"""Write specs for the resource policy a keypair is held to."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedRow

from ai.backend.common.types import (
    DefaultForUnspecified,
    ResourceSlot,
    VFolderHostPermission,
    VFolderHostPermissionMap,
)
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.creators import KeyPairResourcePolicyCreator


@dataclass(frozen=True)
class SeedKeypairPolicy(SeedRow[KeyPairResourcePolicyData]):
    """What a keypair is allowed. The session limits a scenario varies live here.

    The row also carries an ``is_default`` flag, which decides the policy a keypair
    gets when nothing names one, but no write spec sets it. A scenario that needs a
    default keypair policy cannot lay one yet.
    """

    name_hint: str = "keypair-policy"
    max_concurrent_sessions: int = 5
    max_pending_session_count: int | None = None
    vfolder_hosts: Sequence[str] = field(default_factory=tuple)
    host_permissions: Sequence[VFolderHostPermission] = tuple(VFolderHostPermission)
    """What the keypair may do on those hosts. Everything, until a row narrows it."""

    @override
    def kind(self) -> str:
        return "키페어 정책"

    @override
    def detail(self) -> str:
        allows = [f"동시 세션 {self.max_concurrent_sessions}개까지"]
        if self.max_pending_session_count is not None:
            allows.append(f"그중 대기 {self.max_pending_session_count}개까지")
        if self.vfolder_hosts:
            allows.append(f"폴더는 {', '.join(self.vfolder_hosts)}에 놓을 수 있다")
        if set(self.host_permissions) != set(VFolderHostPermission):
            named = ", ".join(sorted(one.value for one in self.host_permissions))
            allows.append(f"그 호스트에서 할 수 있는 것은 {named}뿐이다")
        return ", ".join(allows)

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> KeyPairResourcePolicyCreator:
        allowed = VFolderHostPermissionMap()
        for host in self.vfolder_hosts:
            allowed[host] = set(self.host_permissions)
        return KeyPairResourcePolicyCreator(
            name=name,
            allowed_vfolder_hosts=allowed,
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
