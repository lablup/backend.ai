"""Tests for Fair Share bulk upsert operations using BulkUpserter."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from decimal import Decimal

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BulkUpserter
from ai.backend.manager.repositories.fair_share import FairShareRepository
from ai.backend.manager.repositories.fair_share.upserters import (
    DomainFairShareBulkWeightUpserterSpec,
    ProjectFairShareBulkWeightUpserterSpec,
    UserFairShareBulkWeightUpserterSpec,
)
from ai.backend.testutils.db import with_tables


@dataclass
class DomainFairShareTestContext:
    """Context for domain fair share tests."""

    scaling_group: str
    domain_names: list[str]
    existing_weights: dict[str, Decimal]  # domain_name -> existing weight (empty if none)


@dataclass
class ProjectFairShareTestContext:
    """Context for project fair share tests."""

    scaling_group: str
    domain_name: str
    project_ids: list[uuid.UUID]
    existing_weights: dict[uuid.UUID, Decimal]


@dataclass
class UserFairShareTestContext:
    """Context for user fair share tests."""

    scaling_group: str
    domain_name: str
    project_id: uuid.UUID
    user_uuids: list[uuid.UUID]
    existing_weights: dict[uuid.UUID, Decimal]


class TestBulkUpsertDomainFairShare:
    """Tests for bulk upsert domain fair share operations."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                DomainFairShareRow,
                ProjectFairShareRow,
                UserFairShareRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def fair_share_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> FairShareRepository:
        return FairShareRepository(db=db_with_cleanup)

    @pytest.fixture
    async def context_all_new_domains(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainFairShareTestContext:
        """Scenario: All domains are new (no existing fair share records)."""
        sg_name = f"test-sg-{uuid.uuid4().hex[:8]}"
        domain_names = [f"test-domain-{i}-{uuid.uuid4().hex[:8]}" for i in range(3)]

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ScalingGroupRow(
                name=sg_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(sg)

            for name in domain_names:
                domain = DomainRow(
                    name=name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
                db_sess.add(domain)
            await db_sess.commit()

        return DomainFairShareTestContext(
            scaling_group=sg_name,
            domain_names=domain_names,
            existing_weights={},  # No existing records
        )

    @pytest.fixture
    async def context_all_existing_domains(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainFairShareTestContext:
        """Scenario: All domains already have fair share records."""
        sg_name = f"test-sg-{uuid.uuid4().hex[:8]}"
        domain_names = [f"test-domain-{i}-{uuid.uuid4().hex[:8]}" for i in range(3)]
        existing_weights = {name: Decimal("1.0") for name in domain_names}

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ScalingGroupRow(
                name=sg_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(sg)

            for name in domain_names:
                domain = DomainRow(
                    name=name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
                db_sess.add(domain)
            await db_sess.flush()

            # Pre-create fair share records
            for name, weight in existing_weights.items():
                row = DomainFairShareRow(
                    resource_group=sg_name,
                    domain_name=name,
                    weight=weight,
                )
                db_sess.add(row)
            await db_sess.commit()

        return DomainFairShareTestContext(
            scaling_group=sg_name,
            domain_names=domain_names,
            existing_weights=existing_weights,
        )

    @pytest.fixture
    async def context_mixed_domains(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainFairShareTestContext:
        """Scenario: Mix of new and existing domains."""
        sg_name = f"test-sg-{uuid.uuid4().hex[:8]}"
        domain_names = [f"test-domain-{i}-{uuid.uuid4().hex[:8]}" for i in range(3)]
        # Only first domain has existing record
        existing_weights = {domain_names[0]: Decimal("1.0")}

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ScalingGroupRow(
                name=sg_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(sg)

            for name in domain_names:
                domain = DomainRow(
                    name=name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
                db_sess.add(domain)
            await db_sess.flush()

            # Pre-create only first domain's fair share record
            row = DomainFairShareRow(
                resource_group=sg_name,
                domain_name=domain_names[0],
                weight=Decimal("1.0"),
            )
            db_sess.add(row)
            await db_sess.commit()

        return DomainFairShareTestContext(
            scaling_group=sg_name,
            domain_names=domain_names,
            existing_weights=existing_weights,
        )

    @pytest.mark.asyncio
    async def test_bulk_upsert_all_new(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fair_share_repository: FairShareRepository,
        context_all_new_domains: DomainFairShareTestContext,
    ) -> None:
        """Test bulk upsert when all domains are new (insert case)."""
        ctx = context_all_new_domains
        specs = [
            DomainFairShareBulkWeightUpserterSpec(
                resource_group=ctx.scaling_group,
                domain_name=domain,
                weight=Decimal(f"{i + 1}.0"),
            )
            for i, domain in enumerate(ctx.domain_names)
        ]
        bulk_upserter: BulkUpserter[DomainFairShareRow] = BulkUpserter(specs=specs)

        result = await fair_share_repository.bulk_upsert_domain_fair_share(bulk_upserter)

        assert result.upserted_count == 3

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            rows = await db_sess.execute(
                sa.select(DomainFairShareRow).where(
                    DomainFairShareRow.resource_group == ctx.scaling_group
                )
            )
            fair_shares = {row.domain_name: row.weight for row in rows.scalars()}

        for i, domain in enumerate(ctx.domain_names):
            assert fair_shares[domain] == Decimal(f"{i + 1}.0")

    @pytest.mark.asyncio
    async def test_bulk_upsert_all_existing(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fair_share_repository: FairShareRepository,
        context_all_existing_domains: DomainFairShareTestContext,
    ) -> None:
        """Test bulk upsert when all domains exist (update case)."""
        ctx = context_all_existing_domains
        specs = [
            DomainFairShareBulkWeightUpserterSpec(
                resource_group=ctx.scaling_group,
                domain_name=domain,
                weight=Decimal(f"{i + 10}.0"),
            )
            for i, domain in enumerate(ctx.domain_names)
        ]
        bulk_upserter: BulkUpserter[DomainFairShareRow] = BulkUpserter(specs=specs)

        result = await fair_share_repository.bulk_upsert_domain_fair_share(bulk_upserter)

        assert result.upserted_count == 3

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            rows = await db_sess.execute(
                sa.select(DomainFairShareRow).where(
                    DomainFairShareRow.resource_group == ctx.scaling_group
                )
            )
            fair_shares = {row.domain_name: row.weight for row in rows.scalars()}

        for i, domain in enumerate(ctx.domain_names):
            assert fair_shares[domain] == Decimal(f"{i + 10}.0")

    @pytest.mark.asyncio
    async def test_bulk_upsert_mixed(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fair_share_repository: FairShareRepository,
        context_mixed_domains: DomainFairShareTestContext,
    ) -> None:
        """Test bulk upsert with mixed new and existing domains."""
        ctx = context_mixed_domains
        specs = [
            DomainFairShareBulkWeightUpserterSpec(
                resource_group=ctx.scaling_group,
                domain_name=domain,
                weight=Decimal("5.0"),
            )
            for domain in ctx.domain_names
        ]
        bulk_upserter: BulkUpserter[DomainFairShareRow] = BulkUpserter(specs=specs)

        result = await fair_share_repository.bulk_upsert_domain_fair_share(bulk_upserter)

        assert result.upserted_count == 3

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            rows = await db_sess.execute(
                sa.select(DomainFairShareRow).where(
                    DomainFairShareRow.resource_group == ctx.scaling_group
                )
            )
            fair_shares = list(rows.scalars())

        assert len(fair_shares) == 3
        for fs in fair_shares:
            assert fs.weight == Decimal("5.0")

    @pytest.mark.asyncio
    async def test_bulk_upsert_empty_specs(
        self,
        fair_share_repository: FairShareRepository,
    ) -> None:
        """Test bulk upsert with empty specs list."""
        specs: list[DomainFairShareBulkWeightUpserterSpec] = []
        bulk_upserter: BulkUpserter[DomainFairShareRow] = BulkUpserter(specs=specs)

        result = await fair_share_repository.bulk_upsert_domain_fair_share(bulk_upserter)

        assert result.upserted_count == 0


class TestBulkUpsertProjectFairShare:
    """Tests for bulk upsert project fair share operations."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                DomainFairShareRow,
                ProjectFairShareRow,
                UserFairShareRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def fair_share_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> FairShareRepository:
        return FairShareRepository(db=db_with_cleanup)

    @pytest.fixture
    async def context_all_new_projects(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ProjectFairShareTestContext:
        """Scenario: All projects are new (no existing fair share records)."""
        sg_name = f"test-sg-{uuid.uuid4().hex[:8]}"
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        project_ids = [uuid.uuid4() for _ in range(3)]

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ScalingGroupRow(
                name=sg_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(sg)

            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)

            policy_name = f"test-project-policy-{uuid.uuid4().hex[:8]}"
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(policy)
            await db_sess.flush()

            for pid in project_ids:
                group = GroupRow(
                    id=pid,
                    name=f"test-project-{pid.hex[:8]}",
                    domain_name=domain_name,
                    description="Test project",
                    resource_policy=policy_name,
                )
                db_sess.add(group)
            await db_sess.commit()

        return ProjectFairShareTestContext(
            scaling_group=sg_name,
            domain_name=domain_name,
            project_ids=project_ids,
            existing_weights={},
        )

    @pytest.fixture
    async def context_all_existing_projects(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ProjectFairShareTestContext:
        """Scenario: All projects already have fair share records."""
        sg_name = f"test-sg-{uuid.uuid4().hex[:8]}"
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        project_ids = [uuid.uuid4() for _ in range(3)]
        existing_weights = {pid: Decimal("1.0") for pid in project_ids}

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ScalingGroupRow(
                name=sg_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(sg)

            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)

            policy_name = f"test-project-policy-{uuid.uuid4().hex[:8]}"
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(policy)
            await db_sess.flush()

            for pid in project_ids:
                group = GroupRow(
                    id=pid,
                    name=f"test-project-{pid.hex[:8]}",
                    domain_name=domain_name,
                    description="Test project",
                    resource_policy=policy_name,
                )
                db_sess.add(group)
            await db_sess.flush()

            # Pre-create fair share records
            for pid, weight in existing_weights.items():
                row = ProjectFairShareRow(
                    resource_group=sg_name,
                    project_id=pid,
                    domain_name=domain_name,
                    weight=weight,
                )
                db_sess.add(row)
            await db_sess.commit()

        return ProjectFairShareTestContext(
            scaling_group=sg_name,
            domain_name=domain_name,
            project_ids=project_ids,
            existing_weights=existing_weights,
        )

    @pytest.mark.asyncio
    async def test_bulk_upsert_all_new(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fair_share_repository: FairShareRepository,
        context_all_new_projects: ProjectFairShareTestContext,
    ) -> None:
        """Test bulk upsert when all projects are new (insert case)."""
        ctx = context_all_new_projects
        specs = [
            ProjectFairShareBulkWeightUpserterSpec(
                resource_group=ctx.scaling_group,
                project_id=pid,
                domain_name=ctx.domain_name,
                weight=Decimal(f"{i + 1}.5"),
            )
            for i, pid in enumerate(ctx.project_ids)
        ]
        bulk_upserter: BulkUpserter[ProjectFairShareRow] = BulkUpserter(specs=specs)

        result = await fair_share_repository.bulk_upsert_project_fair_share(bulk_upserter)

        assert result.upserted_count == 3

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            rows = await db_sess.execute(
                sa.select(ProjectFairShareRow).where(
                    ProjectFairShareRow.resource_group == ctx.scaling_group
                )
            )
            fair_shares = {row.project_id: row.weight for row in rows.scalars()}

        for i, pid in enumerate(ctx.project_ids):
            assert fair_shares[pid] == Decimal(f"{i + 1}.5")

    @pytest.mark.asyncio
    async def test_bulk_upsert_all_existing(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fair_share_repository: FairShareRepository,
        context_all_existing_projects: ProjectFairShareTestContext,
    ) -> None:
        """Test bulk upsert when all projects exist (update case)."""
        ctx = context_all_existing_projects
        specs = [
            ProjectFairShareBulkWeightUpserterSpec(
                resource_group=ctx.scaling_group,
                project_id=pid,
                domain_name=ctx.domain_name,
                weight=Decimal(f"{i + 20}.0"),
            )
            for i, pid in enumerate(ctx.project_ids)
        ]
        bulk_upserter: BulkUpserter[ProjectFairShareRow] = BulkUpserter(specs=specs)

        result = await fair_share_repository.bulk_upsert_project_fair_share(bulk_upserter)

        assert result.upserted_count == 3

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            rows = await db_sess.execute(
                sa.select(ProjectFairShareRow).where(
                    ProjectFairShareRow.resource_group == ctx.scaling_group
                )
            )
            fair_shares = {row.project_id: row.weight for row in rows.scalars()}

        for i, pid in enumerate(ctx.project_ids):
            assert fair_shares[pid] == Decimal(f"{i + 20}.0")


class TestBulkUpsertUserFairShare:
    """Tests for bulk upsert user fair share operations."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                DomainFairShareRow,
                ProjectFairShareRow,
                UserFairShareRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def fair_share_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> FairShareRepository:
        return FairShareRepository(db=db_with_cleanup)

    @pytest.fixture
    async def context_all_new_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> UserFairShareTestContext:
        """Scenario: All users are new (no existing fair share records)."""
        sg_name = f"test-sg-{uuid.uuid4().hex[:8]}"
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        project_id = uuid.uuid4()
        user_uuids = [uuid.uuid4() for _ in range(3)]

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ScalingGroupRow(
                name=sg_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(sg)

            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)

            project_policy_name = f"test-project-policy-{uuid.uuid4().hex[:8]}"
            project_policy = ProjectResourcePolicyRow(
                name=project_policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(project_policy)

            user_policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
            user_policy = UserResourcePolicyRow(
                name=user_policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(user_policy)
            await db_sess.flush()

            group = GroupRow(
                id=project_id,
                name=f"test-project-{project_id.hex[:8]}",
                domain_name=domain_name,
                description="Test project",
                resource_policy=project_policy_name,
            )
            db_sess.add(group)

            password_info = PasswordInfo(
                password="dummy",
                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                rounds=600_000,
                salt_size=32,
            )

            for uid in user_uuids:
                user = UserRow(
                    uuid=uid,
                    username=f"testuser-{uid.hex[:8]}",
                    email=f"test-{uid.hex[:8]}@example.com",
                    password=password_info,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=user_policy_name,
                )
                db_sess.add(user)
            await db_sess.commit()

        return UserFairShareTestContext(
            scaling_group=sg_name,
            domain_name=domain_name,
            project_id=project_id,
            user_uuids=user_uuids,
            existing_weights={},
        )

    @pytest.fixture
    async def context_all_existing_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> UserFairShareTestContext:
        """Scenario: All users already have fair share records."""
        sg_name = f"test-sg-{uuid.uuid4().hex[:8]}"
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        project_id = uuid.uuid4()
        user_uuids = [uuid.uuid4() for _ in range(3)]
        existing_weights = {uid: Decimal("1.0") for uid in user_uuids}

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ScalingGroupRow(
                name=sg_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(sg)

            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)

            project_policy_name = f"test-project-policy-{uuid.uuid4().hex[:8]}"
            project_policy = ProjectResourcePolicyRow(
                name=project_policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(project_policy)

            user_policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
            user_policy = UserResourcePolicyRow(
                name=user_policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(user_policy)
            await db_sess.flush()

            group = GroupRow(
                id=project_id,
                name=f"test-project-{project_id.hex[:8]}",
                domain_name=domain_name,
                description="Test project",
                resource_policy=project_policy_name,
            )
            db_sess.add(group)

            password_info = PasswordInfo(
                password="dummy",
                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                rounds=600_000,
                salt_size=32,
            )

            for uid in user_uuids:
                user = UserRow(
                    uuid=uid,
                    username=f"testuser-{uid.hex[:8]}",
                    email=f"test-{uid.hex[:8]}@example.com",
                    password=password_info,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=user_policy_name,
                )
                db_sess.add(user)
            await db_sess.flush()

            # Pre-create fair share records
            for uid, weight in existing_weights.items():
                row = UserFairShareRow(
                    resource_group=sg_name,
                    user_uuid=uid,
                    project_id=project_id,
                    domain_name=domain_name,
                    weight=weight,
                )
                db_sess.add(row)
            await db_sess.commit()

        return UserFairShareTestContext(
            scaling_group=sg_name,
            domain_name=domain_name,
            project_id=project_id,
            user_uuids=user_uuids,
            existing_weights=existing_weights,
        )

    @pytest.fixture
    async def context_null_weight_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> UserFairShareTestContext:
        """Scenario: Users to be set with null weight (use default)."""
        sg_name = f"test-sg-{uuid.uuid4().hex[:8]}"
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        project_id = uuid.uuid4()
        user_uuids = [uuid.uuid4() for _ in range(3)]

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ScalingGroupRow(
                name=sg_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(sg)

            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)

            project_policy_name = f"test-project-policy-{uuid.uuid4().hex[:8]}"
            project_policy = ProjectResourcePolicyRow(
                name=project_policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(project_policy)

            user_policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
            user_policy = UserResourcePolicyRow(
                name=user_policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(user_policy)
            await db_sess.flush()

            group = GroupRow(
                id=project_id,
                name=f"test-project-{project_id.hex[:8]}",
                domain_name=domain_name,
                description="Test project",
                resource_policy=project_policy_name,
            )
            db_sess.add(group)

            password_info = PasswordInfo(
                password="dummy",
                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                rounds=600_000,
                salt_size=32,
            )

            for uid in user_uuids:
                user = UserRow(
                    uuid=uid,
                    username=f"testuser-{uid.hex[:8]}",
                    email=f"test-{uid.hex[:8]}@example.com",
                    password=password_info,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=user_policy_name,
                )
                db_sess.add(user)
            await db_sess.commit()

        return UserFairShareTestContext(
            scaling_group=sg_name,
            domain_name=domain_name,
            project_id=project_id,
            user_uuids=user_uuids,
            existing_weights={},
        )

    @pytest.mark.asyncio
    async def test_bulk_upsert_all_new(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fair_share_repository: FairShareRepository,
        context_all_new_users: UserFairShareTestContext,
    ) -> None:
        """Test bulk upsert when all users are new (insert case)."""
        ctx = context_all_new_users
        specs = [
            UserFairShareBulkWeightUpserterSpec(
                resource_group=ctx.scaling_group,
                user_uuid=uid,
                project_id=ctx.project_id,
                domain_name=ctx.domain_name,
                weight=Decimal(f"{i + 1}.25"),
            )
            for i, uid in enumerate(ctx.user_uuids)
        ]
        bulk_upserter: BulkUpserter[UserFairShareRow] = BulkUpserter(specs=specs)

        result = await fair_share_repository.bulk_upsert_user_fair_share(bulk_upserter)

        assert result.upserted_count == 3

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            rows = await db_sess.execute(
                sa.select(UserFairShareRow).where(
                    UserFairShareRow.resource_group == ctx.scaling_group
                )
            )
            fair_shares = {row.user_uuid: row.weight for row in rows.scalars()}

        for i, uid in enumerate(ctx.user_uuids):
            assert fair_shares[uid] == Decimal(f"{i + 1}.25")

    @pytest.mark.asyncio
    async def test_bulk_upsert_all_existing(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fair_share_repository: FairShareRepository,
        context_all_existing_users: UserFairShareTestContext,
    ) -> None:
        """Test bulk upsert when all users exist (update case)."""
        ctx = context_all_existing_users
        specs = [
            UserFairShareBulkWeightUpserterSpec(
                resource_group=ctx.scaling_group,
                user_uuid=uid,
                project_id=ctx.project_id,
                domain_name=ctx.domain_name,
                weight=Decimal(f"{i + 30}.0"),
            )
            for i, uid in enumerate(ctx.user_uuids)
        ]
        bulk_upserter: BulkUpserter[UserFairShareRow] = BulkUpserter(specs=specs)

        result = await fair_share_repository.bulk_upsert_user_fair_share(bulk_upserter)

        assert result.upserted_count == 3

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            rows = await db_sess.execute(
                sa.select(UserFairShareRow).where(
                    UserFairShareRow.resource_group == ctx.scaling_group
                )
            )
            fair_shares = {row.user_uuid: row.weight for row in rows.scalars()}

        for i, uid in enumerate(ctx.user_uuids):
            assert fair_shares[uid] == Decimal(f"{i + 30}.0")

    @pytest.mark.asyncio
    async def test_bulk_upsert_with_null_weight(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fair_share_repository: FairShareRepository,
        context_null_weight_users: UserFairShareTestContext,
    ) -> None:
        """Test bulk upsert with None weight (uses resource group default)."""
        ctx = context_null_weight_users
        specs = [
            UserFairShareBulkWeightUpserterSpec(
                resource_group=ctx.scaling_group,
                user_uuid=uid,
                project_id=ctx.project_id,
                domain_name=ctx.domain_name,
                weight=None,
            )
            for uid in ctx.user_uuids
        ]
        bulk_upserter: BulkUpserter[UserFairShareRow] = BulkUpserter(specs=specs)

        result = await fair_share_repository.bulk_upsert_user_fair_share(bulk_upserter)

        assert result.upserted_count == 3

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            rows = await db_sess.execute(
                sa.select(UserFairShareRow).where(
                    UserFairShareRow.resource_group == ctx.scaling_group
                )
            )
            fair_shares = list(rows.scalars())

        assert len(fair_shares) == 3
        for fs in fair_shares:
            assert fs.weight is None
