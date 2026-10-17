from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
import yaml
from sqlalchemy import Table

from ai.backend.common.data.entity.user import UserEntityType
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
_APP_CONFIG_ALLOW_LISTS: list[dict[str, Any]] = [
    {"config_name": "webui", "scope_type": "public"},
    {"config_name": "webui", "scope_type": "user", "rank": 350},
    {"config_name": "session_launcher", "scope_type": "domain"},
]
# Fragments at the `public` scope and at the `default` domain of `_DOMAINS`.
_APP_CONFIG_FRAGMENTS: list[dict[str, Any]] = [
    {"config_name": "webui", "scope_type": "public", "config": {"theme": "light"}},
    {
        "config_name": "session_launcher",
        "scope_type": "domain",
        "scope_id": "0198a5a0-0000-7000-8000-00000000d001",
        "config": {"default_image": "python:3.13"},
    },
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
_PROMETHEUS_QUERY_PRESETS: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000f001",
        "name": "container-utilization-sum",
        "metric_name": "backendai_container_utilization",
        "query_template": "sum by (${{group_by}})(backendai_container_utilization{${{labels}}})",
        "options": {"filter_labels": ["kernel_id"], "group_labels": ["kernel_id"]},
        "description": "Instant value of the per-kernel utilization, summed",
        "rank": 100,
        "category_id": "0198a5a0-0000-7000-8000-00000000e001",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000f002",
        "name": "vllm-request-rate",
        "metric_name": "vllm_request_success_total",
        "query_template": "sum(rate(vllm_request_success_total{${{labels}}}[${{window}}]))",
        "time_window": "5m",
        "options": {"filter_labels": [], "group_labels": []},
    },
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
_NOTIFICATION_RULES: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000d001",
        "name": "session-started",
        "rule_type": "session.started",
        "channel_id": "0198a5a0-0000-7000-8000-00000000c001",
        "message_template": "Session {{ session_id }} started",
        "created_by": "f38dea23-50fa-42a0-b5ae-338f5f4693f4",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000d002",
        "name": "artifact-downloaded",
        "description": "Mail when a download completes",
        "rule_type": "artifact.download.completed",
        "channel_id": "0198a5a0-0000-7000-8000-00000000c002",
        "message_template": "Artifact {{ artifact_id }} downloaded",
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
# One global Harbor registry and one registry reachable only from the projects bound to it.
_CONTAINER_REGISTRIES: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000c001",
        "registry_name": "cr.backend.ai",
        "url": "https://cr.backend.ai",
        "type": "harbor2",
        "project": "stable",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000c002",
        "registry_name": "local",
        "url": "http://localhost",
        "type": "local",
        "project": "stable",
        "is_global": False,
        "username": "admin",
        "password": "secret",
        "ssl_verify": False,
        "extra": {"note": "seed"},
    },
]
_OBJECT_STORAGES: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000b001",
        "name": "minio",
        "host": "storage-proxy",
        "access_key": "minioadmin",
        "secret_key": "minioadmin",
        "endpoint": "http://127.0.0.1:9000",
        "region": "us-east-1",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000b002",
        "name": "archive",
        "host": "storage-proxy",
        "access_key": "archive-key",
        "secret_key": "archive-secret",
        "endpoint": "http://127.0.0.1:9001",
    },
]
_STORAGE_NAMESPACES: list[dict[str, str]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000c001",
        "storage_id": "0198a5a0-0000-7000-8000-00000000b001",
        "namespace": "artifacts",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000c002",
        "storage_id": "0198a5a0-0000-7000-8000-00000000b002",
        "namespace": "archive",
    },
]
_VFS_STORAGES: list[dict[str, str]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000b001",
        "name": "local",
        "host": "local",
        "base_path": "/var/lib/backend.ai/vfs",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000b002",
        "name": "shared",
        "host": "nfs",
        "base_path": "/mnt/vfs",
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

# Runtime variant files written for the tests, one variant per file. `vllm` states every
# field; `custom` leaves the optional ones to their defaults.
_RUNTIME_VARIANTS: dict[str, dict[str, Any]] = {
    "vllm.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000b001",
        "name": "vllm",
        "description": "vLLM",
        "reads_vfolder_config_files": True,
        "default_model_definition": {
            "models": [
                {"name": "vllm-model", "service": {"port": 8000}},
            ]
        },
    },
    "custom.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000b002",
        "name": "custom",
    },
}

