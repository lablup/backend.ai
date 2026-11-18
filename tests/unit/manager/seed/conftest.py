from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable
from pathlib import Path
from typing import Any, Final

import pytest
import sqlalchemy as sa
import yaml
from sqlalchemy import Table

from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.base import ensure_all_tables_registered
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow, IdleCheckerRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.notification.row import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.resource_group.row import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
)
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow, ResourceSlotTypeRow
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.session_template.row import SessionTemplateRow
from ai.backend.manager.models.storage_backend.row import StorageBackendTypeRow
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.seed.provider import SeedOpsProvider
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlanner
from ai.backend.manager.seed.types import SeedKind
from ai.backend.testutils.db import HasTable, with_tables

# Columns an upsert rewrites without changing what the row states.
_TIMESTAMPS: Final[frozenset[str]] = frozenset({"created_at", "updated_at"})
_APP_CONFIG_DEFINITIONS: list[str] = ["webui", "session_launcher"]
_APP_CONFIG_ALLOW_LISTS: list[dict[str, Any]] = [
    {"config_name": "webui", "scope_type": "public"},
    {"config_name": "webui", "scope_type": "user", "rank": 350},
    {"config_name": "session_launcher", "scope_type": "domain"},
]
_RESOURCE_SLOT_TYPES: list[dict[str, Any]] = [
    {
        "uuid": "eff6619c-a85c-40f4-ae59-608b0f683b4f",
        "slot_name": "cpu",
        "slot_type": "count",
        "required": True,
        "display_name": "CPU",
        "display_unit": "Core",
        "rank": 100,
    },
    {
        "uuid": "9d1a589e-2a78-491e-97d0-32d2a0079564",
        "slot_name": "mem",
        "slot_type": "bytes",
        "required": True,
        "display_name": "RAM",
        "number_format": {"binary": True, "round_length": 0},
        "rank": 200,
    },
]
_IDLE_CHECKERS: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000f001",
        "name": "session-lifetime",
        "description": "Terminates sessions running longer than a day.",
        "target_session_types": ["interactive", "batch"],
        "spec": {"type": "session_lifetime", "session_lifetime": {"max_lifetime_seconds": 86400}},
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000f002",
        "name": "network-timeout",
        "target_session_types": ["interactive"],
        "initial_grace_period_seconds": 300,
        "spec": {
            "type": "network_timeout",
            "network": {"max_network_inactivity_seconds": 3600},
        },
    },
]

# Domain seed files written for the tests, one domain per file.
_DOMAINS: dict[str, dict[str, Any]] = {
    "default.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000d001",
        "name": "default",
        "description": "The default domain",
        "is_default": True,
        "total_resource_slots": {"cpu": "8", "mem": "17179869184"},
        "allowed_vfolder_hosts": {"local:volume1": ["create-vfolder", "mount-in-session"]},
        "allowed_docker_registries": ["cr.backend.ai"],
    },
    "research.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000d002",
        "name": "research",
    },
}

# Resource group seed file written for the tests. `default` states every field; `gpu`
# leaves the optional ones to their defaults.
_RESOURCE_GROUPS: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000e001",
        "name": "default",
        "description": "The default resource group",
        "is_default": True,
        "wsproxy_addr": "http://127.0.0.1:5050",
        "wsproxy_api_token": "token",
        "driver": "static",
        "driver_opts": {"x": 1},
        "scheduler": "fifo",
        "scheduler_opts": {"pending_timeout": 30},
        "use_host_network": True,
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000e002",
        "name": "gpu",
        "driver": "static",
        "scheduler": "fifo",
    },
]

# Resource policy files written for the tests, one kind per file.
_RESOURCE_POLICIES: dict[str, dict[str, Any]] = {
    "user_resource_policy": {
        "uuid": "0198a5a0-0000-7000-8000-00000000b001",
        "name": "default",
        "max_vfolder_count": 0,
        "max_quota_scope_size": -1,
        "max_session_count_per_model_session": 10,
    },
    "project_resource_policy": {
        "uuid": "0198a5a0-0000-7000-8000-00000000b002",
        "name": "default",
        "max_vfolder_count": 0,
        "max_quota_scope_size": -1,
        "max_network_count": 3,
    },
    "keypair_resource_policy": {
        "uuid": "0198a5a0-0000-7000-8000-00000000b003",
        "name": "default",
        "is_default": True,
        "total_resource_slots": {"cpu": "4", "mem": "8589934592"},
        "max_concurrent_sessions": 5,
        "max_containers_per_session": 1,
        "idle_timeout": 3600,
        "max_pending_session_resource_slots": {"cpu": "2"},
        "allowed_vfolder_hosts": {"local:volume1": ["mount-in-session", "create-vfolder"]},
    },
}


