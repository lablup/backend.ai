"""
Tests for entity-based fair share search with Scope pattern.

Tests that domains/projects/users are returned even without fair share records.
When no record exists, `details` field should be None.

Scope pattern:
- Scope provides required filters (resource_group) converted to query conditions
- Scope defines existence_checks for validation (e.g., ScalingGroupNotFound)
- Valid scope with no matching data returns empty result (not error)
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForProjectRow,
    ScalingGroupOpts,
    ScalingGroupRow,
)
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, Creator
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.fair_share import (
    DomainFairShareCreatorSpec,
    FairShareRepository,
    ProjectFairShareCreatorSpec,
    UserFairShareCreatorSpec,
)
from ai.backend.testutils.db import with_tables


class TestSearchDomainFairSharesEntityBased:
    """Test domain fair share search with Scope pattern."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                ScalingGroupForDomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ScalingGroupForProjectRow,
                AssocGroupUserRow,
                DomainFairShareRow,
                ProjectFairShareRow,
                UserFairShareRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def scaling_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        sg_name = f"test-sg-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    name=sg_name,
                    description="Test scaling group",
                    is_active=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                    wsproxy_addr=None,
                )
            )
            await db_sess.commit()
        return sg_name

    @pytest.fixture
    async def fair_share_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> FairShareRepository:
        return FairShareRepository(db_with_cleanup)

    @pytest.fixture
    async def domain_with_record(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        fair_share_repository: FairShareRepository,
    ) -> str:
        """Create a domain with fair share record."""
        domain_name = f"domain-with-record-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="Domain with fair share record",
                    is_active=True,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            await db_sess.flush()
            db_sess.add(ScalingGroupForDomainRow(scaling_group=scaling_group, domain=domain_name))
            await db_sess.commit()

        await fair_share_repository.create_domain_fair_share(
            Creator(
                spec=DomainFairShareCreatorSpec(
                    resource_group=scaling_group,
                    domain_name=domain_name,
                )
            )
        )
        return domain_name

    @pytest.fixture
    async def domain_without_record(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
    ) -> str:
        """Create a domain without fair share record."""
        domain_name = f"domain-no-record-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="Domain without fair share record",
                    is_active=True,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            await db_sess.flush()
            db_sess.add(ScalingGroupForDomainRow(scaling_group=scaling_group, domain=domain_name))
            await db_sess.commit()
        return domain_name

    @pytest.fixture
    async def scaling_group_without_domains(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create a scaling group with no associated domains."""
        sg_name = f"empty-sg-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    name=sg_name,
                    description="Scaling group without domains",
                    is_active=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                    wsproxy_addr=None,
                )
            )
            await db_sess.commit()
        return sg_name

    @dataclass
    class TwoScalingGroupsFixture:
        rg1: str
        rg2: str
        domain_in_rg1: str
        domain_in_rg2: str

    @pytest.fixture
    async def two_scaling_groups_with_domains(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> TwoScalingGroupsFixture:
        """Create two scaling groups, each with one domain."""
        rg1 = f"rg1-{uuid.uuid4().hex[:8]}"
        rg2 = f"rg2-{uuid.uuid4().hex[:8]}"
        domain1 = f"domain1-{uuid.uuid4().hex[:8]}"
        domain2 = f"domain2-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            for sg_name in [rg1, rg2]:
                db_sess.add(
                    ScalingGroupRow(
                        name=sg_name,
                        description=f"Test {sg_name}",
                        is_active=True,
                        driver="static",
                        driver_opts={},
                        scheduler="fifo",
                        scheduler_opts=ScalingGroupOpts(),
                        wsproxy_addr=None,
                    )
                )
            for domain_name in [domain1, domain2]:
                db_sess.add(
                    DomainRow(
                        name=domain_name,
                        description=f"Test {domain_name}",
                        is_active=True,
                        total_resource_slots={},
                        allowed_vfolder_hosts={},
                        allowed_docker_registries=[],
                    )
                )
            await db_sess.flush()
            db_sess.add(ScalingGroupForDomainRow(scaling_group=rg1, domain=domain1))
            db_sess.add(ScalingGroupForDomainRow(scaling_group=rg2, domain=domain2))
            await db_sess.commit()

        return self.TwoScalingGroupsFixture(
            rg1=rg1, rg2=rg2, domain_in_rg1=domain1, domain_in_rg2=domain2
        )

    @pytest.fixture
    async def five_domains_two_with_records(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        fair_share_repository: FairShareRepository,
    ) -> list[str]:
        """Create 5 domains, only first 2 have fair share records."""
        domain_names = [f"domain-{i}-{uuid.uuid4().hex[:8]}" for i in range(5)]

        async with db_with_cleanup.begin_session() as db_sess:
            for name in domain_names:
                db_sess.add(
                    DomainRow(
                        name=name,
                        description=f"Test {name}",
                        is_active=True,
                        total_resource_slots={},
                        allowed_vfolder_hosts={},
                        allowed_docker_registries=[],
                    )
                )
                await db_sess.flush()
                db_sess.add(ScalingGroupForDomainRow(scaling_group=scaling_group, domain=name))
            await db_sess.commit()

        for name in domain_names[:2]:
            await fair_share_repository.create_domain_fair_share(
                Creator(
                    spec=DomainFairShareCreatorSpec(
                        resource_group=scaling_group,
                        domain_name=name,
                    )
                )
            )
        return domain_names

    # ==================== Scope Validation Tests ====================

    @pytest.mark.asyncio
    async def test_raises_error_for_nonexistent_resource_group(
        self,
        fair_share_repository: FairShareRepository,
    ) -> None:
        """Non-existent resource_group in scope should raise ScalingGroupNotFound."""
        from ai.backend.manager.repositories.fair_share.types import DomainFairShareSearchScope

        scope = DomainFairShareSearchScope(resource_group="nonexistent-rg")
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        with pytest.raises(ScalingGroupNotFound):
            await fair_share_repository.search_domain_fair_share_entities(scope, querier)

    # ==================== Empty Result Tests ====================

    @pytest.mark.asyncio
    async def test_returns_empty_for_resource_group_without_domains(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group_without_domains: str,
    ) -> None:
        """Valid resource_group with no domains should return empty result (not error)."""
        from ai.backend.manager.repositories.fair_share.types import DomainFairShareSearchScope

        scope = DomainFairShareSearchScope(resource_group=scaling_group_without_domains)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        result = await fair_share_repository.search_domain_fair_share_entities(scope, querier)

        assert result.total_count == 0
        assert len(result.items) == 0

    # ==================== Success Cases ====================

    @pytest.mark.asyncio
    async def test_returns_domain_with_record(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        domain_with_record: str,
    ) -> None:
        """Domain with fair share record should have details populated."""
        from ai.backend.manager.repositories.fair_share.types import DomainFairShareSearchScope

        scope = DomainFairShareSearchScope(resource_group=scaling_group)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        result = await fair_share_repository.search_domain_fair_share_entities(scope, querier)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].domain_name == domain_with_record
        assert result.items[0].resource_group == scaling_group
        assert result.items[0].details is not None

    @pytest.mark.asyncio
    async def test_returns_domain_without_record(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        domain_without_record: str,
    ) -> None:
        """Domain without fair share record should have details as None."""
        from ai.backend.manager.repositories.fair_share.types import DomainFairShareSearchScope

        scope = DomainFairShareSearchScope(resource_group=scaling_group)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        result = await fair_share_repository.search_domain_fair_share_entities(scope, querier)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].domain_name == domain_without_record
        assert result.items[0].resource_group == scaling_group
        assert result.items[0].details is None

    @pytest.mark.asyncio
    async def test_mixed_domains_with_and_without_records(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        domain_with_record: str,
        domain_without_record: str,
    ) -> None:
        """Search should return both domains with and without records."""
        from ai.backend.manager.repositories.fair_share.types import DomainFairShareSearchScope

        scope = DomainFairShareSearchScope(resource_group=scaling_group)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        result = await fair_share_repository.search_domain_fair_share_entities(scope, querier)

        assert result.total_count == 2
        assert len(result.items) == 2

        result_domains = {d.domain_name: d for d in result.items}
        assert domain_with_record in result_domains
        assert domain_without_record in result_domains
        assert result_domains[domain_with_record].details is not None
        assert result_domains[domain_without_record].details is None

    @pytest.mark.asyncio
    async def test_filters_by_resource_group_in_scope(
        self,
        fair_share_repository: FairShareRepository,
        two_scaling_groups_with_domains: TwoScalingGroupsFixture,
    ) -> None:
        """Search should only return domains associated with resource_group in scope."""
        from ai.backend.manager.repositories.fair_share.types import DomainFairShareSearchScope

        fixture = two_scaling_groups_with_domains
        scope = DomainFairShareSearchScope(resource_group=fixture.rg1)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        result = await fair_share_repository.search_domain_fair_share_entities(scope, querier)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].domain_name == fixture.domain_in_rg1

    @pytest.mark.asyncio
    async def test_pagination_includes_all_entities(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        five_domains_two_with_records: list[str],
    ) -> None:
        """Pagination total_count should include entities without records."""
        from ai.backend.manager.repositories.fair_share.types import DomainFairShareSearchScope

        scope = DomainFairShareSearchScope(resource_group=scaling_group)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[],
            orders=[],
        )

        result = await fair_share_repository.search_domain_fair_share_entities(scope, querier)

        assert result.total_count == 5
        assert len(result.items) == 2
        assert result.has_next_page is True


class TestSearchProjectFairSharesEntityBased:
    """Test project fair share search with Scope pattern."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                ScalingGroupForDomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ScalingGroupForProjectRow,
                AssocGroupUserRow,
                DomainFairShareRow,
                ProjectFairShareRow,
                UserFairShareRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def scaling_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        sg_name = f"test-sg-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    name=sg_name,
                    description="Test scaling group",
                    is_active=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                    wsproxy_addr=None,
                )
            )
            await db_sess.commit()
        return sg_name

    @pytest.fixture
    async def domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
    ) -> str:
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            await db_sess.flush()
            db_sess.add(ScalingGroupForDomainRow(scaling_group=scaling_group, domain=domain_name))
            await db_sess.commit()
        return domain_name

    @pytest.fixture
    async def fair_share_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> FairShareRepository:
        return FairShareRepository(db_with_cleanup)

    @pytest.fixture
    async def project_with_record(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        domain_name: str,
        fair_share_repository: FairShareRepository,
    ) -> uuid.UUID:
        """Create a project with fair share record."""
        project_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()

            db_sess.add(
                GroupRow(
                    id=project_id,
                    name=f"test-project-{project_id.hex[:8]}",
                    domain_name=domain_name,
                    description="Test project with record",
                    resource_policy=policy_name,
                )
            )
            await db_sess.flush()

            db_sess.add(ScalingGroupForProjectRow(scaling_group=scaling_group, group=project_id))
            await db_sess.commit()

        await fair_share_repository.create_project_fair_share(
            Creator(
                spec=ProjectFairShareCreatorSpec(
                    resource_group=scaling_group,
                    project_id=project_id,
                    domain_name=domain_name,
                )
            )
        )
        return project_id

    @pytest.fixture
    async def project_without_record(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        domain_name: str,
    ) -> uuid.UUID:
        """Create a project without fair share record."""
        project_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()

            db_sess.add(
                GroupRow(
                    id=project_id,
                    name=f"test-project-{project_id.hex[:8]}",
                    domain_name=domain_name,
                    description="Test project without record",
                    resource_policy=policy_name,
                )
            )
            await db_sess.flush()

            db_sess.add(ScalingGroupForProjectRow(scaling_group=scaling_group, group=project_id))
            await db_sess.commit()
        return project_id

    # ==================== Scope Validation Tests ====================

    @pytest.mark.asyncio
    async def test_raises_error_for_nonexistent_resource_group(
        self,
        fair_share_repository: FairShareRepository,
    ) -> None:
        """Non-existent resource_group in scope should raise ScalingGroupNotFound."""
        from ai.backend.manager.repositories.fair_share.types import ProjectFairShareSearchScope

        scope = ProjectFairShareSearchScope(resource_group="nonexistent-rg")
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        with pytest.raises(ScalingGroupNotFound):
            await fair_share_repository.search_project_fair_share_entities(scope, querier)

    # ==================== Success Cases ====================

    @pytest.mark.asyncio
    async def test_returns_project_with_record(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        project_with_record: uuid.UUID,
    ) -> None:
        """Project with fair share record should have details populated."""
        from ai.backend.manager.repositories.fair_share.types import ProjectFairShareSearchScope

        scope = ProjectFairShareSearchScope(resource_group=scaling_group)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        result = await fair_share_repository.search_project_fair_share_entities(scope, querier)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].project_id == project_with_record
        assert result.items[0].resource_group == scaling_group
        assert result.items[0].details is not None

    @pytest.mark.asyncio
    async def test_returns_project_without_record(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        project_without_record: uuid.UUID,
    ) -> None:
        """Project without fair share record should have details as None."""
        from ai.backend.manager.repositories.fair_share.types import ProjectFairShareSearchScope

        scope = ProjectFairShareSearchScope(resource_group=scaling_group)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        result = await fair_share_repository.search_project_fair_share_entities(scope, querier)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].project_id == project_without_record
        assert result.items[0].resource_group == scaling_group
        assert result.items[0].details is None

    @pytest.mark.asyncio
    async def test_mixed_projects_with_and_without_records(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        project_with_record: uuid.UUID,
        project_without_record: uuid.UUID,
    ) -> None:
        """Search should return both projects with and without records."""
        from ai.backend.manager.repositories.fair_share.types import ProjectFairShareSearchScope

        scope = ProjectFairShareSearchScope(resource_group=scaling_group)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        result = await fair_share_repository.search_project_fair_share_entities(scope, querier)

        assert result.total_count == 2
        assert len(result.items) == 2

        result_projects = {p.project_id: p for p in result.items}
        assert project_with_record in result_projects
        assert project_without_record in result_projects
        assert result_projects[project_with_record].details is not None
        assert result_projects[project_without_record].details is None


