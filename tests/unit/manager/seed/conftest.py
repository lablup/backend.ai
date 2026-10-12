from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest
import yaml
from sqlalchemy import Table

from ai.backend.manager.models.base import ensure_all_tables_registered
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
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
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
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

# The tables a seed kind writes, and the graph tables the creation path writes beside them.
_SEED_TABLES: list[Table | type[HasTable]] = [
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
def repository(db: ExtendedAsyncSAEngine) -> OpsRepository[Any]:
    return OpsRepository(V2DBOpsProvider(db))


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
def domain_admin_id() -> str:
    return str(_ROLES["domain-admin.yaml"]["id"])
