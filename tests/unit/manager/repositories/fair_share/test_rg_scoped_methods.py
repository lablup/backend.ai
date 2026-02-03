"""
Tests for RG-scoped fair share methods.

Tests get_rg_scoped_* and search_rg_scoped_* methods that query
from connection tables (ScalingGroupForDomain, ScalingGroupForProject).

Key behaviors tested:
- get_rg_scoped_*: Returns data if record exists, None if connected but no record,
  raises error if not connected
- search_rg_scoped_*: Returns all entities connected to RG with optional details
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from decimal import Decimal

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.errors.fair_share import (
    DomainNotConnectedToResourceGroupError,
    ProjectNotConnectedToResourceGroupError,
    UserNotConnectedToResourceGroupError,
)
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
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.fair_share import FairShareRepository
from ai.backend.manager.repositories.fair_share.types import (
    DomainFairShareSearchScope,
    ProjectFairShareSearchScope,
    UserFairShareSearchScope,
)
from ai.backend.testutils.db import with_tables

# ==================== Domain Fair Share Tests ====================


class TestGetRGScopedDomainFairShare:
    """Test get_rg_scoped_domain_fair_share method."""

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
                DomainFairShareRow,
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
    async def domain_connected_with_record(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
    ) -> str:
        """Domain connected to RG with fair share record."""
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
            db_sess.add(
                DomainFairShareRow(
                    resource_group=scaling_group,
                    domain_name=domain_name,
                    weight=Decimal("1.5"),
                    fair_share_factor=Decimal("1.0"),
                    total_decayed_usage=ResourceSlot(),
                    normalized_usage=Decimal("0"),
                    resource_weights=ResourceSlot(),
                )
            )
            await db_sess.commit()
        return domain_name

    @pytest.fixture
    async def domain_connected_without_record(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
    ) -> str:
        """Domain connected to RG without fair share record."""
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
    async def domain_not_connected(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Domain not connected to any RG."""
        domain_name = f"domain-not-connected-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="Domain not connected",
                    is_active=True,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            await db_sess.commit()
        return domain_name

    async def test_returns_data_when_record_exists(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        domain_connected_with_record: str,
    ) -> None:
        """Domain connected with fair share record returns DomainFairShareData."""
        result = await fair_share_repository.get_rg_scoped_domain_fair_share(
            resource_group=scaling_group,
            domain_name=domain_connected_with_record,
        )

        assert result is not None
        assert result.domain_name == domain_connected_with_record
        assert result.resource_group == scaling_group
        assert result.spec.weight == Decimal("1.5")

    async def test_returns_none_when_no_record(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        domain_connected_without_record: str,
    ) -> None:
        """Domain connected without fair share record returns None."""
        result = await fair_share_repository.get_rg_scoped_domain_fair_share(
            resource_group=scaling_group,
            domain_name=domain_connected_without_record,
        )

        assert result is None

    async def test_raises_error_when_not_connected(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        domain_not_connected: str,
    ) -> None:
        """Domain not connected to RG raises DomainNotConnectedToResourceGroupError."""
        with pytest.raises(DomainNotConnectedToResourceGroupError):
            await fair_share_repository.get_rg_scoped_domain_fair_share(
                resource_group=scaling_group,
                domain_name=domain_not_connected,
            )