# Runtime variant preset files written for the tests, one file per variant. `max-model-len`
# states every field; `enforce-eager` leaves the optional ones to their defaults.
_RUNTIME_VARIANT_PRESETS: dict[str, list[dict[str, Any]]] = {
    "vllm.yaml": [
        {
            "id": "0198a5a0-0000-7000-8000-00000000d001",
            "runtime_variant_id": _RUNTIME_VARIANTS["vllm.yaml"]["id"],
            "name": "max-model-len",
            "description": "Maximum context length",
            "rank": 100,
            "preset_target": "args",
            "value_type": "int",
            "default_value": "4096",
            "key": "--max-model-len",
            "required": True,
            "added_version": "0.6",
            "deprecated_version": "1.0.0",
            "category": "model",
            "display_name": "Max model length",
            "ui_option": {"ui_type": "slider", "slider": {"min": 512, "max": 32768, "step": 512}},
        },
        {
            "id": "0198a5a0-0000-7000-8000-00000000d002",
            "runtime_variant_id": _RUNTIME_VARIANTS["vllm.yaml"]["id"],
            "name": "enforce-eager",
            "rank": 200,
            "preset_target": "args",
            "value_type": "flag",
            "key": "--enforce-eager",
        },
    ],
}

# Deployment preset files written for the tests, one preset per file. `vllm-small` states
# every field; `minimal` leaves the optional ones to their defaults.
_DEPLOYMENT_PRESETS: dict[str, dict[str, Any]] = {
    "vllm-small.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000f001",
        "runtime_variant_id": "0198a5a0-0000-7000-8000-00000000b001",
        "name": "vllm-small",
        "description": "vLLM on one GPU",
        "image_id": "0198a5a0-0000-7000-8000-00000000f101",
        "model_definition": {"models": [{"service": {"port": 8000}}]},
        "resource_slots": {"cpu": 2, "mem": 4294967296},
        "resource_opts": [{"name": "shmem", "value": "1g"}],
        "cluster_mode": "single-node",
        "cluster_size": 1,
        "startup_command": "vllm serve",
        "bootstrap_script": "pip install vllm",
        "environ": {"HF_HOME": "/models"},
        "runtime_variant_preset_values": [
            {"preset_id": "0198a5a0-0000-7000-8000-00000000f201", "value": "0.9"}
        ],
        "open_to_public": True,
        "replica_count": 2,
        "revision_history_limit": 5,
        "deployment_strategy": "BLUE_GREEN",
        "deployment_strategy_spec": {"auto_promote": True},
    },
    "minimal.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000f002",
        "runtime_variant_id": "0198a5a0-0000-7000-8000-00000000b001",
        "name": "minimal",
        "image_id": "0198a5a0-0000-7000-8000-00000000f101",
    },
}

# Project seed files written for the tests, one project per file, in the `default` domain
# under the `default` project resource policy.
_PROJECTS: dict[str, dict[str, Any]] = {
    "research.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000e001",
        "domain_id": "0198a5a0-0000-7000-8000-00000000d001",
        "name": "research",
        "resource_policy": "default",
        "description": "Research project",
        "total_resource_slots": {"cpu": "4"},
        "allowed_vfolder_hosts": {"local:volume1": ["create-vfolder", "mount-in-session"]},
    },
    "model-store.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000e002",
        "domain_id": "0198a5a0-0000-7000-8000-00000000d001",
        "name": "model-store",
        "type": "model-store",
        "resource_policy": "default",
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
        "resource_policy": "default",
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
                "resource_policy": "default",
                "rate_limit": 30000,
                "ssh_public_key": "ssh-ed25519 AAAA admin",
                "ssh_private_key": "-----BEGIN OPENSSH PRIVATE KEY-----",
            },
            {
                "access_key": "AKIAADMINSECOND00002",
                "secret_key": "admin-second-secret",
                "is_active": False,
                "resource_policy": "default",
            },
        ],
    },
    "member.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000f002",
        "domain_id": "0198a5a0-0000-7000-8000-00000000d001",
        "email": "member@example.com",
        "username": "member",
        "password": "member-password",
        "resource_policy": "default",
    },
}

# Resource preset files written for the tests, one preset per file, both bound to no
# resource group. `small` states every field; `large` leaves `shared_memory` out.
_RESOURCE_PRESETS: dict[str, dict[str, Any]] = {
    "small.yaml": {
        "id": "0198a5a0-0000-7000-8000-000000001001",
        "name": "small",
        "resource_slots": {"cpu": "1", "mem": "1073741824"},
        "shared_memory": "64m",
    },
    "large.yaml": {
        "id": "0198a5a0-0000-7000-8000-000000001002",
        "name": "large",
        "resource_slots": {"cpu": "8", "mem": "17179869184", "cuda.shares": "1"},
    },
}

