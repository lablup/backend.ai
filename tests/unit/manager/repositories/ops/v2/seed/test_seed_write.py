"""V2SeedWriteOps against a real database: one savepoint per item, so an item a
constraint refuses fails alone and the rest are written."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import Any, override

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.errors.role_preset import RolePresetScopeNotFound
from ai.backend.manager.models.base import ensure_all_tables_registered
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.upserters import (
    RolePermissionPresetUpserter,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.role_preset.upserters import RolePresetUpserter
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
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
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite, SeedWriteItemResult
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    RolePresetRow,
    RolePermissionPresetRow,
    VirtualEntityRow,
    ScopeBindingRow,
    EntityLabelRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
]


@dataclass
class OrphanPermissionUpserter(RolePermissionPresetUpserter):
    """A permission row naming a preset that does not exist."""

    @override
    def build_insert_values(self, owner_id: RolePresetID) -> dict[str, Any]:
        return {**super().build_insert_values(owner_id), "role_preset_id": uuid.uuid4()}


@dataclass
class MappedOrphanPermissionUpserter(OrphanPermissionUpserter):
    """An orphan permission row whose spec turns the violation into a domain error."""

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=RolePresetScopeNotFound("mapped"),
            ),
        )


@dataclass
class IdKeyedPermissionUpserter(RolePermissionPresetUpserter):
    """A permission row keyed on its id, so the bit it repeats collides on the other
    unique key."""

    @override
    def index_elements(self) -> list[str]:
        return ["id"]


@pytest.fixture
async def db(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    ensure_all_tables_registered()
    async with with_tables(global_entity_ids, _TABLES):
        yield global_entity_ids


@pytest.fixture
def repository(db: ExtendedAsyncSAEngine) -> SeedRepository:
    return SeedRepository(SeedOpsProvider(db))


def _preset(name: str, *permissions: RolePermissionPresetUpserter) -> SeedWrite:
    return SeedWrite(
        upserter=RolePresetUpserter(
            id=RolePresetID(uuid.uuid4()),
            name=name,
            scope_type=EntityType("domain"),
            auto_assign=False,
        ),
        field_upserters=permissions,
        field_purgers=(),
    )


def _read(entity_type: str = "agent") -> RolePermissionPresetUpserter:
    return RolePermissionPresetUpserter(
        entity_type=EntityType(entity_type), permission=Permission.READ
    )


async def _preset_names(db: ExtendedAsyncSAEngine) -> set[str]:
    async with db.begin_readonly() as conn:
        return set((await conn.scalars(sa.select(RolePresetRow.name))).all())


async def _permission_count(db: ExtendedAsyncSAEngine) -> int:
    async with db.begin_readonly() as conn:
        count = await conn.scalar(sa.select(sa.func.count()).select_from(RolePermissionPresetRow))
        return int(count or 0)


async def _rename(db: ExtendedAsyncSAEngine, write: SeedWrite, name: str) -> None:
    preset = write.upserter
    assert isinstance(preset, RolePresetUpserter)
    async with db.begin_session() as sess:
        await sess.execute(
            sa.update(RolePresetRow).where(RolePresetRow.id == preset.id).values(name=name)
        )


class TestWrite:
    async def test_the_rows_are_inserted(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository
    ) -> None:
        results = await repository.partial_write(
            [_preset("first", _read("agent"), _read("domain"))], overwrite=False
        )
        assert results == [SeedWriteItemResult(written=True)]
        assert await _preset_names(db) == {"first"}
        assert await _permission_count(db) == 2

    async def test_an_existing_row_is_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository
    ) -> None:
        write = _preset("first", _read())
        await repository.partial_write([write], overwrite=False)
        await _rename(db, write, "renamed")

        results = await repository.partial_write([write], overwrite=False)

        assert results == [SeedWriteItemResult(written=False)]
        assert await _preset_names(db) == {"renamed"}

    async def test_overwrite_rewrites_an_existing_row(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository
    ) -> None:
        write = _preset("first", _read())
        await repository.partial_write([write], overwrite=False)
        await _rename(db, write, "renamed")

        results = await repository.partial_write([write], overwrite=True)

        assert results == [SeedWriteItemResult(written=True)]
        assert await _preset_names(db) == {"first"}


class TestRefusedItem:
    @pytest.mark.parametrize("overwrite", [False, True], ids=["insert", "overwrite"])
    async def test_a_foreign_key_violation_fails_its_own_item(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, overwrite: bool
    ) -> None:
        orphan = OrphanPermissionUpserter(
            entity_type=EntityType("agent"), permission=Permission.READ
        )
        results = await repository.partial_write(
            [_preset("first", _read()), _preset("orphan", orphan), _preset("last", _read())],
            overwrite=overwrite,
        )

        assert [result.written for result in results] == [True, False, True]
        assert isinstance(results[1].error, ForeignKeyViolationError)
        assert await _preset_names(db) == {"first", "last"}

    @pytest.mark.parametrize("overwrite", [False, True], ids=["insert", "overwrite"])
    async def test_a_violation_the_spec_maps_to_a_domain_error_fails_its_own_item(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, overwrite: bool
    ) -> None:
        mapped = MappedOrphanPermissionUpserter(
            entity_type=EntityType("agent"), permission=Permission.READ
        )
        results = await repository.partial_write(
            [_preset("first", _read()), _preset("mapped", mapped), _preset("last", _read())],
            overwrite=overwrite,
        )

        assert [result.written for result in results] == [True, False, True]
        assert isinstance(results[1].error, ForeignKeyViolationError)
        assert await _preset_names(db) == {"first", "last"}

    async def test_a_collision_on_another_unique_key_fails_its_own_item(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository
    ) -> None:
        repeated = IdKeyedPermissionUpserter(
            entity_type=EntityType("agent"), permission=Permission.READ
        )
        results = await repository.partial_write(
            [_preset("repeats", _read(), repeated), _preset("last", _read())], overwrite=False
        )

        assert [result.written for result in results] == [False, True]
        error = results[0].error
        assert isinstance(error, UniqueConstraintViolationError)
        assert error.constraint_name == "uq_role_permission_presets_preset_entity_op"
        assert await _preset_names(db) == {"last"}
