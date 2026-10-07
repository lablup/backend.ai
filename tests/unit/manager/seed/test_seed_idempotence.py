"""Every registered kind can be applied any number of times and leave the same rows."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.seed.registry import SeedKindRegistry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlanner

# Columns an upsert rewrites without changing what the row states.
_TIMESTAMPS: Final[frozenset[str]] = frozenset({"created_at", "updated_at"})


@dataclass(frozen=True)
class IdempotenceCase:
    kind_name: str
    # The fixture giving the seed paths for the kind.
    seeds_fixture: str


# One case per registered kind. A kind added to the registry fails the test below until
# it is listed here.
_CASES: Final[list[IdempotenceCase]] = [
    IdempotenceCase("role_preset", "role_seed_dir"),
]


async def _snapshot(
    db: ExtendedAsyncSAEngine, tables: Sequence[sa.Table]
) -> dict[str, list[tuple[str, ...]]]:
    snapshot: dict[str, list[tuple[str, ...]]] = {}
    async with db.begin_readonly() as conn:
        for table in tables:
            columns = [column for column in table.columns if column.name not in _TIMESTAMPS]
            rows = await conn.execute(sa.select(*columns))
            snapshot[table.name] = sorted(tuple(map(str, row)) for row in rows)
    return snapshot


def test_every_registered_kind_has_a_case() -> None:
    registered = {kind.name() for kind in SeedKindRegistry.default().ordered()}
    assert {case.kind_name for case in _CASES} == registered


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.kind_name)
async def test_applying_again_changes_nothing(
    case: IdempotenceCase,
    request: pytest.FixtureRequest,
    db: ExtendedAsyncSAEngine,
    repository: OpsRepository[Any],
    seed_tables: list[sa.Table],
) -> None:
    seeds: Path = request.getfixturevalue(case.seeds_fixture)
    plan = SeedPlanner(SeedKindRegistry.default()).plan([seeds])
    assert plan.rejections == []
    applier = SeedApplier(repository)

    first = await applier.apply(plan, overwrite=False)
    assert first[case.kind_name].skipped == []
    assert first[case.kind_name].failed == []
    written = await _snapshot(db, seed_tables)

    again = await applier.apply(plan, overwrite=False)
    assert again[case.kind_name].succeeded == []
    assert await _snapshot(db, seed_tables) == written

    for _ in range(2):
        await applier.apply(plan, overwrite=True)
        assert await _snapshot(db, seed_tables) == written
