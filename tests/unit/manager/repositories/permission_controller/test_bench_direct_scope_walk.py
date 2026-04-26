"""
Benchmark — direct scope walk vs legacy scope-chain CTE path.

Compares the BA-5842 fan-in dedup resolver against the legacy
``resolve_effective_permissions`` and the pre-refactor bulk path
(``_check_permissions_via_scope_chain`` is still in the codebase and
behaves identically to the old bulk implementation when called with K
entities).

Three call paths under measurement:
  * Effective permissions:
      legacy = ``resolve_effective_permissions``
      new    = ``resolve_effective_permissions_via_direct_scope_walk``
  * Bulk permission check:
      legacy = ``_check_permissions_via_scope_chain`` + post-filter
      new    = ``check_bulk_permission_with_scope_chain`` (now routed
               through the shared path)

Scenarios sweep K (number of input entities) and ``num_parents`` (number
of unique direct parent projects), plus a permission grant at DOMAIN
scope so the recursive walk exercises the chain (``D = 2``).

Skipped by default. Enable with ``RUN_BENCH=1`` and run with ``-s`` so
the printed tables and EXPLAIN plans are visible:

    RUN_BENCH=1 pytest -s \\
        tests/unit/manager/repositories/permission_controller/\\
test_bench_direct_scope_walk.py

Tunables (env vars):
  BENCH_REPEATS  — measurements per call path (default 30)
  BENCH_WARMUPS  — discarded warmup iterations (default 3)
"""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any, cast

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from ai.backend.common.data.permission.types import (
    RBACElementType,
    RelationType,
)
from ai.backend.manager.data.permission.role import (
    BulkPermissionCheckInput,
    EffectivePermissionsInput,
)
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import (
    ObjectPermissionRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import (
    PermissionRow,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
    _ScopeChainQueryParams,
)
from ai.backend.testutils.db import with_tables

if not os.environ.get("RUN_BENCH"):
    pytest.skip(
        "Set RUN_BENCH=1 to enable the BA-5842 benchmark suite",
        allow_module_level=True,
    )

REPEATS = int(os.environ.get("BENCH_REPEATS", "30"))
WARMUPS = int(os.environ.get("BENCH_WARMUPS", "3"))


# ─────────────────────────────────────────────────────────────────────
# Seed helpers
# ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BenchSeed:
    user_id: uuid.UUID
    vfolder_ids: list[str]
    project_ids: list[str]
    domain_id: str


async def _seed(
    engine: ExtendedAsyncSAEngine,
    *,
    K: int,
    num_parents: int,
) -> BenchSeed:
    """Seed K vfolders distributed across ``num_parents`` projects under one domain.

    Permission is granted at DOMAIN scope so the recursive scope walk has
    to traverse two AUTO edges (vfolder → project → domain). The parents
    are evenly spread across the K vfolders via round-robin assignment,
    so ``num_parents=1`` gives maximal fan-in and ``num_parents=K`` gives
    no fan-in at all.
    """
    if num_parents > K:
        num_parents = K
    user_id = uuid.uuid4()
    role_id = uuid.uuid4()
    domain_id = str(uuid.uuid4())
    project_ids = [str(uuid.uuid4()) for _ in range(num_parents)]
    vfolder_ids = [str(uuid.uuid4()) for _ in range(K)]

    async with engine.begin() as conn:
        await conn.execute(
            sa.insert(UserResourcePolicyRow.__table__).values(
                name="bench-rbac-policy",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
        )
        await conn.execute(
            sa.insert(UserRow.__table__).values(
                uuid=user_id,
                email="bench@test.com",
                resource_policy="bench-rbac-policy",
                status=UserStatus.ACTIVE,
                need_password_change=False,
                sudo_session_enabled=False,
            )
        )
        await conn.execute(
            sa.insert(RoleRow.__table__).values(
                id=role_id,
                name="bench-role",
                status=RoleStatus.ACTIVE,
            )
        )
        await conn.execute(
            sa.insert(UserRoleRow.__table__).values(
                user_id=user_id,
                role_id=role_id,
            )
        )
        await conn.execute(
            sa.insert(PermissionRow.__table__).values(
                role_id=role_id,
                scope_type=ScopeType.DOMAIN,
                scope_id=domain_id,
                entity_type=EntityType.VFOLDER,
                operation=OperationType.READ,
            )
        )
        await conn.execute(
            sa.insert(AssociationScopesEntitiesRow.__table__),
            [
                {
                    "scope_type": ScopeType.DOMAIN,
                    "scope_id": domain_id,
                    "entity_type": EntityType.PROJECT,
                    "entity_id": pid,
                    "relation_type": RelationType.AUTO,
                }
                for pid in project_ids
            ],
        )
        await conn.execute(
            sa.insert(AssociationScopesEntitiesRow.__table__),
            [
                {
                    "scope_type": ScopeType.PROJECT,
                    "scope_id": project_ids[i % num_parents],
                    "entity_type": EntityType.VFOLDER,
                    "entity_id": vfolder_ids[i],
                    "relation_type": RelationType.AUTO,
                }
                for i in range(K)
            ],
        )
    return BenchSeed(
        user_id=user_id,
        vfolder_ids=vfolder_ids,
        project_ids=project_ids,
        domain_id=domain_id,
    )


# ─────────────────────────────────────────────────────────────────────
# Bench helpers
# ─────────────────────────────────────────────────────────────────────


async def _measure(
    coro_fn: Callable[[], Awaitable[object]],
    *,
    repeats: int = REPEATS,
    warmups: int = WARMUPS,
) -> tuple[float, float]:
    """Returns ``(p50_ms, p95_ms)`` over ``repeats`` after ``warmups`` discarded runs."""
    for _ in range(warmups):
        await coro_fn()
    samples: list[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        await coro_fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples.sort()
    p50 = samples[len(samples) // 2]
    p95 = samples[max(0, round(len(samples) * 0.95) - 1)]
    return p50, p95


# (label, K, num_parents)
_SCENARIOS: list[tuple[str, int, int]] = [
    ("high_fanin K=10", 10, 1),
    ("high_fanin K=100", 100, 1),
    ("high_fanin K=1000", 1000, 1),
    ("high_fanin K=10000", 10000, 1),
    ("med_fanin K=1000 parents=10", 1000, 10),
    ("med_fanin K=1000 parents=100", 1000, 100),
    ("low_fanin K=1000 parents=K", 1000, 1000),
]


# ─────────────────────────────────────────────────────────────────────
# Replicated query builders for EXPLAIN ANALYZE
#
# These mirror the production SELECTs verbatim so we can extract the SA
# expression, compile it with ``literal_binds=True``, and run the result
# through ``EXPLAIN (ANALYZE, BUFFERS, VERBOSE)``. Drift here means the
# bench is no longer measuring what production runs — keep them in sync.
# ─────────────────────────────────────────────────────────────────────


def _legacy_effective_select(
    user_id: uuid.UUID,
    target_entity_type: EntityType,
    target_scope_type: ScopeType,
    permission_entity_type: EntityType,
    entity_ids: list[str],
) -> sa.CompoundSelect[Any]:
    perm = PermissionRow.__table__
    user_roles = UserRoleRow.__table__
    roles = RoleRow.__table__
    chain_cte = PermissionDBSource._build_scope_chain_cte(target_entity_type, entity_ids)
    chain_q = (
        sa.select(chain_cte.c.entity_id, perm.c.operation)
        .select_from(
            chain_cte.join(
                perm,
                sa.and_(
                    perm.c.scope_type == chain_cte.c.scope_type,
                    perm.c.scope_id == chain_cte.c.scope_id,
                ),
            )
            .join(roles, roles.c.id == perm.c.role_id)
            .join(user_roles, user_roles.c.role_id == roles.c.id)
        )
        .where(
            sa.and_(
                user_roles.c.user_id == user_id,
                roles.c.status == RoleStatus.ACTIVE,
                perm.c.entity_type == permission_entity_type,
            )
        )
    )
    self_q = (
        sa.select(perm.c.scope_id.label("entity_id"), perm.c.operation)
        .select_from(
            perm.join(roles, roles.c.id == perm.c.role_id).join(
                user_roles, user_roles.c.role_id == roles.c.id
            )
        )
        .where(
            sa.and_(
                user_roles.c.user_id == user_id,
                roles.c.status == RoleStatus.ACTIVE,
                perm.c.scope_type == target_scope_type,
                perm.c.scope_id.in_(entity_ids),
                perm.c.entity_type == permission_entity_type,
            )
        )
    )
    return sa.union_all(chain_q, self_q)


def _new_effective_select(
    user_id: uuid.UUID,
    target_entity_type: EntityType,
    target_scope_type: ScopeType,
    permission_entity_type: EntityType,
    entity_ids: list[str],
) -> sa.CompoundSelect[Any]:
    ase = AssociationScopesEntitiesRow.__table__
    perm = PermissionRow.__table__
    user_roles = UserRoleRow.__table__
    roles = RoleRow.__table__

    direct_scopes_cte = (
        sa.select(ase.c.entity_id, ase.c.scope_type, ase.c.scope_id)
        .where(
            sa.and_(
                ase.c.entity_type == target_entity_type,
                ase.c.entity_id.in_(entity_ids),
                ase.c.relation_type == RelationType.AUTO,
            )
        )
        .cte("direct_scopes")
    )
    scope_walk_cte = PermissionDBSource._build_direct_scope_walk_cte(direct_scopes_cte)

    chain_q = (
        sa.select(direct_scopes_cte.c.entity_id, perm.c.operation)
        .select_from(
            direct_scopes_cte.join(
                scope_walk_cte,
                sa.and_(
                    scope_walk_cte.c.start_scope_type == direct_scopes_cte.c.scope_type,
                    scope_walk_cte.c.start_scope_id == direct_scopes_cte.c.scope_id,
                ),
            )
            .join(
                perm,
                sa.and_(
                    perm.c.scope_type == scope_walk_cte.c.scope_type,
                    perm.c.scope_id == scope_walk_cte.c.scope_id,
                ),
            )
            .join(roles, roles.c.id == perm.c.role_id)
            .join(user_roles, user_roles.c.role_id == roles.c.id)
        )
        .where(
            sa.and_(
                user_roles.c.user_id == user_id,
                roles.c.status == RoleStatus.ACTIVE,
                perm.c.entity_type == permission_entity_type,
            )
        )
    )
    self_q = (
        sa.select(perm.c.scope_id.label("entity_id"), perm.c.operation)
        .select_from(
            perm.join(roles, roles.c.id == perm.c.role_id).join(
                user_roles, user_roles.c.role_id == roles.c.id
            )
        )
        .where(
            sa.and_(
                user_roles.c.user_id == user_id,
                roles.c.status == RoleStatus.ACTIVE,
                perm.c.scope_type == target_scope_type,
                perm.c.scope_id.in_(entity_ids),
                perm.c.entity_type == permission_entity_type,
            )
        )
    )
    return sa.union_all(chain_q, self_q)


async def _explain(
    engine: ExtendedAsyncSAEngine,
    stmt: sa.CompoundSelect[Any],
) -> str:
    dialect = cast(Any, postgresql.dialect)()
    sql = str(
        cast(Any, stmt).compile(
            dialect=dialect,
            compile_kwargs={"literal_binds": True},
        )
    )
    async with engine.connect() as conn:
        result = await conn.execute(sa.text(f"EXPLAIN (ANALYZE, BUFFERS, VERBOSE) {sql}"))
        return "\n".join(row[0] for row in result)


# ─────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
async def db_with_rbac_tables(
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
            ObjectPermissionRow,
            AssociationScopesEntitiesRow,
        ],
    ):
        yield database_connection


@pytest.fixture
def db_source(db_with_rbac_tables: ExtendedAsyncSAEngine) -> PermissionDBSource:
    return PermissionDBSource(db_with_rbac_tables)


# ─────────────────────────────────────────────────────────────────────
# Wall-time benchmarks
# ─────────────────────────────────────────────────────────────────────


class TestEffectivePermissionsWallTime:
    """Wall-clock comparison: legacy vs direct-scope-walk effective resolver."""

    @pytest.mark.parametrize(
        ("label", "K", "num_parents"),
        _SCENARIOS,
        ids=[s[0] for s in _SCENARIOS],
    )
    async def test_effective_permissions_walltime(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        label: str,
        K: int,
        num_parents: int,
    ) -> None:
        seed = await _seed(db_with_rbac_tables, K=K, num_parents=num_parents)
        input_ = EffectivePermissionsInput(
            user_id=seed.user_id,
            target_element_type=RBACElementType.VFOLDER,
            target_entity_ids=seed.vfolder_ids,
        )

        async def call_legacy() -> None:
            await db_source.resolve_effective_permissions(input_)

        async def call_new() -> None:
            await db_source.resolve_effective_permissions_via_direct_scope_walk(input_)

        legacy_p50, legacy_p95 = await _measure(call_legacy)
        new_p50, new_p95 = await _measure(call_new)
        speedup = legacy_p50 / new_p50 if new_p50 > 0 else float("inf")

        print(
            f"\n[effective] {label:<32} | "
            f"legacy p50={legacy_p50:8.2f}ms p95={legacy_p95:8.2f}ms | "
            f"new p50={new_p50:8.2f}ms p95={new_p95:8.2f}ms | "
            f"speedup={speedup:5.2f}x"
        )


class TestBulkCheckWallTime:
    """Wall-clock comparison: legacy ``_check_permissions_via_scope_chain`` vs the refactored bulk path."""

    @pytest.mark.parametrize(
        ("label", "K", "num_parents"),
        _SCENARIOS,
        ids=[s[0] for s in _SCENARIOS],
    )
    async def test_bulk_check_walltime(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        label: str,
        K: int,
        num_parents: int,
    ) -> None:
        seed = await _seed(db_with_rbac_tables, K=K, num_parents=num_parents)
        legacy_params = _ScopeChainQueryParams(
            user_id=seed.user_id,
            target_element_type=RBACElementType.VFOLDER,
            entity_ids=seed.vfolder_ids,
            operation=OperationType.READ,
        )
        new_input = BulkPermissionCheckInput(
            user_id=seed.user_id,
            target_element_type=RBACElementType.VFOLDER,
            target_entity_ids=seed.vfolder_ids,
            operation=OperationType.READ,
        )

        async def call_legacy() -> dict[str, bool]:
            granted = await db_source._check_permissions_via_scope_chain(legacy_params)
            return {eid: eid in granted for eid in seed.vfolder_ids}

        async def call_new() -> dict[str, bool]:
            return await db_source.check_bulk_permission_with_scope_chain(new_input)

        legacy_p50, legacy_p95 = await _measure(call_legacy)
        new_p50, new_p95 = await _measure(call_new)
        speedup = legacy_p50 / new_p50 if new_p50 > 0 else float("inf")

        print(
            f"\n[bulk]      {label:<32} | "
            f"legacy p50={legacy_p50:8.2f}ms p95={legacy_p95:8.2f}ms | "
            f"new p50={new_p50:8.2f}ms p95={new_p95:8.2f}ms | "
            f"speedup={speedup:5.2f}x"
        )


# ─────────────────────────────────────────────────────────────────────
# Plan inspection
# ─────────────────────────────────────────────────────────────────────


_EXPLAIN_SCENARIOS: list[tuple[str, int, int]] = [
    ("high_fanin K=1000", 1000, 1),
    ("low_fanin K=1000 parents=K", 1000, 1000),
]


class TestExplainPlans:
    """Print full PostgreSQL EXPLAIN (ANALYZE, BUFFERS, VERBOSE) plans for both paths.

    Watch the recursive ``CTE Scan`` ``actual rows`` count — it should
    drop from ``~K * D`` (legacy) to ``~unique_direct_scopes * D``
    (new) in the high fan-in case, and stay roughly equal in the low
    fan-in case where every entity already has a unique parent.
    """

    @pytest.mark.parametrize(
        ("label", "K", "num_parents"),
        _EXPLAIN_SCENARIOS,
        ids=[s[0] for s in _EXPLAIN_SCENARIOS],
    )
    async def test_explain_effective_permissions(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        label: str,
        K: int,
        num_parents: int,
    ) -> None:
        seed = await _seed(db_with_rbac_tables, K=K, num_parents=num_parents)

        legacy_stmt = _legacy_effective_select(
            user_id=seed.user_id,
            target_entity_type=EntityType.VFOLDER,
            target_scope_type=ScopeType.VFOLDER,
            permission_entity_type=EntityType.VFOLDER,
            entity_ids=seed.vfolder_ids,
        )
        new_stmt = _new_effective_select(
            user_id=seed.user_id,
            target_entity_type=EntityType.VFOLDER,
            target_scope_type=ScopeType.VFOLDER,
            permission_entity_type=EntityType.VFOLDER,
            entity_ids=seed.vfolder_ids,
        )

        legacy_plan = await _explain(db_with_rbac_tables, legacy_stmt)
        new_plan = await _explain(db_with_rbac_tables, new_stmt)

        print(f"\n══════ EXPLAIN: legacy effective | {label} ══════\n{legacy_plan}")
        print(f"\n══════ EXPLAIN: new effective    | {label} ══════\n{new_plan}")
