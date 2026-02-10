"""
Tests for PermissionControllerRepository.search_roles() functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.permission_controller.options import (
    RoleConditions,
    RoleOrders,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.testutils.db import with_tables


@dataclass
class CreatedRole:
    role_id: uuid.UUID
    role_name: str
    created_at: datetime


class TestSearchRoles:
    """Tests for searching roles with filtering and ordering."""

    @pytest.fixture
    async def db_with_rbac_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                RoleRow,
                UserRoleRow,
                PermissionRow,
                ObjectPermissionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        return PermissionControllerRepository(db_with_rbac_tables)

    @pytest.fixture
    async def created_roles(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> list[CreatedRole]:
        """Create multiple roles for testing."""
        created: list[CreatedRole] = []
        base_time = datetime(2026, 1, 1, tzinfo=UTC)

        async with db_with_rbac_tables.begin_session() as db_sess:
            for i, (name, description) in enumerate([
                ("admin-role", "Admin role"),
                ("editor-role", "Editor role"),
                ("viewer-role", "Viewer role"),
            ]):
                created_at = base_time + timedelta(minutes=i)
                role = RoleRow(
                    name=name,
                    description=description,
                    created_at=created_at,
                )
                db_sess.add(role)
                await db_sess.flush()
                created.append(
                    CreatedRole(
                        role_id=role.id,
                        role_name=name,
                        created_at=role.created_at,
                    )
                )

        return created

    async def test_search_roles_with_name_filter(
        self,
        repository: PermissionControllerRepository,
        created_roles: list[CreatedRole],
    ) -> None:
        """Name ends-with filter should match all roles ending with '-role'."""
        querier = BatchQuerier(
            conditions=[
                RoleConditions.by_name_ends_with(
                    StringMatchSpec(value="-role", case_insensitive=False, negated=False)
                ),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_roles(querier)

        assert result.total_count == len(created_roles)

    async def test_search_roles_ordered_by_name(
        self,
        repository: PermissionControllerRepository,
        created_roles: list[CreatedRole],
    ) -> None:
        querier = BatchQuerier(
            conditions=[],
            orders=[RoleOrders.name(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_roles(querier)

        names = [item.name for item in result.items]
        expected_names = sorted([r.role_name for r in created_roles])
        assert names == expected_names

    async def test_search_roles_ordered_by_created_at(
        self,
        repository: PermissionControllerRepository,
        created_roles: list[CreatedRole],
    ) -> None:
        """Roles created sequentially should be ordered by created_at."""
        querier = BatchQuerier(
            conditions=[],
            orders=[RoleOrders.created_at(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_roles(querier)

        role_ids = [item.id for item in result.items]
        expected_role_ids = [r.role_id for r in sorted(created_roles, key=lambda r: r.created_at)]
        assert role_ids == expected_role_ids, (
            f"Failed to order roles by created_at: got {[r.created_at for r in result.items]}, expected {[r.created_at for r in created_roles]}"
        )
