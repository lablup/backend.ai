"""Write specs for the resource policy a keypair is held to."""

from __future__ import annotations

from collections.abc import Sequence

from bai_scenario.seeds.seeder import Spec

from ai.backend.common.types import (
    DefaultForUnspecified,
    ResourceSlot,
    VFolderHostPermission,
    VFolderHostPermissionMap,
)
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.creators import KeyPairResourcePolicyCreator


def seed_keypair_policy(
    *,
    name_hint: str = "keypair-policy",
    max_concurrent_sessions: int = 5,
    max_pending_session_count: int | None = None,
    vfolder_hosts: Sequence[str] = (),
) -> Spec[KeyPairResourcePolicyData]:
    """What a keypair is allowed. The session limits a scenario varies live here."""

    def build(name: str) -> KeyPairResourcePolicyCreator:
        return KeyPairResourcePolicyCreator(
            name=name,
            allowed_vfolder_hosts=VFolderHostPermissionMap({
                host: set(VFolderHostPermission) for host in vfolder_hosts
            }),
            default_for_unspecified=DefaultForUnspecified.UNLIMITED,
            idle_timeout=3600,
            max_concurrent_sessions=max_concurrent_sessions,
            max_containers_per_session=1,
            max_pending_session_count=max_pending_session_count,
            max_pending_session_resource_slots=None,
            max_priority=None,
            max_concurrent_sftp_sessions=1,
            max_session_lifetime=0,
            total_resource_slots=ResourceSlot(),
        )

    return Spec("a keypair policy", name_hint, build)
