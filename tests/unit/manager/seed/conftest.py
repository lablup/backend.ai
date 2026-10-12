from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest
import yaml
from sqlalchemy import Table

from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.base import ensure_all_tables_registered
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.notification.row import NotificationChannelRow
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.storage_backend.row import StorageBackendTypeRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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
from ai.backend.manager.seed.role_preset.kinds import PermissionKinds
from ai.backend.testutils.db import HasTable, with_tables

_ALL: list[str] = ["read", "update", "create", "soft_delete", "hard_delete"]
# Role files written for the tests, one role per file. The admin states `agent: [read]` and
# leaves `app_config` empty; every role states every entity type, as a role file must.
_ROLES: dict[str, dict[str, Any]] = {
    "domain-admin.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000a001",
        "name": "domain_admin",
        "scope_type": "domain",
        "auto_assign": False,
        "permissions": {"agent": ["read"], "domain": ["read", "update"], "project": _ALL},
    },
    "domain-member.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000a002",
        "name": "domain_member",
        "scope_type": "domain",
        "auto_assign": True,
        "permissions": {"domain": ["read"], "project": ["read"]},
    },
    "public-member.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000a003",
        "name": "public_member",
        "scope_type": "global",
        "scope": "public",
        "auto_assign": True,
        "permissions": {"image": ["read"]},
    },
}
_APP_CONFIG_DEFINITIONS: list[str] = ["webui", "session_launcher"]
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
_LOGIN_CLIENT_TYPES: list[dict[str, Any]] = [
    {"id": "0198a5a0-0000-7000-8000-00000000c001", "name": "webui", "description": "Web UI"},
    {"id": "0198a5a0-0000-7000-8000-00000000c002", "name": "cli"},
]
_RETENTION_POLICIES: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000d001",
        "category": "logs",
        "retention_period_days": 365,
        "enabled": False,
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000d002",
        "category": "usage_records",
        "retention_period_days": 90,
        "enabled": True,
    },
]
_CLIENT_IP_MASKING_POLICIES: list[dict[str, Any]] = [
    {"target_type": "default", "mode": "truncate", "ipv4_prefix": 24, "ipv6_prefix": 48},
    {"target_type": "audit_logs", "mode": "drop"},
]
_STORAGE_BACKEND_TYPES: dict[str, list[str]] = {
    "vfs": ["vfolder", "metric", "fast-fs-size"],
    "noop": [],
}
_PROMETHEUS_QUERY_PRESET_CATEGORIES: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000e001",
        "name": "container",
        "description": "Container-level utilization metrics",
    },
    {"id": "0198a5a0-0000-7000-8000-00000000e002", "name": "vllm-inference"},
]
_NOTIFICATION_CHANNELS: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000c001",
        "name": "ops-webhook",
        "channel_type": "webhook",
        "spec": {"url": "https://hooks.example.com/ops"},
        "created_by": "f38dea23-50fa-42a0-b5ae-338f5f4693f4",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000c002",
        "name": "ops-email",
        "description": "Mail to the operators",
        "channel_type": "email",
        "spec": {
            "smtp": {"host": "smtp.example.com", "port": 587},
            "message": {"from_email": "noreply@example.com", "to_emails": ["ops@example.com"]},
        },
        "enabled": False,
        "created_by": "f38dea23-50fa-42a0-b5ae-338f5f4693f4",
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

