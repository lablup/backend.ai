import uuid
from dataclasses import dataclass
from typing import AsyncGenerator

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from ai.backend.common.types import BinarySize
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


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
    async def domain(
        self, database_engine: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[DomainRow, None]:
        """Create test domain."""
        domain = DomainRow(name=f"test-{uuid.uuid4()}")

        try:
            async with database_engine.begin_session() as db_sess:
                db_sess.add(domain)
                await db_sess.flush()

            yield domain
        finally:
            # Clean up domain data
            async with database_engine.begin() as conn:
                await conn.execute(sa.delete(DomainRow).where(DomainRow.name == domain.name))

    @pytest.fixture
    async def user_policy(
        self, database_engine: ExtendedAsyncSAEngine, domain: DomainRow
    ) -> AsyncGenerator[UserResourcePolicyRow, None]:
        """Create test user resource policy."""
        policy = UserResourcePolicyRow(
            name=f"{uuid.uuid4()}",
            max_vfolder_count=10,
            max_quota_scope_size=BinarySize.from_str("10GiB"),
            max_session_count_per_model_session=5,
            max_customized_image_count=3,
        )

        try:
            async with database_engine.begin_session() as db_sess:
                db_sess.add(policy)
                await db_sess.flush()

            yield policy

        finally:
            # Clean up user policy data
            async with database_engine.begin() as conn:
                await conn.execute(
                    sa.delete(UserResourcePolicyRow).where(
                        UserResourcePolicyRow.name == policy.name
                    )
                )

    @pytest.fixture
    async def group_policy(
        self, database_engine: ExtendedAsyncSAEngine, domain: DomainRow
    ) -> AsyncGenerator[ProjectResourcePolicyRow, None]:
        """Create test project resource policy."""
        policy = ProjectResourcePolicyRow(
            name=f"{uuid.uuid4()}",
            max_vfolder_count=10,
            max_quota_scope_size=BinarySize.from_str("10GiB"),
            max_network_count=5,
        )

        try:
            async with database_engine.begin_session() as db_sess:
                db_sess.add(policy)
                await db_sess.flush()

            yield policy
        finally:
            # Clean up group policy data
            async with database_engine.begin() as conn:
                await conn.execute(
                    sa.delete(ProjectResourcePolicyRow).where(
                        ProjectResourcePolicyRow.name == policy.name
                    )
                )

    @pytest.fixture
    async def user_one(
        self,
        database_engine: ExtendedAsyncSAEngine,
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

        try:
            async with database_engine.begin_session() as db_sess:
                db_sess.add(user_a)
                await db_sess.flush()

            yield UserData(uuid=user_a.uuid, email=user_a.email)
        finally:
            # Clean up user data
            async with database_engine.begin() as conn:
                await conn.execute(sa.delete(UserRow).where(UserRow.uuid == user_a.uuid))

    @pytest.fixture
    async def user_two(
        self,
        database_engine: ExtendedAsyncSAEngine,
        domain: DomainRow,
        user_policy: UserResourcePolicyRow,
    ) -> AsyncGenerator[UserData, None]:
        user_b = UserRow(
            uuid=uuid.uuid4(),
            email=f"user-b-{uuid.uuid4().hex[:8]}@example.com",
            domain_name=domain.name,
            resource_policy=user_policy.name,
        )

        try:
            async with database_engine.begin_session() as db_sess:
                db_sess.add(user_b)
                await db_sess.flush()

            yield UserData(uuid=user_b.uuid, email=user_b.email)
        finally:
            # Clean up user data
            async with database_engine.begin() as conn:
                await conn.execute(sa.delete(UserRow).where(UserRow.uuid == user_b.uuid))

    @pytest.fixture
    async def group(
        self,
        database_engine: ExtendedAsyncSAEngine,
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

        try:
            async with database_engine.begin_session() as db_sess:
                db_sess.add(group)
                await db_sess.flush()

            yield group
        finally:
            # Clean up group data
            async with database_engine.begin() as conn:
                await conn.execute(sa.delete(GroupRow).where(GroupRow.id == group.id))

    @pytest.fixture
    async def prepared_first_session(
        self,
        database_engine: ExtendedAsyncSAEngine,
        user_one: UserData,
        group: GroupRow,
        domain: DomainRow,
        test_config: TestConfig,
    ) -> AsyncGenerator[SessionData, None]:
        """Create first session with status from parametrize (indirect fixture)"""
        user_a = user_one
        status = test_config.first_session_status
        session = SessionRow(
            name=f"test-{str(uuid.uuid4())}",
            user_uuid=user_a.uuid,
            group_id=group.id,
            domain_name=domain.name,
            status=status,
            occupying_slots={},
            requested_slots={},
            vfolder_mounts=[],
        )

        try:
            async with database_engine.begin_session() as db_sess:
                db_sess.add(session)
                await db_sess.flush()

            yield SessionData(
                name=session.name,
                user_uuid=user_a.uuid,
                group_id=group.id,
                domain_name=domain.name,
                status=status,
            )
        finally:
            async with database_engine.begin() as conn:
                await conn.execute(sa.delete(SessionRow).where(SessionRow.name == session.name))

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
        database_engine: ExtendedAsyncSAEngine,
        prepared_first_session: SessionData,
    ) -> None:
        async with database_engine.begin_session() as db_sess:
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

            try:
                # This should succeed without IntegrityError
                db_sess.add(duplicate_session)
                await db_sess.flush()

            finally:
                # Clean up the duplicate session
                await db_sess.delete(duplicate_session)

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
        database_engine: ExtendedAsyncSAEngine,
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
            async with database_engine.begin_session() as db_sess:
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
        database_engine: ExtendedAsyncSAEngine,
        prepared_first_session: SessionData,
        user_two: UserData,
        test_config: TestConfig,
    ) -> None:
        async with database_engine.begin_session() as db_sess:
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

            try:
                # This should succeed without IntegrityError
                db_sess.add(duplicate_session)
                await db_sess.flush()
            finally:
                # Clean up the duplicate session
                await db_sess.delete(duplicate_session)
