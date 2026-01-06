"""
Tests for ErrorLogRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.types import BinarySize
from ai.backend.manager.data.error_log.types import ErrorLogData, ErrorLogSeverity
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.error_log import ErrorLogCreatorSpec, ErrorLogRepository
from ai.backend.testutils.db import with_tables


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
                DomainRow,
                UserResourcePolicyRow,
                UserRoleRow,
                UserRow,
                ErrorLogRow,
            ],
        ):
            yield database_connection

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
                description="Test domain for error log",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.commit()

        return domain_name

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
        test_domain_name: str,
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
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=test_resource_policy_name,
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

    @pytest.mark.asyncio
    async def test_create_multiple_error_logs(
        self,
        error_log_repository: ErrorLogRepository,
        test_user_id: uuid.UUID,
    ) -> None:
        """Test creating multiple error logs and verifying them"""
        error_log_specs = [
            ErrorLogCreatorSpec(
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
            ErrorLogCreatorSpec(
                severity=ErrorLogSeverity.ERROR,
                source="agent",
                user=test_user_id,
                message="Error in agent",
                context_lang="en",
                context_env={"agent_id": "agent-001"},
            ),
            ErrorLogCreatorSpec(
                severity=ErrorLogSeverity.WARNING,
                source="storage",
                user=None,
                message="Storage warning",
                context_lang="ko",
                context_env={"storage_id": "storage-001"},
                request_url="/api/v1/storage",
                request_status=400,
            ),
        ]

        created_logs: list[ErrorLogData] = []

        for spec in error_log_specs:
            creator = Creator(spec=spec)
            result = await error_log_repository.create(creator)
            created_logs.append(result)

        # Verify all logs were created
        assert len(created_logs) == 3

        # Verify first log (CRITICAL)
        assert created_logs[0].severity == ErrorLogSeverity.CRITICAL
        assert created_logs[0].source == "manager"
        assert created_logs[0].user == test_user_id
        assert created_logs[0].message == "Critical error occurred"
        assert created_logs[0].context_lang == "en"
        assert created_logs[0].context_env == {"version": "1.0.0"}
        assert created_logs[0].request_url == "/api/v1/test"
        assert created_logs[0].request_status == 500
        assert created_logs[0].traceback == "Traceback: ..."
        assert created_logs[0].is_read is False
        assert created_logs[0].is_cleared is False
        assert created_logs[0].id is not None
        assert created_logs[0].created_at is not None

        # Verify second log (ERROR)
        assert created_logs[1].severity == ErrorLogSeverity.ERROR
        assert created_logs[1].source == "agent"
        assert created_logs[1].user == test_user_id
        assert created_logs[1].message == "Error in agent"
        assert created_logs[1].request_url is None
        assert created_logs[1].request_status is None
        assert created_logs[1].traceback is None

        # Verify third log (WARNING, no user)
        assert created_logs[2].severity == ErrorLogSeverity.WARNING
        assert created_logs[2].source == "storage"
        assert created_logs[2].user is None
        assert created_logs[2].message == "Storage warning"
        assert created_logs[2].context_lang == "ko"

        # Verify all IDs are unique
        ids = [log.id for log in created_logs]
        assert len(ids) == len(set(ids))
