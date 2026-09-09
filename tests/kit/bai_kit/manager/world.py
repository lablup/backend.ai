"""The rows every scenario starts from, seeded through src creators.

One default domain, the three "default" resource policies, one resource group, the
role presets an install ships, and four persona users with their default keypairs and
personal projects. Nothing here builds a row by hand: every insert goes through a
Creator spec and the ops layer, so what ``create_user`` would have made is what the
World holds.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import (
    AccessKey,
    DefaultForUnspecified,
    ResourceSlot,
    VFolderHostPermission,
    VFolderHostPermissionMap,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.keypair.types import KeyPairSecrets
from ai.backend.manager.models.base import populate_fixture
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.resource_group.creators import ResourceGroupCreator
from ai.backend.manager.models.resource_policy.creators import (
    KeyPairResourcePolicyCreator,
    ProjectResourcePolicyCreator,
    UserResourcePolicyCreator,
)
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.user.provider import UserOpsProvider
from ai.backend.manager.repositories.ops.v2.user.write import FullUserCreator
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.scenario import Persona

VFOLDER_HOST = "local:volume1"
DEFAULT_POLICY = "default"


@dataclass(frozen=True)
class PersonaSpec:
    username: str
    role: UserRole
    access_key: str
    secret_key: str

    @property
    def email(self) -> str:
        return f"{self.username}@kit.local"


@dataclass(frozen=True)
class WorldSpec:
    """Fixed names and keys, so a scenario can name them as literals."""

    domain_name: str = "default"
    resource_group_name: str = "default"
    vfolder_host: str = VFOLDER_HOST
    personas: Mapping[Persona, PersonaSpec] = field(
        default_factory=lambda: {
            Persona("superadmin"): PersonaSpec(
                "superadmin", UserRole.SUPERADMIN, "AKKITSUPERADMIN00001", "sk-kit-superadmin"
            ),
            Persona("domain-admin"): PersonaSpec(
                "domain-admin", UserRole.ADMIN, "AKKITDOMAINADMIN0001", "sk-kit-domain-admin"
            ),
            Persona("member"): PersonaSpec(
                "member", UserRole.USER, "AKKITMEMBER000000001", "sk-kit-member"
            ),
            Persona("other-member"): PersonaSpec(
                "other-member", UserRole.USER, "AKKITOTHERMEMBER0001", "sk-kit-other-member"
            ),
        }
    )


WORLD = WorldSpec()


@dataclass(frozen=True)
class SeededUser:
    id: UserID
    username: str
    email: str
    role: UserRole
    domain_name: str
    domain_id: DomainID
    access_key: str
    secret_key: str


@dataclass(frozen=True)
class World:
    domain_id: DomainID
    domain_name: str
    resource_group_name: str
    vfolder_host: str
    users: Mapping[Persona, SeededUser]


def _all_host_permissions() -> VFolderHostPermissionMap:
    return VFolderHostPermissionMap({VFOLDER_HOST: set(VFolderHostPermission)})


async def _seed_role_presets(engine: ExtendedAsyncSAEngine) -> None:
    """The presets an install loads from ``fixtures/manager/example-roles.json``."""
    fixture_path = (
        Path(os.environ["BACKEND_BUILD_ROOT"]) / "fixtures" / "manager" / "example-roles.json"
    )
    data = json.loads(fixture_path.read_text())
    await populate_fixture(
        engine,
        {
            "role_presets": data["role_presets"],
            "role_permission_presets": data["role_permission_presets"],
        },
    )


async def build_world(engine: ExtendedAsyncSAEngine, spec: WorldSpec = WORLD) -> World:
    await _seed_role_presets(engine)
    provider = V2DBOpsProvider(engine)
    ops: OpsRepository[Any] = OpsRepository(provider)

    await ops.create_global_entity(
        UserResourcePolicyCreator(
            name=DEFAULT_POLICY,
            max_vfolder_count=0,
            max_quota_scope_size=-1,
            max_session_count_per_model_session=10,
            max_customized_image_count=3,
        )
    )
    await ops.create_global_entity(
        ProjectResourcePolicyCreator(
            name=DEFAULT_POLICY, max_vfolder_count=0, max_quota_scope_size=-1, max_network_count=3
        )
    )
    await ops.create_global_entity(
        KeyPairResourcePolicyCreator(
            name=DEFAULT_POLICY,
            allowed_vfolder_hosts=_all_host_permissions(),
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
    )
    resource_group = await ops.create_role_managed_global_entity(
        ResourceGroupCreator(name=spec.resource_group_name, driver="static", scheduler="fifo")
    )
    domain = await DomainRepository(engine, provider).create_domain_node(
        DomainCreator(
            name=spec.domain_name,
            description="The default domain",
            allowed_vfolder_hosts={VFOLDER_HOST: [p.value for p in VFolderHostPermission]},
        ),
        [resource_group.id],
    )

    users: dict[Persona, SeededUser] = {}
    for persona, p in spec.personas.items():
        async with UserOpsProvider(engine).write_ops() as w:
            created = await w.create_user(
                FullUserCreator(
                    user=UserCreator(
                        email=p.email,
                        username=p.username,
                        password=PasswordInfo(
                            password="kit-password",
                            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                            rounds=1000,
                            salt_size=16,
                        ),
                        need_password_change=False,
                        domain_id=domain.id,
                        role=p.role,
                        is_active=True,
                        resource_policy=DEFAULT_POLICY,
                    ),
                    keypair_secrets=KeyPairSecrets(
                        access_key=AccessKey(p.access_key),
                        secret_key=SecretValue(p.secret_key),
                        ssh_public_key="",
                        ssh_private_key="",
                    ),
                    keypair_resource_policy=DEFAULT_POLICY,
                )
            )
        users[persona] = SeededUser(
            id=UserID(created.user.id),
            username=p.username,
            email=p.email,
            role=p.role,
            domain_name=spec.domain_name,
            domain_id=domain.id,
            access_key=p.access_key,
            secret_key=p.secret_key,
        )

    return World(
        domain_id=domain.id,
        domain_name=spec.domain_name,
        resource_group_name=spec.resource_group_name,
        vfolder_host=spec.vfolder_host,
        users=users,
    )