class TestSearchRGScopedDomainFairShares:
    """Test search_rg_scoped_domain_fair_shares method."""

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
                DomainFairShareRow,
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

    @dataclass
    class DomainSearchContext:
        scaling_group: str
        domains_with_record: list[str]
        domains_without_record: list[str]

    @pytest.fixture
    async def context_all_with_records(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
    ) -> DomainSearchContext:
        """All domains connected with fair share records."""
        domains = [f"domain-all-{i}-{uuid.uuid4().hex[:8]}" for i in range(3)]
        async with db_with_cleanup.begin_session() as db_sess:
            for domain_name in domains:
                db_sess.add(
                    DomainRow(
                        name=domain_name,
                        description="Domain with record",
                        is_active=True,
                        total_resource_slots={},
                        allowed_vfolder_hosts={},
                        allowed_docker_registries=[],
                    )
                )
            await db_sess.flush()
            for domain_name in domains:
                db_sess.add(
                    ScalingGroupForDomainRow(scaling_group=scaling_group, domain=domain_name)
                )
                db_sess.add(
                    DomainFairShareRow(
                        resource_group=scaling_group,
                        domain_name=domain_name,
                        weight=Decimal("1.0"),
                        fair_share_factor=Decimal("1.0"),
                        total_decayed_usage=ResourceSlot(),
                        normalized_usage=Decimal("0"),
                        resource_weights=ResourceSlot(),
                    )
                )
            await db_sess.commit()
        return self.DomainSearchContext(
            scaling_group=scaling_group,
            domains_with_record=domains,
            domains_without_record=[],
        )

    @pytest.fixture
    async def context_mixed_records(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
    ) -> DomainSearchContext:
        """Some domains with records, some without."""
        domains_with = [f"domain-with-{uuid.uuid4().hex[:8]}"]
        domains_without = [f"domain-without-{i}-{uuid.uuid4().hex[:8]}" for i in range(2)]
        all_domains = domains_with + domains_without

        async with db_with_cleanup.begin_session() as db_sess:
            for domain_name in all_domains:
                db_sess.add(
                    DomainRow(
                        name=domain_name,
                        description="Domain",
                        is_active=True,
                        total_resource_slots={},
                        allowed_vfolder_hosts={},
                        allowed_docker_registries=[],
                    )
                )
            await db_sess.flush()
            for domain_name in all_domains:
                db_sess.add(
                    ScalingGroupForDomainRow(scaling_group=scaling_group, domain=domain_name)
                )
            for domain_name in domains_with:
                db_sess.add(
                    DomainFairShareRow(
                        resource_group=scaling_group,
                        domain_name=domain_name,
                        weight=Decimal("1.0"),
                        fair_share_factor=Decimal("1.0"),
                        total_decayed_usage=ResourceSlot(),
                        normalized_usage=Decimal("0"),
                        resource_weights=ResourceSlot(),
                    )
                )
            await db_sess.commit()
        return self.DomainSearchContext(
            scaling_group=scaling_group,
            domains_with_record=domains_with,
            domains_without_record=domains_without,
        )

    @pytest.fixture
    async def context_all_without_records(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
    ) -> DomainSearchContext:
        """All domains connected without fair share records."""
        domains = [f"domain-none-{i}-{uuid.uuid4().hex[:8]}" for i in range(3)]
        async with db_with_cleanup.begin_session() as db_sess:
            for domain_name in domains:
                db_sess.add(
                    DomainRow(
                        name=domain_name,
                        description="Domain without record",
                        is_active=True,
                        total_resource_slots={},
                        allowed_vfolder_hosts={},
                        allowed_docker_registries=[],
                    )
                )
            await db_sess.flush()
            for domain_name in domains:
                db_sess.add(
                    ScalingGroupForDomainRow(scaling_group=scaling_group, domain=domain_name)
                )
            await db_sess.commit()
        return self.DomainSearchContext(
            scaling_group=scaling_group,
            domains_with_record=[],
            domains_without_record=domains,
        )

    @pytest.fixture
    async def context_no_domains(
        self,
        scaling_group: str,
    ) -> DomainSearchContext:
        """No domains connected to RG."""
        return self.DomainSearchContext(
            scaling_group=scaling_group,
            domains_with_record=[],
            domains_without_record=[],
        )

    async def test_all_domains_with_records(
        self,
        fair_share_repository: FairShareRepository,
        context_all_with_records: DomainSearchContext,
    ) -> None:
        """All domains have fair share records - all details should be present."""
        scope = DomainFairShareSearchScope(resource_group=context_all_with_records.scaling_group)
        querier = BatchQuerier(pagination=OffsetPagination(limit=100, offset=0))

        result = await fair_share_repository.search_rg_scoped_domain_fair_shares(scope, querier)

        assert result.total_count == 3
        assert len(result.items) == 3
        for item in result.items:
            assert item.details is not None
            assert item.domain_name in context_all_with_records.domains_with_record

    async def test_mixed_records(
        self,
        fair_share_repository: FairShareRepository,
        context_mixed_records: DomainSearchContext,
    ) -> None:
        """Some domains with records, some without."""
        scope = DomainFairShareSearchScope(resource_group=context_mixed_records.scaling_group)
        querier = BatchQuerier(pagination=OffsetPagination(limit=100, offset=0))

        result = await fair_share_repository.search_rg_scoped_domain_fair_shares(scope, querier)

        assert result.total_count == 3
        assert len(result.items) == 3

        with_details = [item for item in result.items if item.details is not None]
        without_details = [item for item in result.items if item.details is None]

        assert len(with_details) == 1
        assert len(without_details) == 2
        assert with_details[0].domain_name in context_mixed_records.domains_with_record
        for item in without_details:
            assert item.domain_name in context_mixed_records.domains_without_record

    async def test_all_domains_without_records(
        self,
        fair_share_repository: FairShareRepository,
        context_all_without_records: DomainSearchContext,
    ) -> None:
        """All domains without fair share records - all details should be None."""
        scope = DomainFairShareSearchScope(resource_group=context_all_without_records.scaling_group)
        querier = BatchQuerier(pagination=OffsetPagination(limit=100, offset=0))

        result = await fair_share_repository.search_rg_scoped_domain_fair_shares(scope, querier)

        assert result.total_count == 3
        assert len(result.items) == 3
        for item in result.items:
            assert item.details is None
            assert item.domain_name in context_all_without_records.domains_without_record

    async def test_no_domains_connected(
        self,
        fair_share_repository: FairShareRepository,
        context_no_domains: DomainSearchContext,
    ) -> None:
        """No domains connected to RG - returns empty result."""
        scope = DomainFairShareSearchScope(resource_group=context_no_domains.scaling_group)
        querier = BatchQuerier(pagination=OffsetPagination(limit=100, offset=0))

        result = await fair_share_repository.search_rg_scoped_domain_fair_shares(scope, querier)

        assert result.total_count == 0
        assert len(result.items) == 0