# The tables a seed kind writes, and the graph tables the creation path writes beside them.
_SEED_TABLES: list[Table | type[HasTable]] = [
    AppConfigDefinitionRow,
    ResourceSlotTypeRow,
    LoginClientTypeRow,
    RetentionPolicyRow,
    ClientIPMaskingPolicyRow,
    StorageBackendTypeRow,
    PrometheusQueryPresetCategoryRow,
    NotificationChannelRow,
    IdleCheckerRow,
    RolePresetRow,
    RolePermissionPresetRow,
    RoleRow,
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
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(global_entity_ids, _SEED_TABLES):
        yield global_entity_ids


@pytest.fixture
def repository(db: ExtendedAsyncSAEngine) -> SeedRepository:
    return SeedRepository(SeedOpsProvider(db))


@pytest.fixture
def seed_tables() -> list[Table]:
    return [table if isinstance(table, Table) else table.__table__ for table in _SEED_TABLES]


@pytest.fixture
def role_seed_dir(tmp_path: Path) -> Path:
    """A directory of role seed files, the shape `seeds/manager/role_preset/` has."""
    directory = tmp_path / "role_preset"
    directory.mkdir()
    declared = PermissionKinds().declared()
    for file_name, role in _ROLES.items():
        permissions = {kind: [] for kind in declared} | role["permissions"]
        item = role | {"permissions": permissions}
        (directory / file_name).write_text(
            yaml.safe_dump({"kind": "role_preset", "version": 1, "items": [item]})
        )
    return directory


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
def resource_slot_type_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `resource_slot_type` seed file."""
    directory = tmp_path / "resource_slot_type"
    directory.mkdir()
    (directory / "slots.yaml").write_text(
        yaml.safe_dump({"kind": "resource_slot_type", "version": 1, "items": _RESOURCE_SLOT_TYPES})
    )
    return directory


@pytest.fixture
def login_client_type_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `login_client_type` seed file."""
    directory = tmp_path / "login_client_type"
    directory.mkdir()
    (directory / "types.yaml").write_text(
        yaml.safe_dump({"kind": "login_client_type", "version": 1, "items": _LOGIN_CLIENT_TYPES})
    )
    return directory


@pytest.fixture
def retention_policy_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `retention_policy` seed file."""
    directory = tmp_path / "retention_policy"
    directory.mkdir()
    (directory / "policies.yaml").write_text(
        yaml.safe_dump({"kind": "retention_policy", "version": 1, "items": _RETENTION_POLICIES})
    )
    return directory


@pytest.fixture
def client_ip_masking_policy_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `client_ip_masking_policy` seed file."""
    directory = tmp_path / "client_ip_masking_policy"
    directory.mkdir()
    (directory / "policies.yaml").write_text(
        yaml.safe_dump({
            "kind": "client_ip_masking_policy",
            "version": 1,
            "items": _CLIENT_IP_MASKING_POLICIES,
        })
    )
    return directory


@pytest.fixture
def storage_backend_type_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `storage_backend_type` seed file."""
    directory = tmp_path / "storage_backend_type"
    directory.mkdir()
    items = [
        {"name": name, "capabilities": capabilities}
        for name, capabilities in _STORAGE_BACKEND_TYPES.items()
    ]
    (directory / "types.yaml").write_text(
        yaml.safe_dump({"kind": "storage_backend_type", "version": 1, "items": items})
    )
    return directory


@pytest.fixture
def prometheus_query_preset_category_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `prometheus_query_preset_category` seed file."""
    directory = tmp_path / "prometheus_query_preset_category"
    directory.mkdir()
    (directory / "categories.yaml").write_text(
        yaml.safe_dump({
            "kind": "prometheus_query_preset_category",
            "version": 1,
            "items": _PROMETHEUS_QUERY_PRESET_CATEGORIES,
        })
    )
    return directory


@pytest.fixture
def notification_channel_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `notification_channel` seed file."""
    directory = tmp_path / "notification_channel"
    directory.mkdir()
    (directory / "channels.yaml").write_text(
        yaml.safe_dump({
            "kind": "notification_channel",
            "version": 1,
            "items": _NOTIFICATION_CHANNELS,
        })
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
def idle_checker_ids() -> list[str]:
    return [str(checker["id"]) for checker in _IDLE_CHECKERS]


@pytest.fixture
def domain_admin_id() -> str:
    return str(_ROLES["domain-admin.yaml"]["id"])
