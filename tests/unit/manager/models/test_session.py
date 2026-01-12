from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
from sqlalchemy.exc import IntegrityError

from ai.backend.common.types import BinarySize
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
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
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.testutils.db import with_tables


@dataclass
class UserData:
    uuid: uuid.UUID
    email: str


@dataclass
class SessionData:
    name: str
    user_uuid: uuid.UUID
    group_id: uuid.UUID
    domain_name: str
    status: SessionStatus


@dataclass
class TestConfig:
    first_session_status: SessionStatus
    second_session_status: SessionStatus


class TestSessionUniqueNamePerUser:
    @pytest.fixture
    async def database_with_tables(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Set up tables required for session tests with automatic cleanup."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
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
                VFolderRow,
                ImageRow,
                ResourcePresetRow,
                EndpointRow,
                DeploymentRevisionRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentPolicyRow,
                SessionRow,
                KernelRow,
                RoutingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def domain(
        self, database_with_tables: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[DomainRow, None]:
        """Create test domain."""
        domain = DomainRow(name=f"test-{uuid.uuid4()}")

        async with database_with_tables.begin_session() as db_sess:
            db_sess.add(domain)
            await db_sess.flush()

        yield domain

    @pytest.fixture
    async def user_policy(
        self, database_with_tables: ExtendedAsyncSAEngine, domain: DomainRow
    ) -> AsyncGenerator[UserResourcePolicyRow, None]:
        """Create test user resource policy."""
        policy = UserResourcePolicyRow(
            name=f"{uuid.uuid4()}",
            max_vfolder_count=10,
            max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
            max_session_count_per_model_session=5,
            max_customized_image_count=3,
        )

        async with database_with_tables.begin_session() as db_sess:
            db_sess.add(policy)
            await db_sess.flush()

        yield policy

    @pytest.fixture
    async def group_policy(
        self, database_with_tables: ExtendedAsyncSAEngine, domain: DomainRow
    ) -> AsyncGenerator[ProjectResourcePolicyRow, None]:
        """Create test project resource policy."""
        policy = ProjectResourcePolicyRow(
            name=f"{uuid.uuid4()}",
            max_vfolder_count=10,
            max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
            max_network_count=5,
        )

        async with database_with_tables.begin_session() as db_sess:
            db_sess.add(policy)
            await db_sess.flush()

        yield policy

    @pytest.fixture
    async def user_one(
        self,
        database_with_tables: ExtendedAsyncSAEngine,
        domain: DomainRow,
        user_policy: UserResourcePolicyRow,
    ) -> AsyncGenerator[UserData, None]:
        """Create test user for testing unique constraint."""
        user_a = UserRow(
            uuid=uuid.uuid4(),
            email=f"user-a-{uuid.uuid4().hex[:8]}@example.com",
            domain_name=domain.name,
            resource_policy=user_policy.name,
        )

        async with database_with_tables.begin_session() as db_sess:
            db_sess.add(user_a)
            await db_sess.flush()

        yield UserData(uuid=user_a.uuid, email=user_a.email)

    @pytest.fixture
    async def user_two(
        self,
        database_with_tables: ExtendedAsyncSAEngine,
        domain: DomainRow,
        user_policy: UserResourcePolicyRow,
    ) -> AsyncGenerator[UserData, None]:
        user_b = UserRow(
            uuid=uuid.uuid4(),
            email=f"user-b-{uuid.uuid4().hex[:8]}@example.com",
            domain_name=domain.name,
            resource_policy=user_policy.name,
        )

        async with database_with_tables.begin_session() as db_sess:
            db_sess.add(user_b)
            await db_sess.flush()

        yield UserData(uuid=user_b.uuid, email=user_b.email)

    @pytest.fixture
    async def group(
        self,
        database_with_tables: ExtendedAsyncSAEngine,
        domain: DomainRow,
        group_policy: ProjectResourcePolicyRow,
    ) -> AsyncGenerator[GroupRow, None]:
        """Create test group."""
        group = GroupRow(
            id=uuid.uuid4(),
            name=f"test-group-{uuid.uuid4().hex[:8]}",
            domain_name=domain.name,
            resource_policy=group_policy.name,
        )

        async with database_with_tables.begin_session() as db_sess:
            db_sess.add(group)
            await db_sess.flush()

        yield group

    @pytest.fixture
    async def prepared_first_session(
        self,
        database_with_tables: ExtendedAsyncSAEngine,
        user_one: UserData,
        group: GroupRow,
        domain: DomainRow,
        test_config: TestConfig,
    ) -> AsyncGenerator[SessionData, None]:
        """Create first session with status from parametrize (indirect fixture)"""
        user_a = user_one
        status = test_config.first_session_status
        session = SessionRow(
            name=f"test-{uuid.uuid4()!s}",
            user_uuid=user_a.uuid,
            group_id=group.id,
            domain_name=domain.name,
            status=status,
            occupying_slots={},
            requested_slots={},
            vfolder_mounts=[],
        )

        async with database_with_tables.begin_session() as db_sess:
            db_sess.add(session)
            await db_sess.flush()

        assert session.name is not None
        yield SessionData(
            name=session.name,
            user_uuid=user_a.uuid,
            group_id=group.id,
            domain_name=domain.name,
            status=status,
        )

    @pytest.mark.parametrize(
        "test_config",
        [
            TestConfig(
                first_session_status=SessionStatus.ERROR,  # Terminal
                second_session_status=SessionStatus.TERMINATED,  # Terminal
            ),
            TestConfig(
                first_session_status=SessionStatus.CANCELLED,  # Terminal
                second_session_status=SessionStatus.PENDING,  # Non-terminal
            ),
        ],
    )
    async def test_duplicate_session_name_with_terminal_status_in_same_user(
        self,
        test_config: TestConfig,
        database_with_tables: ExtendedAsyncSAEngine,
        prepared_first_session: SessionData,
    ) -> None:
        async with database_with_tables.begin_session() as db_sess:
            duplicate_session = SessionRow(
                name=prepared_first_session.name,
                user_uuid=prepared_first_session.user_uuid,
                group_id=prepared_first_session.group_id,
                domain_name=prepared_first_session.domain_name,
                status=test_config.second_session_status,
                occupying_slots={},
                requested_slots={},
                vfolder_mounts=[],
            )

            # This should succeed without IntegrityError
            db_sess.add(duplicate_session)
            await db_sess.flush()

    @pytest.mark.parametrize(
        "test_config",
        [
            TestConfig(
                first_session_status=SessionStatus.PENDING,  # Non-terminal
                second_session_status=SessionStatus.RUNNING,  # Non-terminal
            ),
        ],
    )
    async def test_duplicate_session_name_with_non_terminal_status_in_same_user(
        self,
        test_config: TestConfig,
        database_with_tables: ExtendedAsyncSAEngine,
        prepared_first_session: SessionData,
    ) -> None:
        duplicate_session = SessionRow(
            name=prepared_first_session.name,
            user_uuid=prepared_first_session.user_uuid,
            group_id=prepared_first_session.group_id,
            domain_name=prepared_first_session.domain_name,
            status=test_config.second_session_status,
            occupying_slots={},
            requested_slots={},
            vfolder_mounts=[],
        )

        with pytest.raises(IntegrityError):
            async with database_with_tables.begin_session() as db_sess:
                db_sess.add(duplicate_session)
                await db_sess.flush()

    @pytest.mark.parametrize(
        "test_config",
        [
            TestConfig(
                first_session_status=SessionStatus.PENDING,  # Non-terminal
                second_session_status=SessionStatus.TERMINATED,  # Terminal
            ),
            TestConfig(
                first_session_status=SessionStatus.ERROR,  # Terminal
                second_session_status=SessionStatus.TERMINATED,  # Terminal
            ),
            TestConfig(
                first_session_status=SessionStatus.RUNNING,  # Non-terminal
                second_session_status=SessionStatus.PENDING,  # Non-terminal
            ),
        ],
    )
    async def test_duplicate_session_name_different_user(
        self,
        database_with_tables: ExtendedAsyncSAEngine,
        prepared_first_session: SessionData,
        user_two: UserData,
        test_config: TestConfig,
    ) -> None:
        async with database_with_tables.begin_session() as db_sess:
            duplicate_session = SessionRow(
                name=prepared_first_session.name,
                user_uuid=user_two.uuid,  # Different user
                group_id=prepared_first_session.group_id,
                domain_name=prepared_first_session.domain_name,
                status=test_config.second_session_status,
                occupying_slots={},
                requested_slots={},
                vfolder_mounts=[],
            )

            # This should succeed without IntegrityError
            db_sess.add(duplicate_session)
            await db_sess.flush()
