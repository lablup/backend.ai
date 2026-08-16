"""
Tests for ErrorLogRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.data.error_log.types import (
    ErrorLogData,
    ErrorLogSeverity,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.error_log.creators import ErrorLogCreator
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.error_log import ErrorLogRepository
from ai.backend.manager.repositories.error_log.searchers import ErrorLogSearcher
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFixtureData


class TestErrorLogRepository:
    """Test cases for ErrorLogRepository"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AgentRow,
                VFolderRow,
                ContainerRegistryRow,
                ImageRow,
                ResourcePresetRow,
                EndpointRow,
                RuntimeVariantRow,
                DeploymentRevisionPresetRow,
                DeploymentRevisionRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentPolicyRow,
                ErrorLogRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainFixtureData:
        """Create test domain and return domain name"""
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                id=domain_id,
                name=domain_name,
                description="Test domain for error log",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.commit()

        return DomainFixtureData(domain_name=DomainName(domain_name), domain_id=domain_id)

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test resource policy and return policy name"""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_user_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_resource_policy_name: str,
    ) -> uuid.UUID:
        """Create test user and return user UUID"""
        user_uuid = uuid.uuid4()

        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain.domain_name,
                role=UserRole.USER,
                resource_policy=test_resource_policy_name,
                domain_id=test_domain.domain_id,
            )
            db_sess.add(user)
            await db_sess.commit()

        return user_uuid

    @pytest.fixture
    def error_log_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ErrorLogRepository:
        """Create ErrorLogRepository instance with database"""
        return ErrorLogRepository(db=db_with_cleanup)

    @pytest.fixture
    def error_log_ops(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> OpsRepository[ErrorLogData]:
        """Searches run through the generic ops repository the v2 searcher wires to."""
        return OpsRepository(V2DBOpsProvider(db_with_cleanup))

    async def test_create_multiple_error_logs(
        self,
        error_log_repository: ErrorLogRepository,
        error_log_ops: OpsRepository[ErrorLogData],
        test_user_id: uuid.UUID,
    ) -> None:
        """Test creating multiple error logs and verifying them"""
        error_log_specs = [
            ErrorLogCreator(
                severity=ErrorLogSeverity.CRITICAL,
                source="manager",
                user=test_user_id,
                message="Critical error occurred",
                context_lang="en",
                context_env={"version": "1.0.0"},
                request_url="/api/v1/test",
                request_status=500,
                traceback="Traceback: ...",
            ),
            ErrorLogCreator(
                severity=ErrorLogSeverity.ERROR,
                source="agent",
                user=test_user_id,
                message="Error in agent",
                context_lang="en",
                context_env={"agent_id": "agent-001"},
            ),
            ErrorLogCreator(
                severity=ErrorLogSeverity.WARNING,
                source="storage",
                message="Storage warning",
                context_lang="ko",
                context_env={"storage_id": "storage-001"},
                request_url="/api/v1/storage",
                request_status=400,
            ),
        ]

        created_logs: list[ErrorLogData] = []

        for creator in error_log_specs:
            created_logs.append(await error_log_repository.create(creator))

        # Verify all logs were created with correct data
        assert len(created_logs) == 3

        # Verify first log (CRITICAL)
        assert created_logs[0].content.severity == ErrorLogSeverity.CRITICAL
        assert created_logs[0].meta.source == "manager"
        assert created_logs[0].meta.user == test_user_id
        assert created_logs[0].content.message == "Critical error occurred"
        assert created_logs[0].meta.context_lang == "en"
        assert created_logs[0].meta.context_env == {"version": "1.0.0"}
        assert created_logs[0].meta.request_url == "/api/v1/test"
        assert created_logs[0].meta.request_status == 500
        assert created_logs[0].content.traceback == "Traceback: ..."
        assert created_logs[0].meta.is_read is False
        assert created_logs[0].meta.is_cleared is False
        assert created_logs[0].id is not None
        assert created_logs[0].meta.created_at is not None

        # Verify second log (ERROR)
        assert created_logs[1].content.severity == ErrorLogSeverity.ERROR
        assert created_logs[1].meta.source == "agent"
        assert created_logs[1].meta.user == test_user_id
        assert created_logs[1].content.message == "Error in agent"
        assert created_logs[1].meta.request_url is None
        assert created_logs[1].meta.request_status is None
        assert created_logs[1].content.traceback is None

        # Verify third log (WARNING, no user)
        assert created_logs[2].content.severity == ErrorLogSeverity.WARNING
        assert created_logs[2].meta.source == "storage"
        assert created_logs[2].meta.user is None
        assert created_logs[2].content.message == "Storage warning"
        assert created_logs[2].meta.context_lang == "ko"

        # Verify all IDs are unique
        ids = [log.id for log in created_logs]
        assert len(ids) == len(set(ids))

    # =========================================================================
    # Fixtures for search tests
    # =========================================================================

    @pytest.fixture
    async def sample_error_logs_for_filtering(
        self,
        error_log_repository: ErrorLogRepository,
        error_log_ops: OpsRepository[ErrorLogData],
        test_user_id: uuid.UUID,
    ) -> AsyncGenerator[dict[str, uuid.UUID], None]:
        """Create sample error logs with different sources for filter testing"""
        entity_map: dict[str, uuid.UUID] = {}

        test_data = [
            ("manager", ErrorLogSeverity.CRITICAL, "Manager critical error"),
            ("agent", ErrorLogSeverity.ERROR, "Agent error occurred"),
        ]

        for source, severity, message in test_data:
            creator = ErrorLogCreator(
                severity=severity,
                source=source,
                user=test_user_id,
                message=message,
                context_lang="en",
                context_env={},
            )
            result = await error_log_repository.create(creator)
            entity_map[source] = result.id

        yield entity_map

    @pytest.fixture
    async def sample_error_logs_for_ordering(
        self,
        error_log_repository: ErrorLogRepository,
        error_log_ops: OpsRepository[ErrorLogData],
        test_user_id: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create sample error logs with predictable sources for ordering tests"""
        error_log_ids: list[uuid.UUID] = []
        sources = ["alpha-source", "beta-source", "gamma-source", "delta-source"]

        for source in sources:
            creator = ErrorLogCreator(
                severity=ErrorLogSeverity.ERROR,
                source=source,
                user=test_user_id,
                message=f"Error from {source}",
                context_lang="en",
                context_env={},
            )
            result = await error_log_repository.create(creator)
            error_log_ids.append(result.id)

        yield error_log_ids

    @pytest.fixture
    async def sample_error_logs_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_id: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 25 error logs for pagination testing"""
        specs = [
            ErrorLogCreator(
                severity=ErrorLogSeverity.ERROR,
                source=f"source_{i:02d}",
                user=test_user_id,
                message=f"Error message {i}",
                context_lang="en",
                context_env={},
            )
            for i in range(25)
        ]

        async with db_with_cleanup.begin_session() as db_sess:
            rows = [creator.build_row() for creator in specs]
            db_sess.add_all(rows)
            await db_sess.flush()
            ids = [row.id for row in rows]
            await db_sess.commit()

        yield ids

    # =========================================================================
    # Tests - Search with filtering
    # =========================================================================

    async def test_search_error_logs_filter_by_source(
        self,
        error_log_ops: OpsRepository[ErrorLogData],
        sample_error_logs_for_filtering: dict[str, uuid.UUID],
    ) -> None:
        """Test searching error logs filtered by source returns only matching error logs"""
        target_source = "manager"

        searcher = ErrorLogSearcher(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ErrorLogRow.source == target_source,
            ],
            orders=[],
        )

        result = await error_log_ops.search_in_global(searcher)

        result_ids = [log.id for log in result.items]
        assert sample_error_logs_for_filtering["manager"] in result_ids
        assert sample_error_logs_for_filtering["agent"] not in result_ids

    async def test_search_error_logs_filter_by_severity(
        self,
        error_log_ops: OpsRepository[ErrorLogData],
        sample_error_logs_for_filtering: dict[str, uuid.UUID],
    ) -> None:
        """Test searching error logs filtered by severity"""
        searcher = ErrorLogSearcher(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ErrorLogRow.severity == ErrorLogSeverity.CRITICAL.value,
            ],
            orders=[],
        )

        result = await error_log_ops.search_in_global(searcher)

        assert len(result.items) == 1
        assert result.items[0].content.severity == ErrorLogSeverity.CRITICAL

    # =========================================================================
    # Tests - Search with ordering
    # =========================================================================

    async def test_search_error_logs_order_by_source_ascending(
        self,
        error_log_ops: OpsRepository[ErrorLogData],
        sample_error_logs_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching error logs ordered by source ascending"""
        searcher = ErrorLogSearcher(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[ErrorLogRow.source.asc()],
        )

        result = await error_log_ops.search_in_global(searcher)

        result_sources = [log.meta.source for log in result.items]
        assert result_sources == sorted(result_sources)
        assert result_sources[0] == "alpha-source"
        assert result_sources[-1] == "gamma-source"

    async def test_search_error_logs_order_by_source_descending(
        self,
        error_log_ops: OpsRepository[ErrorLogData],
        sample_error_logs_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching error logs ordered by source descending"""
        searcher = ErrorLogSearcher(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[ErrorLogRow.source.desc()],
        )

        result = await error_log_ops.search_in_global(searcher)

        result_sources = [log.meta.source for log in result.items]
        assert result_sources == sorted(result_sources, reverse=True)
        assert result_sources[0] == "gamma-source"
        assert result_sources[-1] == "alpha-source"

    # =========================================================================
    # Tests - Search with pagination
    # =========================================================================

    async def test_search_error_logs_offset_pagination_first_page(
        self,
        error_log_ops: OpsRepository[ErrorLogData],
        sample_error_logs_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test first page of offset-based pagination"""
        searcher = ErrorLogSearcher(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await error_log_ops.search_in_global(searcher)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_error_logs_offset_pagination_second_page(
        self,
        error_log_ops: OpsRepository[ErrorLogData],
        sample_error_logs_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test second page of offset-based pagination"""
        searcher = ErrorLogSearcher(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )

        result = await error_log_ops.search_in_global(searcher)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_error_logs_offset_pagination_last_page(
        self,
        error_log_ops: OpsRepository[ErrorLogData],
        sample_error_logs_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test last page of offset-based pagination with partial results"""
        searcher = ErrorLogSearcher(
            pagination=OffsetPagination(limit=10, offset=20),
            conditions=[],
            orders=[],
        )

        result = await error_log_ops.search_in_global(searcher)

        assert len(result.items) == 5
        assert result.total_count == 25

    # =========================================================================
    # Tests - Search with combined query
    # =========================================================================

    async def test_search_error_logs_with_pagination_filter_and_order(
        self,
        error_log_ops: OpsRepository[ErrorLogData],
        sample_error_logs_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test searching error logs with pagination, filter condition, and ordering combined"""
        searcher = ErrorLogSearcher(
            pagination=OffsetPagination(limit=5, offset=2),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ErrorLogRow.severity == ErrorLogSeverity.ERROR.value,
            ],
            orders=[ErrorLogRow.source.asc()],
        )

        result = await error_log_ops.search_in_global(searcher)

        assert result.total_count == 25
        assert len(result.items) == 5

        result_sources = [log.meta.source for log in result.items]
        assert result_sources == sorted(result_sources)