# ==================== Project Fair Share Tests ====================


class TestGetRGScopedProjectFairShare:
    """Test get_rg_scoped_project_fair_share method."""

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
                ProjectResourcePolicyRow,
                GroupRow,
                ScalingGroupForProjectRow,
                ProjectFairShareRow,
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

    async def _create_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        project_name: str,
    ) -> uuid.UUID:
        """Helper to create a project."""
        project_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=f"prp-{project_id.hex[:8]}",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()
            db_sess.add(
                GroupRow(
                    id=project_id,
                    name=project_name,
                    description="Test project",
                    is_active=True,
                    domain_name=domain_name,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    resource_policy=f"prp-{project_id.hex[:8]}",
                )
            )
            await db_sess.commit()
        return project_id

    @pytest.fixture
    async def project_connected_with_record(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        domain_name: str,
    ) -> uuid.UUID:
        """Project connected to RG with fair share record."""
        project_id = await self._create_project(
            db_with_cleanup, domain_name, f"project-with-{uuid.uuid4().hex[:8]}"
        )
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(ScalingGroupForProjectRow(scaling_group=scaling_group, group=project_id))
            db_sess.add(
                ProjectFairShareRow(
                    resource_group=scaling_group,
                    project_id=project_id,
                    domain_name=domain_name,
                    weight=Decimal("2.0"),
                    fair_share_factor=Decimal("1.0"),
                    total_decayed_usage=ResourceSlot(),
                    normalized_usage=Decimal("0"),
                    resource_weights=ResourceSlot(),
                )
            )
            await db_sess.commit()
        return project_id

    @pytest.fixture
    async def project_connected_without_record(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        domain_name: str,
    ) -> uuid.UUID:
        """Project connected to RG without fair share record."""
        project_id = await self._create_project(
            db_with_cleanup, domain_name, f"project-no-{uuid.uuid4().hex[:8]}"
        )
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(ScalingGroupForProjectRow(scaling_group=scaling_group, group=project_id))
            await db_sess.commit()
        return project_id

    @pytest.fixture
    async def project_not_connected(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
    ) -> uuid.UUID:
        """Project not connected to any RG."""
        return await self._create_project(
            db_with_cleanup, domain_name, f"project-disconn-{uuid.uuid4().hex[:8]}"
        )

    async def test_returns_data_when_record_exists(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        project_connected_with_record: uuid.UUID,
    ) -> None:
        """Project connected with fair share record returns ProjectFairShareData."""
        result = await fair_share_repository.get_rg_scoped_project_fair_share(
            resource_group=scaling_group,
            project_id=project_connected_with_record,
        )

        assert result is not None
        assert result.project_id == project_connected_with_record
        assert result.resource_group == scaling_group
        assert result.spec.weight == Decimal("2.0")

    async def test_returns_none_when_no_record(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        project_connected_without_record: uuid.UUID,
    ) -> None:
        """Project connected without fair share record returns None."""
        result = await fair_share_repository.get_rg_scoped_project_fair_share(
            resource_group=scaling_group,
            project_id=project_connected_without_record,
        )

        assert result is None

    async def test_raises_error_when_not_connected(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        project_not_connected: uuid.UUID,
    ) -> None:
        """Project not connected to RG raises ProjectNotConnectedToResourceGroupError."""
        with pytest.raises(ProjectNotConnectedToResourceGroupError):
            await fair_share_repository.get_rg_scoped_project_fair_share(
                resource_group=scaling_group,
                project_id=project_not_connected,
            )