class TestSearchUserFairSharesEntityBased:
    """Test user fair share search with Scope pattern."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                ScalingGroupForDomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ScalingGroupForProjectRow,
                AssocGroupUserRow,
                DomainFairShareRow,
                ProjectFairShareRow,
                UserFairShareRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def scaling_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        sg_name = f"test-sg-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    name=sg_name,
                    description="Test scaling group",
                    is_active=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                    wsproxy_addr=None,
                )
            )
            await db_sess.commit()
        return sg_name

    @pytest.fixture
    async def domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
    ) -> str:
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            await db_sess.flush()
            db_sess.add(ScalingGroupForDomainRow(scaling_group=scaling_group, domain=domain_name))
            await db_sess.commit()
        return domain_name

    @pytest.fixture
    async def project_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        scaling_group: str,
    ) -> uuid.UUID:
        project_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()

            db_sess.add(
                GroupRow(
                    id=project_id,
                    name=f"test-project-{project_id.hex[:8]}",
                    domain_name=domain_name,
                    description="Test project",
                    resource_policy=policy_name,
                )
            )
            await db_sess.flush()

            db_sess.add(ScalingGroupForProjectRow(scaling_group=scaling_group, group=project_id))
            await db_sess.commit()
        return project_id

    @pytest.fixture
    async def fair_share_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> FairShareRepository:
        return FairShareRepository(db_with_cleanup)

    async def _create_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        project_id: uuid.UUID,
    ) -> uuid.UUID:
        """Helper to create a user associated with domain and project."""
        user_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            user_policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
            db_sess.add(
                UserResourcePolicyRow(
                    name=user_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )

            kp_policy_name = f"test-kp-policy-{uuid.uuid4().hex[:8]}"
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name=kp_policy_name,
                    total_resource_slots={},
                    max_session_lifetime=0,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=5,
                    max_containers_per_session=1,
                    idle_timeout=3600,
                )
            )
            await db_sess.flush()

            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"test-user-{user_uuid.hex[:8]}",
                    email=f"test-{user_uuid.hex[:8]}@test.com",
                    password=PasswordInfo(
                        password="test_password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=100_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    full_name="Test User",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    resource_policy=user_policy_name,
                )
            )
            await db_sess.flush()

            db_sess.add(
                KeyPairRow(
                    user=user_uuid,
                    access_key=f"AKIATEST{uuid.uuid4().hex[:12].upper()}",
                    secret_key="test-secret-key",
                    is_active=True,
                    resource_policy=kp_policy_name,
                )
            )
            await db_sess.flush()

            db_sess.add(AssocGroupUserRow(group_id=project_id, user_id=user_uuid))
            await db_sess.commit()
        return user_uuid

    @pytest.fixture
    async def user_with_record(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        domain_name: str,
        project_id: uuid.UUID,
        fair_share_repository: FairShareRepository,
    ) -> uuid.UUID:
        """Create a user with fair share record."""
        user_uuid = await self._create_user(db_with_cleanup, domain_name, project_id)

        await fair_share_repository.create_user_fair_share(
            Creator(
                spec=UserFairShareCreatorSpec(
                    resource_group=scaling_group,
                    user_uuid=user_uuid,
                    project_id=project_id,
                    domain_name=domain_name,
                )
            )
        )
        return user_uuid

    @pytest.fixture
    async def user_without_record(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        project_id: uuid.UUID,
    ) -> uuid.UUID:
        """Create a user without fair share record."""
        return await self._create_user(db_with_cleanup, domain_name, project_id)

    # ==================== Scope Validation Tests ====================

    @pytest.mark.asyncio
    async def test_raises_error_for_nonexistent_resource_group(
        self,
        fair_share_repository: FairShareRepository,
    ) -> None:
        """Non-existent resource_group in scope should raise ScalingGroupNotFound."""
        from ai.backend.manager.repositories.fair_share.types import UserFairShareSearchScope

        scope = UserFairShareSearchScope(resource_group="nonexistent-rg")
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        with pytest.raises(ScalingGroupNotFound):
            await fair_share_repository.search_user_fair_share_entities(scope, querier)

    # ==================== Success Cases ====================

    @pytest.mark.asyncio
    async def test_returns_user_with_record(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        project_id: uuid.UUID,
        user_with_record: uuid.UUID,
    ) -> None:
        """User with fair share record should have details populated."""
        from ai.backend.manager.repositories.fair_share.types import UserFairShareSearchScope

        scope = UserFairShareSearchScope(resource_group=scaling_group)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        result = await fair_share_repository.search_user_fair_share_entities(scope, querier)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].user_uuid == user_with_record
        assert result.items[0].resource_group == scaling_group
        assert result.items[0].project_id == project_id
        assert result.items[0].details is not None

    @pytest.mark.asyncio
    async def test_returns_user_without_record(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        project_id: uuid.UUID,
        user_without_record: uuid.UUID,
    ) -> None:
        """User without fair share record should have details as None."""
        from ai.backend.manager.repositories.fair_share.types import UserFairShareSearchScope

        scope = UserFairShareSearchScope(resource_group=scaling_group)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        result = await fair_share_repository.search_user_fair_share_entities(scope, querier)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].user_uuid == user_without_record
        assert result.items[0].resource_group == scaling_group
        assert result.items[0].project_id == project_id
        assert result.items[0].details is None

    @pytest.mark.asyncio
    async def test_mixed_users_with_and_without_records(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        project_id: uuid.UUID,
        user_with_record: uuid.UUID,
        user_without_record: uuid.UUID,
    ) -> None:
        """Search should return both users with and without records."""
        from ai.backend.manager.repositories.fair_share.types import UserFairShareSearchScope

        scope = UserFairShareSearchScope(resource_group=scaling_group)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        result = await fair_share_repository.search_user_fair_share_entities(scope, querier)

        assert result.total_count == 2
        assert len(result.items) == 2

        result_users = {u.user_uuid: u for u in result.items}
        assert user_with_record in result_users
        assert user_without_record in result_users
        assert result_users[user_with_record].details is not None
        assert result_users[user_without_record].details is None