# Project seed files written for the tests, one project per file, in the `default` domain
# under the `default` project resource policy.
_PROJECTS: dict[str, dict[str, Any]] = {
    "research.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000e001",
        "domain_id": "0198a5a0-0000-7000-8000-00000000d001",
        "name": "research",
        "resource_policy_id": "0198a5a0-0000-7000-8000-00000000b002",
        "description": "Research project",
        "total_resource_slots": {"cpu": "4"},
        "allowed_vfolder_hosts": {"local:volume1": ["create-vfolder", "mount-in-session"]},
    },
    "model-store.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000e002",
        "domain_id": "0198a5a0-0000-7000-8000-00000000d001",
        "name": "model-store",
        "type": "model-store",
        "resource_policy_id": "0198a5a0-0000-7000-8000-00000000b002",
        "description": "Model Store",
    },
}

# User seed files written for the tests, one user per file, in the `default` domain under
# the `default` resource policies. `admin` states every field but `allowed_client_ip`, and two keypairs; `member`
# leaves the optional ones to their defaults.
_USERS: dict[str, dict[str, Any]] = {
    "admin.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000f001",
        "domain_id": "0198a5a0-0000-7000-8000-00000000d001",
        "email": "admin@example.com",
        "username": "admin",
        "password": "admin-password",
        "need_password_change": True,
        "full_name": "Admin",
        "description": "The administrator",
        "status": "active",
        "status_info": "seeded",
        "role": "superadmin",
        "resource_policy_id": "0198a5a0-0000-7000-8000-00000000b001",
        "sudo_session_enabled": True,
        "container_uid": 1000,
        "container_main_gid": 1000,
        "container_gids": [1000, 1001],
        "keypairs": [
            {
                "access_key": "AKIAADMINDEFAULT0001",
                "secret_key": "admin-default-secret",
                "is_admin": True,
                "is_default": True,
                "resource_policy_id": "0198a5a0-0000-7000-8000-00000000b003",
                "rate_limit": 30000,
            },
            {
                "access_key": "AKIAADMINSECOND00002",
                "secret_key": "admin-second-secret",
                "is_active": False,
                "resource_policy_id": "0198a5a0-0000-7000-8000-00000000b003",
            },
        ],
    },
    "member.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000f002",
        "domain_id": "0198a5a0-0000-7000-8000-00000000d001",
        "email": "member@example.com",
        "username": "member",
        "password": "member-password",
        "resource_policy_id": "0198a5a0-0000-7000-8000-00000000b001",
    },
}


# Role seed files written for the tests, one role per file. The project role states its
# permissions, grants `member` and is auto-assigned; the domain role grants `admin`.
_SCOPED_ROLES: dict[str, dict[str, Any]] = {
    "research-member.yaml": {
        "id": "0198a5a0-0000-7000-8000-000000001301",
        "name": "research_member",
        "description": "Members of the research project",
        "scope_type": "project",
        "scope_id": _PROJECTS["research.yaml"]["id"],
        "auto_assign": True,
        "permissions": {"session": ["read", "create"], "vfolder": ["read"]},
        "users": [_USERS["member.yaml"]["id"]],
    },
    "default-auditor.yaml": {
        "id": "0198a5a0-0000-7000-8000-000000001302",
        "name": "default_auditor",
        "scope_type": "domain",
        "scope_id": _DOMAINS["default.yaml"]["id"],
        "permissions": {"domain": ["read"]},
        "users": [_USERS["admin.yaml"]["id"]],
    },
}