class TestSearchRGScopedProjectFairShares:
    """Test search_rg_scoped_project_fair_shares method."""

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
                ProjectResourcePolicyRow,
                GroupRow,
                ScalingGroupForProjectRow,
                ProjectFairShareRow,
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

    async def _create_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        project_name: str,
    ) -> uuid.UUID:
        """Helper to create a project."""
        project_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=f"prp-{project_id.hex[:8]}",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()
            db_sess.add(
                GroupRow(
                    id=project_id,
                    name=project_name,
                    description="Test project",
                    is_active=True,
                    domain_name=domain_name,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    resource_policy=f"prp-{project_id.hex[:8]}",
                )
            )
            await db_sess.commit()
        return project_id

    @dataclass
    class ProjectSearchContext:
        scaling_group: str
        domain_name: str
        projects_with_record: list[uuid.UUID]
        projects_without_record: list[uuid.UUID]

    @pytest.fixture
    async def context_all_with_records(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        domain_name: str,
    ) -> ProjectSearchContext:
        """All projects connected with fair share records."""
        projects = []
        for i in range(3):
            project_id = await self._create_project(
                db_with_cleanup, domain_name, f"project-all-{i}-{uuid.uuid4().hex[:8]}"
            )
            projects.append(project_id)

        async with db_with_cleanup.begin_session() as db_sess:
            for project_id in projects:
                db_sess.add(
                    ScalingGroupForProjectRow(scaling_group=scaling_group, group=project_id)
                )
                db_sess.add(
                    ProjectFairShareRow(
                        resource_group=scaling_group,
                        project_id=project_id,
                        domain_name=domain_name,
                        weight=Decimal("1.0"),
                        fair_share_factor=Decimal("1.0"),
                        total_decayed_usage=ResourceSlot(),
                        normalized_usage=Decimal("0"),
                        resource_weights=ResourceSlot(),
                    )
                )
            await db_sess.commit()
        return self.ProjectSearchContext(
            scaling_group=scaling_group,
            domain_name=domain_name,
            projects_with_record=projects,
            projects_without_record=[],
        )

    @pytest.fixture
    async def context_mixed_records(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        domain_name: str,
    ) -> ProjectSearchContext:
        """Some projects with records, some without."""
        project_with = await self._create_project(
            db_with_cleanup, domain_name, f"project-with-{uuid.uuid4().hex[:8]}"
        )
        projects_without = []
        for i in range(2):
            project_id = await self._create_project(
                db_with_cleanup, domain_name, f"project-without-{i}-{uuid.uuid4().hex[:8]}"
            )
            projects_without.append(project_id)

        async with db_with_cleanup.begin_session() as db_sess:
            for project_id in [project_with, *projects_without]:
                db_sess.add(
                    ScalingGroupForProjectRow(scaling_group=scaling_group, group=project_id)
                )
            db_sess.add(
                ProjectFairShareRow(
                    resource_group=scaling_group,
                    project_id=project_with,
                    domain_name=domain_name,
                    weight=Decimal("1.0"),
                    fair_share_factor=Decimal("1.0"),
                    total_decayed_usage=ResourceSlot(),
                    normalized_usage=Decimal("0"),
                    resource_weights=ResourceSlot(),
                )
            )
            await db_sess.commit()
        return self.ProjectSearchContext(
            scaling_group=scaling_group,
            domain_name=domain_name,
            projects_with_record=[project_with],
            projects_without_record=projects_without,
        )

    @pytest.fixture
    async def context_all_without_records(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        domain_name: str,
    ) -> ProjectSearchContext:
        """All projects connected without fair share records."""
        projects = []
        for i in range(3):
            project_id = await self._create_project(
                db_with_cleanup, domain_name, f"project-none-{i}-{uuid.uuid4().hex[:8]}"
            )
            projects.append(project_id)

        async with db_with_cleanup.begin_session() as db_sess:
            for project_id in projects:
                db_sess.add(
                    ScalingGroupForProjectRow(scaling_group=scaling_group, group=project_id)
                )
            await db_sess.commit()
        return self.ProjectSearchContext(
            scaling_group=scaling_group,
            domain_name=domain_name,
            projects_with_record=[],
            projects_without_record=projects,
        )

    @pytest.fixture
    async def context_no_projects(
        self,
        scaling_group: str,
        domain_name: str,
    ) -> ProjectSearchContext:
        """No projects connected to RG."""
        return self.ProjectSearchContext(
            scaling_group=scaling_group,
            domain_name=domain_name,
            projects_with_record=[],
            projects_without_record=[],
        )

    async def test_all_projects_with_records(
        self,
        fair_share_repository: FairShareRepository,
        context_all_with_records: ProjectSearchContext,
    ) -> None:
        """All projects have fair share records - all details should be present."""
        scope = ProjectFairShareSearchScope(
            resource_group=context_all_with_records.scaling_group,
            domain_name=context_all_with_records.domain_name,
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=100, offset=0))

        result = await fair_share_repository.search_rg_scoped_project_fair_shares(scope, querier)

        assert result.total_count == 3
        assert len(result.items) == 3
        for item in result.items:
            assert item.details is not None
            assert item.project_id in context_all_with_records.projects_with_record

    async def test_mixed_records(
        self,
        fair_share_repository: FairShareRepository,
        context_mixed_records: ProjectSearchContext,
    ) -> None:
        """Some projects with records, some without."""
        scope = ProjectFairShareSearchScope(
            resource_group=context_mixed_records.scaling_group,
            domain_name=context_mixed_records.domain_name,
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=100, offset=0))

        result = await fair_share_repository.search_rg_scoped_project_fair_shares(scope, querier)

        assert result.total_count == 3
        assert len(result.items) == 3

        with_details = [item for item in result.items if item.details is not None]
        without_details = [item for item in result.items if item.details is None]

        assert len(with_details) == 1
        assert len(without_details) == 2
        assert with_details[0].project_id in context_mixed_records.projects_with_record
        for item in without_details:
            assert item.project_id in context_mixed_records.projects_without_record

    async def test_all_projects_without_records(
        self,
        fair_share_repository: FairShareRepository,
        context_all_without_records: ProjectSearchContext,
    ) -> None:
        """All projects without fair share records - all details should be None."""
        scope = ProjectFairShareSearchScope(
            resource_group=context_all_without_records.scaling_group,
            domain_name=context_all_without_records.domain_name,
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=100, offset=0))

        result = await fair_share_repository.search_rg_scoped_project_fair_shares(scope, querier)

        assert result.total_count == 3
        assert len(result.items) == 3
        for item in result.items:
            assert item.details is None
            assert item.project_id in context_all_without_records.projects_without_record

    async def test_no_projects_connected(
        self,
        fair_share_repository: FairShareRepository,
        context_no_projects: ProjectSearchContext,
    ) -> None:
        """No projects connected to RG - returns empty result."""
        scope = ProjectFairShareSearchScope(
            resource_group=context_no_projects.scaling_group,
            domain_name=context_no_projects.domain_name,
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=100, offset=0))

        result = await fair_share_repository.search_rg_scoped_project_fair_shares(scope, querier)

        assert result.total_count == 0
        assert len(result.items) == 0


