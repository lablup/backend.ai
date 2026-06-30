"""Tests for the role preset repository.

Exercises the observable contracts of RolePresetRepository against a real
database: create round-trips (preset + dependent permission rows), id-based
get, search, single-row update, bulk soft delete / restore (per-id partial
update with silent skip for missing ids), single and bulk hard purge (returned
success rows + skipped non-existent ids), bulk add of permission-preset rows
(per-spec partial create), and bulk remove of permission-preset rows (per-id
partial purge).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import sqlalchemy as sa

from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.errors.role_preset import RolePresetNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkCreator,
    NoPagination,
    OffsetPagination,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.role_preset.creators import (
    RolePermissionPresetCreatorSpec,
    RolePermissionPresetDependentCreatorSpec,
    RolePresetCreatorSpec,
)
from ai.backend.manager.repositories.role_preset.repository import RolePresetRepository
from ai.backend.manager.repositories.role_preset.updaters import (
    RolePresetDeletedFlagUpdaterSpec,
    RolePresetUpdaterSpec,
)
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def repository(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[RolePresetRepository, None]:
    async with with_tables(
        database_connection,
        [
            RolePresetRow,  # parent
            RolePermissionPresetRow,  # child (FK -> role_presets.id, CASCADE)
        ],
    ):
        yield RolePresetRepository(DBOpsProvider(database_connection))


async def _count_permissions(
    engine: ExtendedAsyncSAEngine,
    preset_id: RolePresetID,
) -> int:
    async with engine.begin_readonly_session() as session:
        result = await session.execute(
            sa.select(sa.func.count())
            .select_from(RolePermissionPresetRow)
            .where(RolePermissionPresetRow.role_preset_id == preset_id)
        )
        return result.scalar_one()


async def _create_preset_with_permissions(
    repository: RolePresetRepository,
    name: str,
    permissions: list[tuple[EntityType, OperationType]],
) -> RolePresetID:
    created = await repository.create(
        RolePresetCreatorSpec(name=name, scope_type=ScopeType.DOMAIN),
        [
            RolePermissionPresetDependentCreatorSpec(entity_type=entity_type, operation=operation)
            for entity_type, operation in permissions
        ],
    )
    return created.id


def _by_preset(preset_id: RolePresetID) -> QueryCondition:
    # The model layer has no role-permission-preset conditions yet, so the
    # preset-scoping predicate is built inline here.
    return lambda: RolePermissionPresetRow.role_preset_id == preset_id


class TestCreate:
    async def test_persists_preset(self, repository: RolePresetRepository) -> None:
        created = await repository.create(
            RolePresetCreatorSpec(name="p1", scope_type=ScopeType.DOMAIN), []
        )
        fetched = await repository.role_preset(created.id)
        assert fetched.id == created.id
        assert fetched.name == "p1"
        assert fetched.scope_type == ScopeType.DOMAIN.to_element()
        assert fetched.deleted is False

    async def test_persists_dependent_permission_rows(
        self,
        repository: RolePresetRepository,
        database_connection: ExtendedAsyncSAEngine,
    ) -> None:
        created = await repository.create(
            RolePresetCreatorSpec(name="p1", scope_type=ScopeType.DOMAIN),
            [
                RolePermissionPresetDependentCreatorSpec(
                    entity_type=EntityType.VFOLDER, operation=OperationType.READ
                ),
                RolePermissionPresetDependentCreatorSpec(
                    entity_type=EntityType.VFOLDER, operation=OperationType.UPDATE
                ),
            ],
        )
        assert await _count_permissions(database_connection, created.id) == 2


class TestGet:
    async def test_round_trip(self, repository: RolePresetRepository) -> None:
        created = await repository.create(
            RolePresetCreatorSpec(name="p1", scope_type=ScopeType.DOMAIN), []
        )
        fetched = await repository.role_preset(created.id)
        assert fetched.id == created.id

    async def test_missing_raises(self, repository: RolePresetRepository) -> None:
        with pytest.raises(RolePresetNotFound):
            await repository.role_preset(RolePresetID(uuid4()))


class TestSearch:
    async def test_returns_all_with_count(self, repository: RolePresetRepository) -> None:
        await repository.create(RolePresetCreatorSpec(name="a", scope_type=ScopeType.DOMAIN), [])
        await repository.create(RolePresetCreatorSpec(name="b", scope_type=ScopeType.DOMAIN), [])

        result = await repository.search(BatchQuerier(pagination=NoPagination()))

        assert result.total_count == 2
        assert {item.name for item in result.items} == {"a", "b"}
        assert result.has_next_page is False
        assert result.has_previous_page is False


class TestUpdate:
    async def test_updates_field(self, repository: RolePresetRepository) -> None:
        created = await repository.create(
            RolePresetCreatorSpec(name="old", scope_type=ScopeType.DOMAIN), []
        )
        updater = Updater(
            spec=RolePresetUpdaterSpec(name=OptionalState.update("renamed")),
            pk_value=created.id,
        )

        updated = await repository.update(updater)

        assert updated.name == "renamed"
        assert (await repository.role_preset(created.id)).name == "renamed"

    async def test_missing_raises(self, repository: RolePresetRepository) -> None:
        updater = Updater(
            spec=RolePresetUpdaterSpec(name=OptionalState.update("x")),
            pk_value=RolePresetID(uuid4()),
        )
        with pytest.raises(RolePresetNotFound):
            await repository.update(updater)


class TestBulkDeleteRestore:
    async def test_soft_delete_then_restore(self, repository: RolePresetRepository) -> None:
        a = await repository.create(
            RolePresetCreatorSpec(name="a", scope_type=ScopeType.DOMAIN), []
        )
        b = await repository.create(
            RolePresetCreatorSpec(name="b", scope_type=ScopeType.DOMAIN), []
        )
        ids = [a.id, b.id]

        delete_updaters = [
            Updater(spec=RolePresetDeletedFlagUpdaterSpec(deleted=True), pk_value=preset_id)
            for preset_id in ids
        ]
        delete_result = await repository.bulk_update(delete_updaters)
        assert {row.id for row in delete_result.successes} == {a.id, b.id}
        assert delete_result.failures == []
        # Soft delete: the row is still present, only the flag flips.
        assert (await repository.role_preset(a.id)).deleted is True

        restore_updaters = [
            Updater(spec=RolePresetDeletedFlagUpdaterSpec(deleted=False), pk_value=preset_id)
            for preset_id in ids
        ]
        restore_result = await repository.bulk_update(restore_updaters)
        assert {row.id for row in restore_result.successes} == {a.id, b.id}
        assert restore_result.failures == []
        assert (await repository.role_preset(a.id)).deleted is False

    async def test_skips_missing_ids(self, repository: RolePresetRepository) -> None:
        existing = await repository.create(
            RolePresetCreatorSpec(name="x", scope_type=ScopeType.DOMAIN), []
        )

        # Non-existent id is silently skipped, matching bulk_purge semantics.
        updaters = [
            Updater(spec=RolePresetDeletedFlagUpdaterSpec(deleted=True), pk_value=preset_id)
            for preset_id in [existing.id, RolePresetID(uuid4())]
        ]
        result = await repository.bulk_update(updaters)

        assert [row.id for row in result.successes] == [existing.id]
        assert result.failures == []


class TestPurge:
    async def test_single_purge_success_then_false(self, repository: RolePresetRepository) -> None:
        created = await repository.create(
            RolePresetCreatorSpec(name="p1", scope_type=ScopeType.DOMAIN), []
        )
        assert await repository.purge(created.id) is True
        # Already gone -> no row matched -> False.
        assert await repository.purge(created.id) is False
        with pytest.raises(RolePresetNotFound):
            await repository.role_preset(created.id)

    async def test_bulk_purge_returns_only_existing(self, repository: RolePresetRepository) -> None:
        a = await repository.create(
            RolePresetCreatorSpec(name="a", scope_type=ScopeType.DOMAIN), []
        )
        b = await repository.create(
            RolePresetCreatorSpec(name="b", scope_type=ScopeType.DOMAIN), []
        )

        # One id does not exist: it is skipped, not an error.
        result = await repository.bulk_purge([a.id, b.id, RolePresetID(uuid4())])

        assert {preset.id for preset in result.successes} == {a.id, b.id}
        assert result.failures == []


class TestPermissions:
    async def test_bulk_add_returns_rows_bound_to_preset(
        self, repository: RolePresetRepository
    ) -> None:
        preset = await repository.create(
            RolePresetCreatorSpec(name="p1", scope_type=ScopeType.DOMAIN), []
        )
        result = await repository.bulk_add_permissions(
            BulkCreator(
                specs=[
                    RolePermissionPresetCreatorSpec(
                        role_preset_id=preset.id,
                        entity_type=EntityType.SESSION,
                        operation=OperationType.READ,
                    ),
                    RolePermissionPresetCreatorSpec(
                        role_preset_id=preset.id,
                        entity_type=EntityType.SESSION,
                        operation=OperationType.UPDATE,
                    ),
                ]
            )
        )

        assert len(result.successes) == 2
        assert result.failures == []
        assert all(perm.role_preset_id == preset.id for perm in result.successes)

    async def test_bulk_remove_returns_rows(
        self,
        repository: RolePresetRepository,
        database_connection: ExtendedAsyncSAEngine,
    ) -> None:
        preset = await repository.create(
            RolePresetCreatorSpec(name="p1", scope_type=ScopeType.DOMAIN), []
        )
        added = await repository.bulk_add_permissions(
            BulkCreator(
                specs=[
                    RolePermissionPresetCreatorSpec(
                        role_preset_id=preset.id,
                        entity_type=EntityType.SESSION,
                        operation=OperationType.READ,
                    ),
                    RolePermissionPresetCreatorSpec(
                        role_preset_id=preset.id,
                        entity_type=EntityType.SESSION,
                        operation=OperationType.UPDATE,
                    ),
                ]
            )
        )
        permission_ids = [perm.id for perm in added.successes]

        result = await repository.bulk_remove_permissions(permission_ids)

        assert {perm.id for perm in result.successes} == set(permission_ids)
        assert result.failures == []
        assert await _count_permissions(database_connection, preset.id) == 0


class TestSearchPermissionPresets:
    @pytest.fixture
    async def preset_with_permissions(self, repository: RolePresetRepository) -> RolePresetID:
        """A single preset carrying three permission entries with distinct operations."""
        return await _create_preset_with_permissions(
            repository,
            "p1",
            [
                (EntityType.VFOLDER, OperationType.CREATE),
                (EntityType.VFOLDER, OperationType.READ),
                (EntityType.VFOLDER, OperationType.UPDATE),
            ],
        )

    @pytest.fixture
    async def target_among_other_presets(self, repository: RolePresetRepository) -> RolePresetID:
        """A target preset (three entries) alongside an unrelated preset (one entry)."""
        target = await _create_preset_with_permissions(
            repository,
            "target",
            [
                (EntityType.VFOLDER, OperationType.READ),
                (EntityType.VFOLDER, OperationType.UPDATE),
                (EntityType.SESSION, OperationType.READ),
            ],
        )
        await _create_preset_with_permissions(
            repository, "other", [(EntityType.IMAGE, OperationType.READ)]
        )
        return target

    async def test_scopes_to_role_preset(
        self,
        repository: RolePresetRepository,
        target_among_other_presets: RolePresetID,
    ) -> None:
        result = await repository.search_permission_presets(
            BatchQuerier(
                pagination=NoPagination(),
                conditions=[_by_preset(target_among_other_presets)],
            )
        )

        assert result.total_count == 3
        assert all(item.role_preset_id == target_among_other_presets for item in result.items)

    @pytest.mark.parametrize(
        ("limit", "offset", "expected_len", "expected_next", "expected_prev"),
        [
            (2, 0, 2, True, False),  # first page of three
            (2, 2, 1, False, True),  # last page
            (10, 0, 3, False, False),  # whole set in one page
        ],
    )
    async def test_paginates(
        self,
        repository: RolePresetRepository,
        preset_with_permissions: RolePresetID,
        limit: int,
        offset: int,
        expected_len: int,
        expected_next: bool,
        expected_prev: bool,
    ) -> None:
        result = await repository.search_permission_presets(
            BatchQuerier(
                pagination=OffsetPagination(limit=limit, offset=offset),
                conditions=[_by_preset(preset_with_permissions)],
            )
        )

        assert len(result.items) == expected_len
        assert result.total_count == 3
        assert result.has_next_page is expected_next
        assert result.has_previous_page is expected_prev

    async def test_orders_by_operation(
        self,
        repository: RolePresetRepository,
        preset_with_permissions: RolePresetID,
    ) -> None:
        result = await repository.search_permission_presets(
            BatchQuerier(
                pagination=NoPagination(),
                conditions=[_by_preset(preset_with_permissions)],
                orders=[RolePermissionPresetRow.operation.asc()],
            )
        )

        operations = [item.operation for item in result.items]
        assert operations == sorted(operations, key=lambda op: op.value)
