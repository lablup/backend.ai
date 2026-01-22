"""
Tests for FairShareRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.errors.fair_share import FairShareNotFoundError
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, Creator, Upserter
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.fair_share import (
    DomainFairShareConditions,
    DomainFairShareCreatorSpec,
    DomainFairShareOrders,
    DomainFairShareUpserterSpec,
    FairShareRepository,
    ProjectFairShareCreatorSpec,
    ProjectFairShareUpserterSpec,
    UserFairShareCreatorSpec,
    UserFairShareUpserterSpec,
)
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.testutils.db import with_tables


class TestFairShareRepository:
    """Test cases for FairShareRepository"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                # Base rows in FK dependency order (parents before children)
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AgentRow,
                ImageRow,
                SessionRow,
                KernelRow,
                ResourcePresetRow,
                # Fair Share rows (no FK constraints but need mapper registration)
                DomainFairShareRow,
                ProjectFairShareRow,
                UserFairShareRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_scaling_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test scaling group and return name"""
        sg_name = f"test-sg-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ScalingGroupRow(
                name=sg_name,
                description="Test scaling group for fair share",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
                wsproxy_addr=None,
            )
            db_sess.add(sg)
            await db_sess.commit()

        return sg_name

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test domain and return domain name"""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain for fair share",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.commit()

        return domain_name

    @pytest.fixture
    async def test_project_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
    ) -> uuid.UUID:
        """Create test project (group) and return its ID"""
        project_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            # Create project resource policy first
            policy_name = f"test-project-policy-{uuid.uuid4().hex[:8]}"
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(policy)
            await db_sess.flush()

            # Create project (group)
            group = GroupRow(
                id=project_id,
                name=f"test-project-{project_id.hex[:8]}",
                domain_name=test_domain_name,
                description="Test project for fair share",
                resource_policy=policy_name,
            )
            db_sess.add(group)
            await db_sess.commit()

        return project_id

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
    ) -> uuid.UUID:
        """Create test user and return user UUID"""
        user_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            # Create user resource policy first
            policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

            password_info = PasswordInfo(
                password="dummy",
                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                rounds=600_000,
                salt_size=32,
            )

            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=policy_name,
            )
            db_sess.add(user)
            await db_sess.commit()

        return user_uuid

    @pytest.fixture
    def fair_share_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> FairShareRepository:
        """Create FairShareRepository instance with database"""
        return FairShareRepository(db=db_with_cleanup)

    # ==================== Domain Fair Share Tests ====================

    @pytest.mark.asyncio
    async def test_create_domain_fair_share(
        self,
        fair_share_repository: FairShareRepository,
        test_scaling_group: str,
        test_domain_name: str,
    ) -> None:
        """Test creating domain fair share"""
        creator = Creator(
            spec=DomainFairShareCreatorSpec(
                resource_group=test_scaling_group,
                domain_name=test_domain_name,
                weight=Decimal("2.0"),
            )
        )

        result = await fair_share_repository.create_domain_fair_share(creator)

        assert result.resource_group == test_scaling_group
        assert result.domain_name == test_domain_name
        assert result.spec.weight == Decimal("2.0")
        assert result.calculation_snapshot.fair_share_factor == Decimal(
            "1.0"
        )  # Default initial value
        assert result.calculation_snapshot.total_decayed_usage == ResourceSlot()

    @pytest.mark.asyncio
    async def test_upsert_domain_fair_share_insert(
        self,
        fair_share_repository: FairShareRepository,
        test_scaling_group: str,
        test_domain_name: str,
    ) -> None:
        """Test upsert domain fair share - insert case"""
        upserter = Upserter(
            spec=DomainFairShareUpserterSpec(
                resource_group=test_scaling_group,
                domain_name=test_domain_name,
                weight=TriState.update(Decimal("1.5")),
                # Must provide at least one update value for ON CONFLICT UPDATE
                fair_share_factor=OptionalState.update(Decimal("1.0")),
            )
        )

        result = await fair_share_repository.upsert_domain_fair_share(upserter)

        assert result.resource_group == test_scaling_group
        assert result.domain_name == test_domain_name
        assert result.spec.weight == Decimal("1.5")
        assert result.calculation_snapshot.fair_share_factor == Decimal("1.0")

    @pytest.mark.asyncio
    async def test_upsert_domain_fair_share_update(
        self,
        fair_share_repository: FairShareRepository,
        test_scaling_group: str,
        test_domain_name: str,
    ) -> None:
        """Test upsert domain fair share - update case"""
        # First insert
        upserter1 = Upserter(
            spec=DomainFairShareUpserterSpec(
                resource_group=test_scaling_group,
                domain_name=test_domain_name,
                weight=TriState.update(Decimal("1.0")),
                # Must provide at least one update value for ON CONFLICT UPDATE
                fair_share_factor=OptionalState.update(Decimal("1.0")),
            )
        )
        await fair_share_repository.upsert_domain_fair_share(upserter1)

        # Second upsert - should update calculated fields only
        upserter2 = Upserter(
            spec=DomainFairShareUpserterSpec(
                resource_group=test_scaling_group,
                domain_name=test_domain_name,
                fair_share_factor=OptionalState.update(Decimal("0.75")),
                normalized_usage=OptionalState.update(Decimal("0.5")),
            )
        )
        result = await fair_share_repository.upsert_domain_fair_share(upserter2)

        # weight is a spec value, only set on INSERT, not updated on conflict
        assert result.spec.weight == Decimal("1.0")
        # Calculated values should be updated
        assert result.calculation_snapshot.fair_share_factor == Decimal("0.75")
        assert result.calculation_snapshot.normalized_usage == Decimal("0.5")

    @pytest.mark.asyncio
    async def test_get_domain_fair_share(
        self,
        fair_share_repository: FairShareRepository,
        test_scaling_group: str,
        test_domain_name: str,
    ) -> None:
        """Test getting domain fair share by scaling group and domain"""
        # Create first
        creator = Creator(
            spec=DomainFairShareCreatorSpec(
                resource_group=test_scaling_group,
                domain_name=test_domain_name,
                weight=Decimal("1.5"),
            )
        )
        await fair_share_repository.create_domain_fair_share(creator)

        # Get
        result = await fair_share_repository.get_domain_fair_share(
            resource_group=test_scaling_group,
            domain_name=test_domain_name,
        )

        assert result.resource_group == test_scaling_group
        assert result.domain_name == test_domain_name
        assert result.spec.weight == Decimal("1.5")

    @pytest.mark.asyncio
    async def test_get_domain_fair_share_not_found(
        self,
        fair_share_repository: FairShareRepository,
    ) -> None:
        """Test getting non-existent domain fair share raises FairShareNotFoundError"""
        with pytest.raises(FairShareNotFoundError):
            await fair_share_repository.get_domain_fair_share(
                resource_group="non-existent-sg",
                domain_name="non-existent-domain",
            )

    @pytest.mark.asyncio
    async def test_search_domain_fair_shares(
        self,
        fair_share_repository: FairShareRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group: str,
    ) -> None:
        """Test searching domain fair shares with BatchQuerier"""
        # Create multiple domain fair shares
        domain_names = [f"domain-{i}-{uuid.uuid4().hex[:8]}" for i in range(3)]

        async with db_with_cleanup.begin_session() as db_sess:
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

        for name in domain_names:
            creator = Creator(
                spec=DomainFairShareCreatorSpec(
                    resource_group=test_scaling_group,
                    domain_name=name,
                )
            )
            await fair_share_repository.create_domain_fair_share(creator)

        # Search with BatchQuerier
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[DomainFairShareConditions.by_resource_group(test_scaling_group)],
            orders=[DomainFairShareOrders.by_domain_name()],
        )
        result = await fair_share_repository.search_domain_fair_shares(querier)

        assert result.total_count == 3
        assert len(result.items) == 3
        result_domains = {r.domain_name for r in result.items}
        assert result_domains == set(domain_names)

    # ==================== Project Fair Share Tests ====================

    @pytest.mark.asyncio
    async def test_create_project_fair_share(
        self,
        fair_share_repository: FairShareRepository,
        test_scaling_group: str,
        test_domain_name: str,
        test_project_id: uuid.UUID,
    ) -> None:
        """Test creating project fair share"""
        creator = Creator(
            spec=ProjectFairShareCreatorSpec(
                resource_group=test_scaling_group,
                project_id=test_project_id,
                domain_name=test_domain_name,
                weight=Decimal("1.5"),
            )
        )

        result = await fair_share_repository.create_project_fair_share(creator)

        assert result.resource_group == test_scaling_group
        assert result.project_id == test_project_id
        assert result.domain_name == test_domain_name
        assert result.spec.weight == Decimal("1.5")

    @pytest.mark.asyncio
    async def test_upsert_project_fair_share(
        self,
        fair_share_repository: FairShareRepository,
        test_scaling_group: str,
        test_domain_name: str,
        test_project_id: uuid.UUID,
    ) -> None:
        """Test upsert project fair share"""
        upserter = Upserter(
            spec=ProjectFairShareUpserterSpec(
                resource_group=test_scaling_group,
                project_id=test_project_id,
                domain_name=test_domain_name,
                weight=TriState.update(Decimal("2.0")),
                fair_share_factor=OptionalState.update(Decimal("0.8")),
            )
        )

        result = await fair_share_repository.upsert_project_fair_share(upserter)

        assert result.project_id == test_project_id
        assert result.spec.weight == Decimal("2.0")
        assert result.calculation_snapshot.fair_share_factor == Decimal("0.8")

    @pytest.mark.asyncio
    async def test_get_project_fair_share(
        self,
        fair_share_repository: FairShareRepository,
        test_scaling_group: str,
        test_domain_name: str,
        test_project_id: uuid.UUID,
    ) -> None:
        """Test getting project fair share"""
        creator = Creator(
            spec=ProjectFairShareCreatorSpec(
                resource_group=test_scaling_group,
                project_id=test_project_id,
                domain_name=test_domain_name,
            )
        )
        await fair_share_repository.create_project_fair_share(creator)

        result = await fair_share_repository.get_project_fair_share(
            resource_group=test_scaling_group,
            project_id=test_project_id,
        )

        assert result.project_id == test_project_id

    # ==================== User Fair Share Tests ====================

    @pytest.mark.asyncio
    async def test_create_user_fair_share(
        self,
        fair_share_repository: FairShareRepository,
        test_scaling_group: str,
        test_domain_name: str,
        test_project_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> None:
        """Test creating user fair share"""
        creator = Creator(
            spec=UserFairShareCreatorSpec(
                resource_group=test_scaling_group,
                user_uuid=test_user_uuid,
                project_id=test_project_id,
                domain_name=test_domain_name,
                weight=Decimal("1.2"),
            )
        )

        result = await fair_share_repository.create_user_fair_share(creator)

        assert result.resource_group == test_scaling_group
        assert result.user_uuid == test_user_uuid
        assert result.project_id == test_project_id
        assert result.spec.weight == Decimal("1.2")

    @pytest.mark.asyncio
    async def test_upsert_user_fair_share(
        self,
        fair_share_repository: FairShareRepository,
        test_scaling_group: str,
        test_domain_name: str,
        test_project_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> None:
        """Test upsert user fair share"""
        upserter = Upserter(
            spec=UserFairShareUpserterSpec(
                resource_group=test_scaling_group,
                user_uuid=test_user_uuid,
                project_id=test_project_id,
                domain_name=test_domain_name,
                weight=TriState.update(Decimal("1.5")),
                fair_share_factor=OptionalState.update(Decimal("0.9")),
            )
        )

        result = await fair_share_repository.upsert_user_fair_share(upserter)

        assert result.user_uuid == test_user_uuid
        assert result.spec.weight == Decimal("1.5")
        assert result.calculation_snapshot.fair_share_factor == Decimal("0.9")

    @pytest.mark.asyncio
    async def test_get_user_fair_share(
        self,
        fair_share_repository: FairShareRepository,
        test_scaling_group: str,
        test_domain_name: str,
        test_project_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> None:
        """Test getting user fair share"""
        creator = Creator(
            spec=UserFairShareCreatorSpec(
                resource_group=test_scaling_group,
                user_uuid=test_user_uuid,
                project_id=test_project_id,
                domain_name=test_domain_name,
            )
        )
        await fair_share_repository.create_user_fair_share(creator)

        result = await fair_share_repository.get_user_fair_share(
            resource_group=test_scaling_group,
            project_id=test_project_id,
            user_uuid=test_user_uuid,
        )

        assert result.user_uuid == test_user_uuid
        assert result.project_id == test_project_id