# ==================== User Fair Share Tests ====================


class TestGetRGScopedUserFairShare:
    """Test get_rg_scoped_user_fair_share method."""

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
                UserRoleRow,
                UserRow,
                KeyPairResourcePolicyRow,
                KeyPairRow,
                GroupRow,
                ScalingGroupForProjectRow,
                AssocGroupUserRow,
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

    async def _create_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        project_name: str,
    ) -> uuid.UUID:
        """Helper to create a project."""
        project_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=f"prp-{project_id.hex[:8]}",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()
            db_sess.add(
                GroupRow(
                    id=project_id,
                    name=project_name,
                    description="Test project",
                    is_active=True,
                    domain_name=domain_name,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    resource_policy=f"prp-{project_id.hex[:8]}",
                )
            )
            await db_sess.commit()
        return project_id

    async def _create_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        project_id: uuid.UUID,
        user_email: str,
    ) -> uuid.UUID:
        """Helper to create a user and associate with project."""
        user_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name=f"urp-{user_uuid.hex[:8]}",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name=f"kprp-{user_uuid.hex[:8]}",
                    total_resource_slots={},
                    max_session_lifetime=0,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=5,
                    max_containers_per_session=1,
                )
            )
            await db_sess.flush()
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    email=user_email,
                    username=user_email.split("@")[0],
                    password=PasswordInfo(
                        password="test",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=100_000,
                        salt_size=16,
                    ),
                    need_password_change=False,
                    domain_name=domain_name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    status_info="",
                    resource_policy=f"urp-{user_uuid.hex[:8]}",
                    allowed_client_ip=None,
                    totp_key=None,
                    totp_key_last_used=None,
                    main_access_key=None,
                )
            )
            await db_sess.flush()
            db_sess.add(
                KeyPairRow(
                    access_key=f"AK{user_uuid.hex[:16]}",
                    user=user_uuid,
                    secret_key="SK" + user_uuid.hex,
                    is_active=True,
                    is_admin=False,
                    resource_policy=f"kprp-{user_uuid.hex[:8]}",
                )
            )
            db_sess.add(
                AssocGroupUserRow(
                    group_id=project_id,
                    user_id=user_uuid,
                )
            )
            await db_sess.commit()
        return user_uuid

    @dataclass
    class UserContext:
        user_uuid: uuid.UUID
        project_id: uuid.UUID
        domain_name: str

    @pytest.fixture
    async def user_connected_with_record(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        domain_name: str,
    ) -> UserContext:
        """User connected to RG (via project) with fair share record."""
        project_id = await self._create_project(
            db_with_cleanup, domain_name, f"proj-user-with-{uuid.uuid4().hex[:8]}"
        )
        user_uuid = await self._create_user(
            db_with_cleanup, domain_name, project_id, f"user-with-{uuid.uuid4().hex[:8]}@test.com"
        )

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(ScalingGroupForProjectRow(scaling_group=scaling_group, group=project_id))
            db_sess.add(
                UserFairShareRow(
                    resource_group=scaling_group,
                    user_uuid=user_uuid,
                    project_id=project_id,
                    domain_name=domain_name,
                    weight=Decimal("3.0"),
                    fair_share_factor=Decimal("1.0"),
                    total_decayed_usage=ResourceSlot(),
                    normalized_usage=Decimal("0"),
                    resource_weights=ResourceSlot(),
                )
            )
            await db_sess.commit()

        return self.UserContext(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name=domain_name,
        )

    @pytest.fixture
    async def user_connected_without_record(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        domain_name: str,
    ) -> UserContext:
        """User connected to RG (via project) without fair share record."""
        project_id = await self._create_project(
            db_with_cleanup, domain_name, f"proj-user-no-{uuid.uuid4().hex[:8]}"
        )
        user_uuid = await self._create_user(
            db_with_cleanup, domain_name, project_id, f"user-no-{uuid.uuid4().hex[:8]}@test.com"
        )

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(ScalingGroupForProjectRow(scaling_group=scaling_group, group=project_id))
            await db_sess.commit()

        return self.UserContext(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name=domain_name,
        )

    @pytest.fixture
    async def user_not_connected(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
    ) -> UserContext:
        """User not connected to any RG (project not connected)."""
        project_id = await self._create_project(
            db_with_cleanup, domain_name, f"proj-disconn-{uuid.uuid4().hex[:8]}"
        )
        user_uuid = await self._create_user(
            db_with_cleanup,
            domain_name,
            project_id,
            f"user-disconn-{uuid.uuid4().hex[:8]}@test.com",
        )

        return self.UserContext(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name=domain_name,
        )

    async def test_returns_data_when_record_exists(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        user_connected_with_record: UserContext,
    ) -> None:
        """User connected with fair share record returns UserFairShareData."""
        result = await fair_share_repository.get_rg_scoped_user_fair_share(
            resource_group=scaling_group,
            project_id=user_connected_with_record.project_id,
            user_uuid=user_connected_with_record.user_uuid,
        )

        assert result is not None
        assert result.user_uuid == user_connected_with_record.user_uuid
        assert result.project_id == user_connected_with_record.project_id
        assert result.resource_group == scaling_group
        assert result.spec.weight == Decimal("3.0")

    async def test_returns_none_when_no_record(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        user_connected_without_record: UserContext,
    ) -> None:
        """User connected without fair share record returns None."""
        result = await fair_share_repository.get_rg_scoped_user_fair_share(
            resource_group=scaling_group,
            project_id=user_connected_without_record.project_id,
            user_uuid=user_connected_without_record.user_uuid,
        )

        assert result is None

    async def test_raises_error_when_not_connected(
        self,
        fair_share_repository: FairShareRepository,
        scaling_group: str,
        user_not_connected: UserContext,
    ) -> None:
        """User not connected to RG raises UserNotConnectedToResourceGroupError."""
        with pytest.raises(UserNotConnectedToResourceGroupError):
            await fair_share_repository.get_rg_scoped_user_fair_share(
                resource_group=scaling_group,
                project_id=user_not_connected.project_id,
                user_uuid=user_not_connected.user_uuid,
            )


