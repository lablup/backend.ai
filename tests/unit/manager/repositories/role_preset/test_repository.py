"""A role preset name is unique within its scope, deleted presets included."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.errors.role_preset import RolePresetNameConflict
from ai.backend.manager.models.base import ensure_all_tables_registered
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_field import PermissionFieldRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.creators import (
    RolePermissionPresetCreator,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.creators import RolePresetCreator
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.role_preset.updaters import RolePresetUpdater
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
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
from ai.backend.manager.repositories.ops.v2.role_preset.provider import RolePresetOpsProvider
from ai.backend.manager.repositories.role_preset.repository import RolePresetRepository
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables

ensure_all_tables_registered()


@dataclass(frozen=True)
class _Presets:
    alive: RolePresetID
    deleted: RolePresetID
    other: RolePresetID


@dataclass(frozen=True)
class _NameCase:
    name: str
    scope_type: EntityType


@pytest.fixture
async def database(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        global_entity_ids,
        [
            DomainRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            UserRow,
            KeyPairRow,
            ProjectRow,
            VirtualEntityRow,
            EntityMembershipRow,
            EntityMembershipCapRow,
            EntityMembershipFieldRow,
            ScopeBindingRow,
            RolePresetRow,
            RolePermissionPresetRow,
            RoleRow,
            PermissionRow,
            PermissionFieldRow,
            UserRoleRow,
        ],
    ):
        yield global_entity_ids


@pytest.fixture
async def presets(database: ExtendedAsyncSAEngine) -> _Presets:
    alive = RolePresetRow(name="admin", scope_type=DomainEntityType())
    deleted = RolePresetRow(name="retired", scope_type=DomainEntityType(), deleted=True)
    other = RolePresetRow(name="member", scope_type=DomainEntityType())
    async with database.begin_session() as session:
        session.add_all([alive, deleted, other])
        await session.flush()
        return _Presets(
            alive=RolePresetID(alive.id),
            deleted=RolePresetID(deleted.id),
            other=RolePresetID(other.id),
        )


@pytest.fixture
def ops(database: ExtendedAsyncSAEngine) -> OpsRepository[RolePresetData]:
    return OpsRepository(V2DBOpsProvider(database))


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> RolePresetRepository:
    return RolePresetRepository(RolePresetOpsProvider(database))


class TestCreate:
    @pytest.mark.parametrize(
        "case",
        [
            _NameCase(name="admin", scope_type=DomainEntityType()),
            _NameCase(name="retired", scope_type=DomainEntityType()),
        ],
        ids=lambda case: case.name,
    )
    async def test_a_name_taken_in_the_scope_is_refused(
        self, ops: OpsRepository[RolePresetData], presets: _Presets, case: _NameCase
    ) -> None:
        with pytest.raises(RolePresetNameConflict):
            await ops.create_entity_with_fields(
                RolePresetCreator(name=case.name, scope_type=case.scope_type),
                list[RolePermissionPresetCreator](),
            )

    async def test_a_name_taken_in_another_scope_type_is_accepted(
        self, ops: OpsRepository[RolePresetData], presets: _Presets
    ) -> None:
        result = await ops.create_entity_with_fields(
            RolePresetCreator(name="admin", scope_type=ProjectEntityType()),
            list[RolePermissionPresetCreator](),
        )

        assert (result.data.name, result.data.scope_type) == ("admin", ProjectEntityType())


class TestUpdate:
    @pytest.mark.parametrize("name", ["admin", "retired"])
    async def test_renaming_onto_a_name_taken_in_the_scope_is_refused(
        self, repository: RolePresetRepository, presets: _Presets, name: str
    ) -> None:
        with pytest.raises(RolePresetNameConflict):
            await repository.update(
                RolePresetUpdater(preset_id=presets.other, name=OptionalState.update(name))
            )
