"""Runs the role preset name key's pre-check against a real database.

Presets sharing one name in one scope stop the migration, deleted rows and presets for
every scope of a type included.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.alembic.versions.a37b92a3e063_key_role_presets_by_name_and_scope import (
    refuse_duplicate_names,
)
from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables

# The table had no key on the name when this migration ran, so the pre-migration shape
# is declared here.
_metadata = sa.MetaData()
_role_presets = sa.Table(
    "role_presets",
    _metadata,
    sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")),
    sa.Column("name", sa.String(64), nullable=False),
    sa.Column("scope_type", sa.String(32), nullable=False),
    sa.Column("scope_id", GUID, nullable=True),
    sa.Column("deleted", sa.Boolean, nullable=False, server_default=sa.false()),
)

_DOMAIN_A = uuid.UUID("00000000-0000-0000-0000-00000000000a")
_DOMAIN_B = uuid.UUID("00000000-0000-0000-0000-00000000000b")


@dataclass(frozen=True)
class _Preset:
    name: str
    scope_type: str = "domain"
    scope_id: uuid.UUID | None = None
    deleted: bool = False


@dataclass(frozen=True)
class _PresetsCase:
    label: str
    presets: list[_Preset] = field(default_factory=list)


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, [_role_presets]):
        yield database_connection


@pytest.fixture
async def laid(db: ExtendedAsyncSAEngine, case: _PresetsCase) -> ExtendedAsyncSAEngine:
    async with db.begin() as conn:
        await conn.execute(
            sa.insert(_role_presets),
            [
                {
                    "name": preset.name,
                    "scope_type": preset.scope_type,
                    "scope_id": preset.scope_id,
                    "deleted": preset.deleted,
                }
                for preset in case.presets
            ],
        )
    return db


class TestRefuseDuplicateNames:
    @pytest.mark.parametrize(
        "case",
        [
            _PresetsCase(
                label="both-alive",
                presets=[_Preset(name="admin"), _Preset(name="admin")],
            ),
            _PresetsCase(
                label="one-deleted",
                presets=[_Preset(name="admin"), _Preset(name="admin", deleted=True)],
            ),
            _PresetsCase(
                label="same-scope-id",
                presets=[
                    _Preset(name="admin", scope_id=_DOMAIN_A),
                    _Preset(name="admin", scope_id=_DOMAIN_A),
                ],
            ),
        ],
        ids=lambda case: case.label,
    )
    async def test_a_name_shared_in_one_scope_stops_the_migration(
        self, laid: ExtendedAsyncSAEngine, case: _PresetsCase
    ) -> None:
        with pytest.raises(RuntimeError, match="'admin'"):
            async with laid.begin() as conn:
                await conn.run_sync(refuse_duplicate_names)

    @pytest.mark.parametrize(
        "case",
        [
            _PresetsCase(
                label="other-scope-type",
                presets=[_Preset(name="admin"), _Preset(name="admin", scope_type="project")],
            ),
            _PresetsCase(
                label="other-scope-id",
                presets=[
                    _Preset(name="admin", scope_id=_DOMAIN_A),
                    _Preset(name="admin", scope_id=_DOMAIN_B),
                ],
            ),
            _PresetsCase(
                label="every-scope-and-one-scope",
                presets=[_Preset(name="admin"), _Preset(name="admin", scope_id=_DOMAIN_A)],
            ),
            _PresetsCase(
                label="other-name",
                presets=[_Preset(name="admin"), _Preset(name="member")],
            ),
        ],
        ids=lambda case: case.label,
    )
    async def test_names_distinct_within_each_scope_pass(
        self, laid: ExtendedAsyncSAEngine, case: _PresetsCase
    ) -> None:
        async with laid.begin() as conn:
            await conn.run_sync(refuse_duplicate_names)