class TestSearchRGScopedUserFairShares:
    """Test search_rg_scoped_user_fair_shares method."""

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
                UserRoleRow,
                UserRow,
                KeyPairResourcePolicyRow,
                KeyPairRow,
                GroupRow,
                ScalingGroupForProjectRow,
                AssocGroupUserRow,
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

    async def _create_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        project_name: str,
    ) -> uuid.UUID:
        """Helper to create a project."""
        project_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=f"prp-{project_id.hex[:8]}",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()
            db_sess.add(
                GroupRow(
                    id=project_id,
                    name=project_name,
                    description="Test project",
                    is_active=True,
                    domain_name=domain_name,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    resource_policy=f"prp-{project_id.hex[:8]}",
                )
            )
            await db_sess.commit()
        return project_id

    async def _create_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_name: str,
        project_id: uuid.UUID,
        user_email: str,
    ) -> uuid.UUID:
        """Helper to create a user and associate with project."""
        user_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name=f"urp-{user_uuid.hex[:8]}",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name=f"kprp-{user_uuid.hex[:8]}",
                    total_resource_slots={},
                    max_session_lifetime=0,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=5,
                    max_containers_per_session=1,
                )
            )
            await db_sess.flush()
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    email=user_email,
                    username=user_email.split("@")[0],
                    password=PasswordInfo(
                        password="test",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=100_000,
                        salt_size=16,
                    ),
                    need_password_change=False,
                    domain_name=domain_name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    status_info="",
                    resource_policy=f"urp-{user_uuid.hex[:8]}",
                    allowed_client_ip=None,
                    totp_key=None,
                    totp_key_last_used=None,
                    main_access_key=None,
                )
            )
            await db_sess.flush()
            db_sess.add(
                KeyPairRow(
                    access_key=f"AK{user_uuid.hex[:16]}",
                    user=user_uuid,
                    secret_key="SK" + user_uuid.hex,
                    is_active=True,
                    is_admin=False,
                    resource_policy=f"kprp-{user_uuid.hex[:8]}",
                )
            )
            db_sess.add(
                AssocGroupUserRow(
                    group_id=project_id,
                    user_id=user_uuid,
                )
            )
            await db_sess.commit()
        return user_uuid

    @dataclass
    class UserSearchContext:
        scaling_group: str
        domain_name: str
        project_id: uuid.UUID
        users_with_record: list[uuid.UUID]
        users_without_record: list[uuid.UUID]

    @pytest.fixture
    async def context_all_with_records(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        domain_name: str,
    ) -> UserSearchContext:
        """All users connected with fair share records."""
        project_id = await self._create_project(
            db_with_cleanup, domain_name, f"proj-all-{uuid.uuid4().hex[:8]}"
        )
        users = []
        for i in range(3):
            user_uuid = await self._create_user(
                db_with_cleanup,
                domain_name,
                project_id,
                f"user-all-{i}-{uuid.uuid4().hex[:8]}@test.com",
            )
            users.append(user_uuid)

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(ScalingGroupForProjectRow(scaling_group=scaling_group, group=project_id))
            for user_uuid in users:
                db_sess.add(
                    UserFairShareRow(
                        resource_group=scaling_group,
                        user_uuid=user_uuid,
                        project_id=project_id,
                        domain_name=domain_name,
                        weight=Decimal("1.0"),
                        fair_share_factor=Decimal("1.0"),
                        total_decayed_usage=ResourceSlot(),
                        normalized_usage=Decimal("0"),
                        resource_weights=ResourceSlot(),
                    )
                )
            await db_sess.commit()

        return self.UserSearchContext(
            scaling_group=scaling_group,
            domain_name=domain_name,
            project_id=project_id,
            users_with_record=users,
            users_without_record=[],
        )

    @pytest.fixture
    async def context_mixed_records(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        domain_name: str,
    ) -> UserSearchContext:
        """Some users with records, some without."""
        project_id = await self._create_project(
            db_with_cleanup, domain_name, f"proj-mixed-{uuid.uuid4().hex[:8]}"
        )
        user_with = await self._create_user(
            db_with_cleanup, domain_name, project_id, f"user-with-{uuid.uuid4().hex[:8]}@test.com"
        )
        users_without = []
        for i in range(2):
            user_uuid = await self._create_user(
                db_with_cleanup,
                domain_name,
                project_id,
                f"user-without-{i}-{uuid.uuid4().hex[:8]}@test.com",
            )
            users_without.append(user_uuid)

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(ScalingGroupForProjectRow(scaling_group=scaling_group, group=project_id))
            db_sess.add(
                UserFairShareRow(
                    resource_group=scaling_group,
                    user_uuid=user_with,
                    project_id=project_id,
                    domain_name=domain_name,
                    weight=Decimal("1.0"),
                    fair_share_factor=Decimal("1.0"),
                    total_decayed_usage=ResourceSlot(),
                    normalized_usage=Decimal("0"),
                    resource_weights=ResourceSlot(),
                )
            )
            await db_sess.commit()

        return self.UserSearchContext(
            scaling_group=scaling_group,
            domain_name=domain_name,
            project_id=project_id,
            users_with_record=[user_with],
            users_without_record=users_without,
        )

    @pytest.fixture
    async def context_all_without_records(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        domain_name: str,
    ) -> UserSearchContext:
        """All users connected without fair share records."""
        project_id = await self._create_project(
            db_with_cleanup, domain_name, f"proj-none-{uuid.uuid4().hex[:8]}"
        )
        users = []
        for i in range(3):
            user_uuid = await self._create_user(
                db_with_cleanup,
                domain_name,
                project_id,
                f"user-none-{i}-{uuid.uuid4().hex[:8]}@test.com",
            )
            users.append(user_uuid)

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(ScalingGroupForProjectRow(scaling_group=scaling_group, group=project_id))
            await db_sess.commit()

        return self.UserSearchContext(
            scaling_group=scaling_group,
            domain_name=domain_name,
            project_id=project_id,
            users_with_record=[],
            users_without_record=users,
        )

    @pytest.fixture
    async def context_no_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
        domain_name: str,
    ) -> UserSearchContext:
        """No users connected to RG (no project or empty project)."""
        project_id = await self._create_project(
            db_with_cleanup, domain_name, f"proj-empty-{uuid.uuid4().hex[:8]}"
        )
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(ScalingGroupForProjectRow(scaling_group=scaling_group, group=project_id))
            await db_sess.commit()

        return self.UserSearchContext(
            scaling_group=scaling_group,
            domain_name=domain_name,
            project_id=project_id,
            users_with_record=[],
            users_without_record=[],
        )

    async def test_all_users_with_records(
        self,
        fair_share_repository: FairShareRepository,
        context_all_with_records: UserSearchContext,
    ) -> None:
        """All users have fair share records - all details should be present."""
        scope = UserFairShareSearchScope(
            resource_group=context_all_with_records.scaling_group,
            domain_name=context_all_with_records.domain_name,
            project_id=context_all_with_records.project_id,
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=100, offset=0))

        result = await fair_share_repository.search_rg_scoped_user_fair_shares(scope, querier)

        assert result.total_count == 3
        assert len(result.items) == 3
        for item in result.items:
            assert item.details is not None
            assert item.user_uuid in context_all_with_records.users_with_record

    async def test_mixed_records(
        self,
        fair_share_repository: FairShareRepository,
        context_mixed_records: UserSearchContext,
    ) -> None:
        """Some users with records, some without."""
        scope = UserFairShareSearchScope(
            resource_group=context_mixed_records.scaling_group,
            domain_name=context_mixed_records.domain_name,
            project_id=context_mixed_records.project_id,
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=100, offset=0))

        result = await fair_share_repository.search_rg_scoped_user_fair_shares(scope, querier)

        assert result.total_count == 3
        assert len(result.items) == 3

        with_details = [item for item in result.items if item.details is not None]
        without_details = [item for item in result.items if item.details is None]

        assert len(with_details) == 1
        assert len(without_details) == 2
        assert with_details[0].user_uuid in context_mixed_records.users_with_record
        for item in without_details:
            assert item.user_uuid in context_mixed_records.users_without_record

    async def test_all_users_without_records(
        self,
        fair_share_repository: FairShareRepository,
        context_all_without_records: UserSearchContext,
    ) -> None:
        """All users without fair share records - all details should be None."""
        scope = UserFairShareSearchScope(
            resource_group=context_all_without_records.scaling_group,
            domain_name=context_all_without_records.domain_name,
            project_id=context_all_without_records.project_id,
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=100, offset=0))

        result = await fair_share_repository.search_rg_scoped_user_fair_shares(scope, querier)

        assert result.total_count == 3
        assert len(result.items) == 3
        for item in result.items:
            assert item.details is None
            assert item.user_uuid in context_all_without_records.users_without_record

    async def test_no_users_connected(
        self,
        fair_share_repository: FairShareRepository,
        context_no_users: UserSearchContext,
    ) -> None:
        """No users connected to RG - returns empty result."""
        scope = UserFairShareSearchScope(
            resource_group=context_no_users.scaling_group,
            domain_name=context_no_users.domain_name,
            project_id=context_no_users.project_id,
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=100, offset=0))

        result = await fair_share_repository.search_rg_scoped_user_fair_shares(scope, querier)

        assert result.total_count == 0
        assert len(result.items) == 0
