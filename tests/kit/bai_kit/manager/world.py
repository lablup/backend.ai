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

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role import RoleID
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
from ai.backend.manager.data.permission.role import UserRoleAssignmentInput
from ai.backend.manager.models.base import populate_fixture
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.project.creators import ProjectCreator
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
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
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
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
    project_name: str = "shared"
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
    project_id: ProjectID
    project_name: str
    users: Mapping[Persona, SeededUser]


def _all_host_permissions() -> VFolderHostPermissionMap:
    return VFolderHostPermissionMap({VFOLDER_HOST: set(VFolderHostPermission)})


async def _seed_role_presets(engine: ExtendedAsyncSAEngine) -> None:
    """The presets an install loads from ``fixtures/manager/example-roles.json``.

    The shipped rows all carry ``deleted = true``, which makes the preset machinery
    inert: a domain, project or user created after the install gets no role from it.
    The World marks them active instead, because a persona with no role cannot be told
    apart from a stranger and every "allowed" scenario would be unwritable. Whether the
    shipped rows are meant to be inert is a question for the RBAC owners; see the PoC
    report.
    """
    fixture_path = (
        Path(os.environ["BACKEND_BUILD_ROOT"]) / "fixtures" / "manager" / "example-roles.json"
    )
    data = json.loads(fixture_path.read_text())
    await populate_fixture(
        engine,
        {
            "role_presets": [{**row, "deleted": False} for row in data["role_presets"]],
            "role_permission_presets": data["role_permission_presets"],
        },
    )


async def _role_of_preset(engine: ExtendedAsyncSAEngine, preset_name: str, scope_id: str) -> RoleID:
    """The role a preset created in one scope.

    A preset role is discoverable by the permissions it was created with: they name the
    scope, and the role names the preset it came from.
    """
    async with engine.begin_readonly_session() as sess:
        role_id = await sess.scalar(
            sa.select(RoleRow.id)
            .join(RolePresetRow, RolePresetRow.id == RoleRow.role_preset_id)
            .join(PermissionRow, PermissionRow.role_id == RoleRow.id)
            .where(RolePresetRow.name == preset_name, PermissionRow.scope_id == scope_id)
            .limit(1)
        )
    if role_id is None:
        raise LookupError(f"no role from preset {preset_name!r} in scope {scope_id}")
    return RoleID(role_id)


async def _grant(
    engine: ExtendedAsyncSAEngine, user_id: UserID, preset_name: str, scope_id: str
) -> None:
    """Give the user the role a preset created in that scope, the way an operator would."""
    role_id = await _role_of_preset(engine, preset_name, scope_id)
    await PermissionControllerRepository(engine).assign_role(
        UserRoleAssignmentInput(user_id=user_id, role_id=role_id)
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

    # A project the personas differ on: the member is on its roster, the other member
    # is not. Without one, every "has permission" scenario would be unwritable.
    project = await ops.create_role_managed_entity(
        ProjectCreator(
            name=spec.project_name,
            domain_id=domain.id,
            domain_name=spec.domain_name,
            description="The project the personas differ on",
            resource_policy=DEFAULT_POLICY,
        )
    )
    project_id = ProjectID(project.id)
    member_id = users[Persona("member")].id
    async with UserOpsProvider(engine).write_ops() as w:
        await w.join_projects(member_id, domain.id, [project_id])

    # The roles an operator assigns. ``preset_user`` and ``preset_domain_admin`` are not
    # auto-assigned, so without this every persona but the superadmin holds nothing and
    # no scenario could tell "allowed" from "refused".
    await _grant(engine, users[Persona("domain-admin")].id, "preset_domain_admin", str(domain.id))
    for persona in (Persona("member"), Persona("other-member")):
        user_id = users[persona].id
        await _grant(engine, user_id, "preset_user", str(user_id))

    return World(
        domain_id=domain.id,
        domain_name=spec.domain_name,
        resource_group_name=spec.resource_group_name,
        vfolder_host=spec.vfolder_host,
        project_id=project_id,
        project_name=spec.project_name,
        users=users,
    )
