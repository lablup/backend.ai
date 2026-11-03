"""`mgr seed apply` grants the example domain admins the role provisioning created."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.errors.permission import RoleNotFound
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWriteItemResult
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.domain_admin.seed import DomainAdminSeed
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind


@pytest.fixture
def plan(domain_admin_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([domain_admin_seed_dir])


@pytest.fixture
async def applied(repository: SeedRepository, plan: SeedPlan) -> None:
    """The admin files applied, with the domain, user and role they refer to."""
    await SeedApplier(repository).apply(plan, overwrite=False)


@pytest.fixture
def seed(plan: SeedPlan) -> DomainAdminSeed:
    [seed] = _seeds(plan)
    return seed


def _seeds(plan: SeedPlan) -> list[DomainAdminSeed]:
    return [
        item
        for batch in plan.batches
        for item in batch.items()
        if isinstance(item, DomainAdminSeed)
    ]


async def _roles(db: ExtendedAsyncSAEngine, user_id: UserID) -> set[uuid.UUID]:
    async with db.begin_readonly() as conn:
        rows = await conn.scalars(
            sa.select(UserRoleRow.role_id).where(UserRoleRow.user_id == user_id)
        )
        return set(rows.all())


class TestApply:
    async def test_the_domain_admin_holds_the_role(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        seed: DomainAdminSeed,
        domain_admin_role_id: str,
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.DOMAIN_ADMIN].succeeded == [seed.key()]
        assert results[SeedKind.DOMAIN_ADMIN].failed == []
        assert uuid.UUID(domain_admin_role_id) in await _roles(db, seed.user_id)

    @pytest.mark.parametrize("overwrite", [False, True], ids=["insert", "overwrite"])
    async def test_applying_again_skips_and_leaves_one_grant(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        applied: None,
        seed: DomainAdminSeed,
        overwrite: bool,
    ) -> None:
        roles = await _roles(db, seed.user_id)

        results = await SeedApplier(repository).apply(plan, overwrite=overwrite)

        assert results[SeedKind.DOMAIN_ADMIN].succeeded == []
        assert len(results[SeedKind.DOMAIN_ADMIN].skipped) == 1
        assert await _roles(db, seed.user_id) == roles

    async def test_an_item_naming_a_domain_without_the_role_fails_alone(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        seed: DomainAdminSeed,
        research_domain_id: str,
        admin_user_id: str,
    ) -> None:
        refused = seed.model_copy(update={"domain_id": DomainID(uuid.UUID(research_domain_id))})
        other = seed.model_copy(update={"user_id": UserID(uuid.UUID(admin_user_id))})

        results = await repository.partial_write([refused.write(), other.write()], overwrite=False)

        assert isinstance(results[0].error, RoleNotFound)
        assert results[1] == SeedWriteItemResult(written=True)
