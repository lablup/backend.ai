"""
Tests for the global permission search through ``OpsRepository.global_search``.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.agent import AgentRow

# ORM cluster registration: configure_mappers() (triggered when this isolated
# test registers a domain-cluster row) resolves string relationships against the
# registry. These rows are reachable via relationships but are not otherwise
# imported/registered by this test; _ORM_CLUSTER keeps them live.
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.searchable_fields import (
    PermissionSearchableFields,
)
from ai.backend.manager.models.rbac_models.permission.searchers import RolePermissionSearcher
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_group import ResourceGroupForDomainRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables

_ORM_CLUSTER = (
    AgentRow,
    ResourceGroupForDomainRow,
    ImageRow,
)


@dataclass
class RoleWithPermissions:
    role_id: uuid.UUID
    permission_ids: list[uuid.UUID]


class TestSearchPermissions:
    """Tests for searching permissions."""

    @pytest.fixture
    async def db_with_rbac_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                PermissionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> OpsRepository[PermissionData]:
        return OpsRepository[PermissionData](V2DBOpsProvider(db_with_rbac_tables))

    @pytest.fixture
    async def role_with_permissions(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> RoleWithPermissions:
        """Create a role with multiple permissions."""
        role_id = uuid.uuid4()
        perm_ids: list[uuid.UUID] = []

        async with db_with_rbac_tables.begin_session() as db_sess:
            role = RoleRow(
                scope_type=EntityType("project"),
                scope_id=uuid.uuid4(),
                id=role_id,
                name="test-role-perms",
                description="Test role for permissions",
            )
            db_sess.add(role)
            await db_sess.flush()

            for entity_type, operation in [
                (VFolderEntityType(), Permission.READ),
                (VFolderEntityType(), Permission.UPDATE),
                (SessionEntityType(), Permission.CREATE),
                (ImageEntityType(), Permission.READ),
            ]:
                perm = PermissionRow(
                    role_id=role_id,
                    entity_type=entity_type,
                    permission=operation,
                )
                db_sess.add(perm)
                await db_sess.flush()
                perm_ids.append(perm.id)

        return RoleWithPermissions(role_id=role_id, permission_ids=perm_ids)

    async def test_search_permissions_with_entity_type_filter(
        self,
        repository: OpsRepository[PermissionData],
        role_with_permissions: RoleWithPermissions,
    ) -> None:
        searcher = RolePermissionSearcher(
            conditions=[
                PermissionSearchableFields.own.entity_type.filter.equals(
                    StringMatchSpec(
                        value=str(VFolderEntityType()), case_insensitive=False, negated=False
                    )
                ),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.global_search(GlobalSearcher(used_by=(), searcher=searcher))

        assert result.total_count == 2
        for item in result.items:
            assert item.entity_type == VFolderEntityType()

    async def test_search_permissions_ordered_by_entity_type(
        self,
        repository: OpsRepository[PermissionData],
        role_with_permissions: RoleWithPermissions,
    ) -> None:
        searcher = RolePermissionSearcher(
            conditions=[],
            orders=[PermissionSearchableFields.own.entity_type.order.apply(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.global_search(GlobalSearcher(used_by=(), searcher=searcher))

        entity_types = [item.entity_type for item in result.items]
        assert entity_types == sorted(entity_types)