# The user the session templates belong to, inserted by `template_owner` so the session
# template tests do not apply the user kind.
_TEMPLATE_OWNER: dict[str, Any] = {
    "uuid": "0198a5a0-0000-7000-8000-000000001201",
    "username": "owner",
    "email": "owner@example.com",
    "domain_id": "0198a5a0-0000-7000-8000-000000001202",
    "domain_name": "templates",
    "resource_policy": "templates",
}

# Session template files written for the tests, one template per file, neither in a
# project. `task` states every field; `cluster` leaves the optional ones to their defaults.
_SESSION_TEMPLATES: dict[str, dict[str, Any]] = {
    "task.yaml": {
        "id": "0198a5a0-0000-7000-8000-000000001211",
        "user_id": _TEMPLATE_OWNER["uuid"],
        "type": "task",
        "name": "python",
        "is_active": True,
        "template": {
            "api_version": "6",
            "kind": "task_template",
            "metadata": {"name": "python"},
            "spec": {"kernel": {"image": "python"}},
        },
    },
    "cluster.yaml": {
        "id": "0198a5a0-0000-7000-8000-000000001212",
        "user_id": _TEMPLATE_OWNER["uuid"],
        "type": "cluster",
        "template": {
            "api_version": "6",
            "kind": "cluster_template",
            "mode": "single-node",
            "metadata": {"name": "python"},
            "spec": {
                "nodes": [
                    {"role": "main", "session_template": "0198a5a0-0000-7000-8000-000000001211"}
                ]
            },
        },
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

# Project member items written for the tests: `admin` on `research`, `member` on
# `model-store`.
_PROJECT_MEMBERS: list[dict[str, str]] = [
    {"project_id": _PROJECTS["research.yaml"]["id"], "user_id": _USERS["admin.yaml"]["id"]},
    {"project_id": _PROJECTS["model-store.yaml"]["id"], "user_id": _USERS["member.yaml"]["id"]},
]

# The tables a seed kind writes, and the graph tables the creation path writes beside them.
_SEED_TABLES: list[Table | type[HasTable]] = [
    AppConfigDefinitionRow,
    AppConfigAllowListRow,
    AppConfigFragmentRow,
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
def app_config_fragment_seed_dir(
    tmp_path: Path, app_config_allow_list_seed_dir: Path, domain_seed_dir: Path
) -> Path:
    """The `app_config_allow_list` and `domain` directories plus one `app_config_fragment`
    seed file, so the entries and the owning domain are written first."""
    directory = tmp_path / "app_config_fragment"
    directory.mkdir()
    (directory / "fragments.yaml").write_text(
        yaml.safe_dump({
            "kind": "app_config_fragment",
            "version": 1,
            "items": _APP_CONFIG_FRAGMENTS,
        })
    )
    return tmp_path


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
def prometheus_query_preset_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `prometheus_query_preset` seed file and the
    `prometheus_query_preset_category` file its presets refer to."""
    directory = tmp_path / "prometheus_query_preset"
    directory.mkdir()
    (directory / "categories.yaml").write_text(
        yaml.safe_dump({
            "kind": "prometheus_query_preset_category",
            "version": 1,
            "items": _PROMETHEUS_QUERY_PRESET_CATEGORIES,
        })
    )
    (directory / "presets.yaml").write_text(
        yaml.safe_dump({
            "kind": "prometheus_query_preset",
            "version": 1,
            "items": _PROMETHEUS_QUERY_PRESETS,
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
def notification_rule_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `notification_rule` seed file."""
    directory = tmp_path / "notification_rule"
    directory.mkdir()
    (directory / "rules.yaml").write_text(
        yaml.safe_dump({
            "kind": "notification_rule",
            "version": 1,
            "items": _NOTIFICATION_RULES,
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
def idle_checker_assignment_seed_dir(
    tmp_path: Path, idle_checker_seed_dir: Path, domain_seed_dir: Path
) -> Path:
    """The `idle_checker` and `domain` directories plus one `idle_checker_assignment` seed
    file applying every checker to the default domain."""
    directory = tmp_path / "idle_checker_assignment"
    directory.mkdir()
    domain_id = _DOMAINS["default.yaml"]["id"]
    items = [
        {"idle_checker_id": checker["id"], "scope_type": "domain", "scope_id": domain_id}
        for checker in _IDLE_CHECKERS
    ]
    (directory / "assignments.yaml").write_text(
        yaml.safe_dump({"kind": "idle_checker_assignment", "version": 1, "items": items})
    )
    return tmp_path


@pytest.fixture
def container_registry_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `container_registry` seed file."""
    directory = tmp_path / "container_registry"
    directory.mkdir()
    (directory / "registries.yaml").write_text(
        yaml.safe_dump({"kind": "container_registry", "version": 1, "items": _CONTAINER_REGISTRIES})
    )
    return directory


@pytest.fixture
def container_registry_project_seed_dir(project_seed_dir: Path) -> Path:
    """The project directory plus the registries and the projects allowed on them, the
    research project taking the first registry as its default."""
    (project_seed_dir / "registries.yaml").write_text(
        yaml.safe_dump({"kind": "container_registry", "version": 1, "items": _CONTAINER_REGISTRIES})
    )
    research = _PROJECTS["research.yaml"]["id"]
    allowed = [
        {"registry_id": _CONTAINER_REGISTRIES[0]["id"], "project_id": research, "is_default": True},
        {"registry_id": _CONTAINER_REGISTRIES[1]["id"], "project_id": research},
    ]
    (project_seed_dir / "allowed-registries.yaml").write_text(
        yaml.safe_dump({"kind": "container_registry_project", "version": 1, "items": allowed})
    )
    return project_seed_dir


@pytest.fixture
def object_storage_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `object_storage` seed file."""
    directory = tmp_path / "object_storage"
    directory.mkdir()
    (directory / "storages.yaml").write_text(
        yaml.safe_dump({"kind": "object_storage", "version": 1, "items": _OBJECT_STORAGES})
    )
    return directory


@pytest.fixture
def storage_namespace_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `storage_namespace` seed file."""
    directory = tmp_path / "storage_namespace"
    directory.mkdir()
    (directory / "namespaces.yaml").write_text(
        yaml.safe_dump({"kind": "storage_namespace", "version": 1, "items": _STORAGE_NAMESPACES})
    )
    return directory


@pytest.fixture
def vfs_storage_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `vfs_storage` seed file."""
    directory = tmp_path / "vfs_storage"
    directory.mkdir()
    (directory / "storages.yaml").write_text(
        yaml.safe_dump({"kind": "vfs_storage", "version": 1, "items": _VFS_STORAGES})
    )
    return directory


@pytest.fixture
def domain_admin_id() -> str:
    return str(_ROLES["domain-admin.yaml"]["id"])


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
def default_domain_id() -> str:
    return str(_DOMAINS["default.yaml"]["id"])


@pytest.fixture
def resource_group_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `resource_group` seed file."""
    directory = tmp_path / "resource_group"
    directory.mkdir()
    (directory / "resource-groups.yaml").write_text(
        yaml.safe_dump({"kind": "resource_group", "version": 1, "items": _RESOURCE_GROUPS})
    )
    return directory


@pytest.fixture
def default_resource_group_id() -> str:
    return str(_RESOURCE_GROUPS[0]["id"])


@pytest.fixture
def resource_policy_seed_dir(tmp_path: Path) -> Path:
    """A directory of resource policy seed files, one file per kind."""
    directory = tmp_path / "resource_policy"
    directory.mkdir()
    for kind, item in _RESOURCE_POLICIES.items():
        (directory / f"{kind}.yaml").write_text(
            yaml.safe_dump({"kind": kind, "version": 1, "items": [item]})
        )
    return directory


@pytest.fixture
def runtime_variant_seed_dir(tmp_path: Path) -> Path:
    """A directory of runtime variant seed files, the shape `seeds/manager/runtime_variant/`
    has."""
    directory = tmp_path / "runtime_variant"
    directory.mkdir()
    for file_name, variant in _RUNTIME_VARIANTS.items():
        (directory / file_name).write_text(
            yaml.safe_dump({"kind": "runtime_variant", "version": 1, "items": [variant]})
        )
    return directory


@pytest.fixture
def vllm_variant_id() -> str:
    return str(_RUNTIME_VARIANTS["vllm.yaml"]["id"])


@pytest.fixture
def runtime_variant_preset_seed_dir(tmp_path: Path) -> Path:
    """A directory of runtime variant preset seed files, the shape
    `seeds/manager/runtime_variant_preset/` has."""
    directory = tmp_path / "runtime_variant_preset"
    directory.mkdir()
    for file_name, presets in _RUNTIME_VARIANT_PRESETS.items():
        (directory / file_name).write_text(
            yaml.safe_dump({"kind": "runtime_variant_preset", "version": 1, "items": presets})
        )
    return directory


@pytest.fixture
def max_model_len_preset_id() -> str:
    return str(_RUNTIME_VARIANT_PRESETS["vllm.yaml"][0]["id"])


@pytest.fixture
def deployment_preset_seed_dir(resource_slot_type_seed_dir: Path) -> Path:
    """The `resource_slot_type` directory plus one `deployment_preset` file per preset, so
    the slot names the presets state are registered first."""
    for file_name, preset in _DEPLOYMENT_PRESETS.items():
        (resource_slot_type_seed_dir / file_name).write_text(
            yaml.safe_dump({"kind": "deployment_preset", "version": 1, "items": [preset]})
        )
    return resource_slot_type_seed_dir


@pytest.fixture
def vllm_small_preset_id() -> str:
    return str(_DEPLOYMENT_PRESETS["vllm-small.yaml"]["id"])


@pytest.fixture
def minimal_preset_id() -> str:
    return str(_DEPLOYMENT_PRESETS["minimal.yaml"]["id"])


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
def resource_preset_seed_dir(tmp_path: Path) -> Path:
    """A directory of resource preset seed files, the shape `seeds/manager/resource_preset/`
    has."""
    directory = tmp_path / "resource_preset"
    directory.mkdir()
    for file_name, preset in _RESOURCE_PRESETS.items():
        (directory / file_name).write_text(
            yaml.safe_dump({"kind": "resource_preset", "version": 1, "items": [preset]})
        )
    return directory


@pytest.fixture
def small_preset_id() -> str:
    return str(_RESOURCE_PRESETS["small.yaml"]["id"])


@pytest.fixture
def user_seed_dir(tmp_path: Path) -> Path:
    """A directory of user seed files with the domains and the resource policies they
    refer to."""
    directory = tmp_path / "user"
    directory.mkdir()
    for file_name, domain in _DOMAINS.items():
        (directory / f"domain-{file_name}").write_text(
            yaml.safe_dump({"kind": "domain", "version": 1, "items": [domain]})
        )
    for kind in ("user_resource_policy", "keypair_resource_policy"):
        (directory / f"{kind}.yaml").write_text(
            yaml.safe_dump({"kind": kind, "version": 1, "items": [_RESOURCE_POLICIES[kind]]})
        )
    for file_name, user in _USERS.items():
        (directory / file_name).write_text(
            yaml.safe_dump({"kind": "user", "version": 1, "items": [user]})
        )
    return directory


@pytest.fixture
def admin_user_id() -> str:
    return str(_USERS["admin.yaml"]["id"])


@pytest.fixture
async def template_owner(db: ExtendedAsyncSAEngine) -> str:
    """The owner of the session templates in the graph, in the `templates` domain."""
    owner = _TEMPLATE_OWNER
    async with db.begin_session() as sess:
        await sess.execute(
            sa.insert(DomainRow).values(id=owner["domain_id"], name=owner["domain_name"])
        )
        await sess.execute(
            sa.insert(UserResourcePolicyRow).values(
                name=owner["resource_policy"],
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
            )
        )
        await sess.execute(sa.insert(UserRow).values(**owner))
        await sess.execute(
            sa.insert(VirtualEntityRow).values(
                entity_type=UserEntityType(), entity_id=owner["uuid"]
            )
        )
    return str(owner["uuid"])


@pytest.fixture
def session_template_files(tmp_path: Path) -> Path:
    """A directory of session template seed files, the shape `seeds/manager/session_template/`
    has."""
    directory = tmp_path / "session_template"
    directory.mkdir()
    for file_name, template in _SESSION_TEMPLATES.items():
        (directory / file_name).write_text(
            yaml.safe_dump({"kind": "session_template", "version": 1, "items": [template]})
        )
    return directory


@pytest.fixture
def session_template_seed_dir(session_template_files: Path, template_owner: str) -> Path:
    """The session template files, with their owner already written."""
    return session_template_files


@pytest.fixture
def task_template_id() -> str:
    return str(_SESSION_TEMPLATES["task.yaml"]["id"])


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


@pytest.fixture
def project_member_seed_dir(role_kind_seed_dir: Path) -> Path:
    """The role directory plus a project member file, so the projects, the users and the
    auto_assign role the items name are written first."""
    (role_kind_seed_dir / "project-members.yaml").write_text(
        yaml.safe_dump({"kind": "project_member", "version": 1, "items": _PROJECT_MEMBERS})
    )
    return role_kind_seed_dir
