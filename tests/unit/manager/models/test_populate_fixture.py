"""Tests for fixture inserts whose rows carry different sets of attributes."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.base import populate_fixture
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def db_engine(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(global_entity_ids, [ContainerRegistryRow]):
        yield global_entity_ids


def _registry(name: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "url": f"https://{name}",
        "registry_name": name,
        "type": "harbor2",
    }
    row.update(overrides)
    return row


async def test_row_attributes_survive_a_wider_row_that_follows(
    db_engine: ExtendedAsyncSAEngine,
) -> None:
    """A row's own attributes must reach the server even when the first row lacks them."""
    explicit_id = uuid.uuid4()
    await populate_fixture(
        db_engine,
        {
            "container_registries": [
                _registry("without-id"),
                _registry("with-id", id=explicit_id, is_global=False),
            ],
        },
    )

    async with db_engine.begin_readonly_session() as db_sess:
        rows = (await db_sess.scalars(sa.select(ContainerRegistryRow))).all()

    assert {row.registry_name for row in rows} == {"without-id", "with-id"}
    with_id = next(row for row in rows if row.registry_name == "with-id")
    assert with_id.id == explicit_id
    assert with_id.is_global is False
