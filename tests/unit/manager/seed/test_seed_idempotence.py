"""Every registered kind can be applied any number of times and leave the same rows."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

# Columns an upsert rewrites without changing what the row states.
_TIMESTAMPS: Final[frozenset[str]] = frozenset({"created_at", "updated_at"})


@dataclass(frozen=True)
class IdempotenceCase:
    kind_name: SeedKind
    # The fixture giving the seed paths for the kind.
    seeds_fixture: str


# One case per registered kind. A kind added to the registry fails the test below until
# it is listed here.
_CASES: Final[list[IdempotenceCase]] = [
    IdempotenceCase(SeedKind.RESOURCE_SLOT_TYPE, "resource_slot_type_seed_dir"),
    IdempotenceCase(SeedKind.LOGIN_CLIENT_TYPE, "login_client_type_seed_dir"),
    IdempotenceCase(SeedKind.RETENTION_POLICY, "retention_policy_seed_dir"),
    IdempotenceCase(
        SeedKind.PROMETHEUS_QUERY_PRESET_CATEGORY, "prometheus_query_preset_category_seed_dir"
    ),
    IdempotenceCase(SeedKind.PROMETHEUS_QUERY_PRESET, "prometheus_query_preset_seed_dir"),
    IdempotenceCase(SeedKind.APP_CONFIG_DEFINITION, "app_config_definition_seed_dir"),
    IdempotenceCase(SeedKind.APP_CONFIG_ALLOW_LIST, "app_config_allow_list_seed_dir"),
    IdempotenceCase(SeedKind.CLIENT_IP_MASKING_POLICY, "client_ip_masking_policy_seed_dir"),
    IdempotenceCase(SeedKind.NOTIFICATION_CHANNEL, "notification_channel_seed_dir"),
    IdempotenceCase(SeedKind.NOTIFICATION_RULE, "notification_rule_seed_dir"),
    IdempotenceCase(SeedKind.RUNTIME_VARIANT, "runtime_variant_seed_dir"),
    IdempotenceCase(SeedKind.RUNTIME_VARIANT_PRESET, "runtime_variant_preset_seed_dir"),
    IdempotenceCase(SeedKind.ROLE_PRESET, "role_seed_dir"),
    IdempotenceCase(SeedKind.USER_RESOURCE_POLICY, "resource_policy_seed_dir"),
    IdempotenceCase(SeedKind.PROJECT_RESOURCE_POLICY, "resource_policy_seed_dir"),
    IdempotenceCase(SeedKind.KEYPAIR_RESOURCE_POLICY, "resource_policy_seed_dir"),
    IdempotenceCase(SeedKind.IDLE_CHECKER, "idle_checker_seed_dir"),
    IdempotenceCase(SeedKind.CONTAINER_REGISTRY, "container_registry_seed_dir"),
    IdempotenceCase(SeedKind.STORAGE_BACKEND_TYPE, "storage_backend_type_seed_dir"),
    IdempotenceCase(SeedKind.OBJECT_STORAGE, "object_storage_seed_dir"),
    IdempotenceCase(SeedKind.STORAGE_NAMESPACE, "storage_namespace_seed_dir"),
    IdempotenceCase(SeedKind.VFS_STORAGE, "vfs_storage_seed_dir"),
    IdempotenceCase(SeedKind.DOMAIN, "domain_seed_dir"),
    IdempotenceCase(SeedKind.PROJECT, "project_seed_dir"),
    IdempotenceCase(SeedKind.DEPLOYMENT_PRESET, "deployment_preset_seed_dir"),
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
    registered = {kind.name for kind in create_seed_kind_registry().ordered()}
    assert {case.kind_name for case in _CASES} == registered


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.kind_name)
async def test_applying_again_changes_nothing(
    case: IdempotenceCase,
    request: pytest.FixtureRequest,
    db: ExtendedAsyncSAEngine,
    repository: SeedRepository,
    seed_tables: list[sa.Table],
) -> None:
    seeds: Path = request.getfixturevalue(case.seeds_fixture)
    plan = SeedPlanner(create_seed_kind_registry()).plan([seeds])
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