# The tables a seed kind writes, and the graph tables the creation path writes beside them.
_SEED_TABLES: list[Table | type[HasTable]] = [
    AppConfigDefinitionRow,
    AppConfigAllowListRow,
    AppConfigFragmentRow,
    SystemSessionEnvironRow,
    ResourceSlotTypeRow,
    LoginClientTypeRow,
    RetentionPolicyRow,
    ClientIPMaskingPolicyRow,
    StorageBackendTypeRow,
    PrometheusQueryPresetCategoryRow,
    PrometheusQueryPresetRow,
    NotificationChannelRow,
    NotificationRuleRow,
    IdleCheckerRow,
    IdleCheckerBindingRow,
    ContainerRegistryRow,
    ObjectStorageRow,
    StorageNamespaceRow,
    DomainRow,
    RuntimeVariantRow,
    RuntimeVariantPresetRow,
    ResourcePresetRow,
    DeploymentRevisionPresetRow,
    PresetResourceSlotRow,
    RolePresetRow,
    RolePermissionPresetRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    AssociationContainerRegistriesGroupsRow,
    SessionTemplateRow,
    ResourceGroupRow,
    ResourceGroupForDomainRow,
    ResourceGroupForProjectRow,
    ResourceGroupForKeypairsRow,
    RoleRow,
    UserRoleRow,
    VFSStorageRow,
    PermissionRow,
    VirtualEntityRow,
    ScopeBindingRow,
    EntityLabelRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
]


@pytest.fixture
def registered_models() -> None:
    """The write ops reach rows whose relationships name the whole model tree."""
    ensure_all_tables_registered()


@pytest.fixture
async def db(
    registered_models: None,
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine]:
    async with with_tables(global_entity_ids, _SEED_TABLES):
        yield global_entity_ids


@pytest.fixture
def repository(db: ExtendedAsyncSAEngine) -> SeedRepository:
    return SeedRepository(SeedOpsProvider(db))


@pytest.fixture
def seed_tables() -> list[Table]:
    return [table if isinstance(table, Table) else table.__table__ for table in _SEED_TABLES]


@pytest.fixture
def assert_idempotent(
    db: ExtendedAsyncSAEngine, repository: SeedRepository, seed_tables: list[Table]
) -> Callable[[SeedKind, Path], Awaitable[None]]:
    """Applies the seed directory again and checks that the rows stay the same."""

    async def snapshot() -> dict[str, list[tuple[str, ...]]]:
        rows_by_table: dict[str, list[tuple[str, ...]]] = {}
        async with db.begin_readonly() as conn:
            for table in seed_tables:
                columns = [column for column in table.columns if column.name not in _TIMESTAMPS]
                rows = await conn.execute(sa.select(*columns))
                rows_by_table[table.name] = sorted(tuple(map(str, row)) for row in rows)
        return rows_by_table

    async def check(kind_name: SeedKind, seeds: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([seeds])
        assert plan.rejections == []
        applier = SeedApplier(repository)

        first = await applier.apply(plan, overwrite=False)
        assert first[kind_name].skipped == []
        assert first[kind_name].failed == []
        written = await snapshot()

        again = await applier.apply(plan, overwrite=False)
        assert again[kind_name].succeeded == []
        assert await snapshot() == written

        for _ in range(2):
            await applier.apply(plan, overwrite=True)
            assert await snapshot() == written

    return check


@pytest.fixture
def app_config_definition_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `app_config_definition` seed file."""
    directory = tmp_path / "app_config_definition"
    directory.mkdir()
    items = [{"config_name": name} for name in _APP_CONFIG_DEFINITIONS]
    (directory / "definitions.yaml").write_text(
        yaml.safe_dump({"kind": "app_config_definition", "version": 1, "items": items})
    )
    return directory


@pytest.fixture
def app_config_allow_list_seed_dir(app_config_definition_seed_dir: Path) -> Path:
    """The `app_config_definition` directory plus one `app_config_allow_list` seed file,
    so the entries' config names are registered first."""
    (app_config_definition_seed_dir / "allow-list.yaml").write_text(
        yaml.safe_dump({
            "kind": "app_config_allow_list",
            "version": 1,
            "items": _APP_CONFIG_ALLOW_LISTS,
        })
    )
    return app_config_definition_seed_dir


@pytest.fixture
def resource_slot_type_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `resource_slot_type` seed file."""
    directory = tmp_path / "resource_slot_type"
    directory.mkdir()
    (directory / "slots.yaml").write_text(
        yaml.safe_dump({"kind": "resource_slot_type", "version": 1, "items": _RESOURCE_SLOT_TYPES})
    )
    return directory


@pytest.fixture
def idle_checker_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `idle_checker` seed file."""
    directory = tmp_path / "idle_checker"
    directory.mkdir()
    (directory / "checkers.yaml").write_text(
        yaml.safe_dump({"kind": "idle_checker", "version": 1, "items": _IDLE_CHECKERS})
    )
    return directory


@pytest.fixture
def domain_seed_dir(tmp_path: Path) -> Path:
    """A directory of domain seed files, the shape `seeds/manager/domain/` has."""
    directory = tmp_path / "domain"
    directory.mkdir()
    for file_name, domain in _DOMAINS.items():
        (directory / file_name).write_text(
            yaml.safe_dump({"kind": "domain", "version": 1, "items": [domain]})
        )
    return directory


@pytest.fixture
def research_domain_id() -> str:
    return str(_DOMAINS["research.yaml"]["id"])


@pytest.fixture
def project_seed_dir(tmp_path: Path) -> Path:
    """A directory of project seed files with the domain and the project resource policy
    files they refer to."""
    directory = tmp_path / "project"
    directory.mkdir()
    for file_name, domain in _DOMAINS.items():
        (directory / f"domain-{file_name}").write_text(
            yaml.safe_dump({"kind": "domain", "version": 1, "items": [domain]})
        )
    for kind in ("user_resource_policy", "project_resource_policy"):
        (directory / f"{kind}.yaml").write_text(
            yaml.safe_dump({"kind": kind, "version": 1, "items": [_RESOURCE_POLICIES[kind]]})
        )
    for file_name, project in _PROJECTS.items():
        (directory / file_name).write_text(
            yaml.safe_dump({"kind": "project", "version": 1, "items": [project]})
        )
    return directory


@pytest.fixture
def research_project_id() -> str:
    return str(_PROJECTS["research.yaml"]["id"])


@pytest.fixture
def admin_user_id() -> str:
    return str(_USERS["admin.yaml"]["id"])


@pytest.fixture
def role_kind_seed_dir(project_seed_dir: Path) -> Path:
    """The project directory plus the users and the role files, so the scopes and the
    users the roles name are written first."""
    (project_seed_dir / "keypair_resource_policy.yaml").write_text(
        yaml.safe_dump({
            "kind": "keypair_resource_policy",
            "version": 1,
            "items": [_RESOURCE_POLICIES["keypair_resource_policy"]],
        })
    )
    for file_name, user in _USERS.items():
        (project_seed_dir / f"user-{file_name}").write_text(
            yaml.safe_dump({"kind": "user", "version": 1, "items": [user]})
        )
    for file_name, role in _SCOPED_ROLES.items():
        (project_seed_dir / f"role-{file_name}").write_text(
            yaml.safe_dump({"kind": "role", "version": 1, "items": [role]})
        )
    return project_seed_dir


@pytest.fixture
def resource_group_allow_seed_dir(project_seed_dir: Path) -> Path:
    """The project directory plus the users, the resource groups and one file per resource
    group allow kind, linking each to the `default` resource group."""
    (project_seed_dir / "keypair_resource_policy.yaml").write_text(
        yaml.safe_dump({
            "kind": "keypair_resource_policy",
            "version": 1,
            "items": [_RESOURCE_POLICIES["keypair_resource_policy"]],
        })
    )
    for file_name, user in _USERS.items():
        (project_seed_dir / f"user-{file_name}").write_text(
            yaml.safe_dump({"kind": "user", "version": 1, "items": [user]})
        )
    (project_seed_dir / "resource-groups.yaml").write_text(
        yaml.safe_dump({"kind": "resource_group", "version": 1, "items": _RESOURCE_GROUPS})
    )
    resource_group_id = _RESOURCE_GROUPS[0]["id"]
    admin = _USERS["admin.yaml"]
    allows: dict[str, list[dict[str, Any]]] = {
        "resource_group_for_domain": [
            {"domain_id": domain["id"], "resource_group_id": resource_group_id}
            for domain in _DOMAINS.values()
        ],
        "resource_group_for_project": [
            {"project_id": _PROJECTS["research.yaml"]["id"], "resource_group_id": resource_group_id}
        ],
        "resource_group_for_keypair": [
            {
                "access_key": keypair["access_key"],
                "user_id": admin["id"],
                "resource_group_id": resource_group_id,
            }
            for keypair in admin["keypairs"]
        ],
    }
    for kind, items in allows.items():
        (project_seed_dir / f"{kind}.yaml").write_text(
            yaml.safe_dump({"kind": kind, "version": 1, "items": items})
        )
    return project_seed_dir


@pytest.fixture
def research_member_role_id() -> str:
    return str(_SCOPED_ROLES["research-member.yaml"]["id"])
