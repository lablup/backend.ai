"""
Tests for update_with_history functionality in ScheduleDBSource.
Tests that session status updates and history records are created atomically.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from decimal import Decimal

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    DefaultForUnspecified,
    ResourceSlot,
    SecretKey,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.session.types import SchedulingResult, SessionStatus
from ai.backend.manager.data.user.types import UserRole, UserStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.scheduling_history.row import SessionSchedulingHistoryRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.repositories.scheduler.updaters import SessionStatusBatchUpdaterSpec
from ai.backend.manager.repositories.scheduling_history.creators import (
    SessionSchedulingHistoryCreatorSpec,
)
from ai.backend.testutils.db import with_tables


class TestUpdateWithHistory:
    """Test suite for update_with_history functionality."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents first
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                SessionRow,
                SessionSchedulingHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test domain and return domain name."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("1000"),
                    "mem": Decimal("1048576"),
                }),
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield domain_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test resource policy and return policy name."""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            project_policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(project_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test user resource policy and return policy name."""
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            user_policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=3,
            )
            db_sess.add(user_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test keypair resource policy and return policy name."""
        policy_name = f"test-keypair-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            keypair_policy = KeyPairResourcePolicyRow(
                name=policy_name,
                default_for_unspecified=DefaultForUnspecified.LIMITED,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("100"),
                    "mem": Decimal("102400"),
                }),
                max_concurrent_sessions=10,
                max_containers_per_session=1,
                idle_timeout=600,
                max_session_lifetime=0,
                allowed_vfolder_hosts={},
            )
            db_sess.add(keypair_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test user and return user UUID."""
        user_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                email=f"test-user-{uuid.uuid4().hex[:8]}@test.com",
                username=f"test-user-{uuid.uuid4().hex[:8]}",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                domain_name=test_domain_name,
                resource_policy=test_user_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        yield user_uuid

    @pytest.fixture
    async def test_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AsyncGenerator[AccessKey, None]:
        """Create test keypair and return access key."""
        access_key = AccessKey(f"AKIA{uuid.uuid4().hex[:16].upper()}")

        async with db_with_cleanup.begin_session() as db_sess:
            keypair = KeyPairRow(
                user_id=f"test-user-{uuid.uuid4().hex[:8]}@test.com",
                access_key=access_key,
                secret_key=SecretKey(f"SK{uuid.uuid4().hex}"),
                is_active=True,
                is_admin=False,
                resource_policy=test_keypair_resource_policy_name,
                rate_limit=1000,
                num_queries=0,
                user=test_user_uuid,
            )
            db_sess.add(keypair)
            await db_sess.flush()

        yield access_key

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test group and return group ID."""
        group_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                description="Test group",
                is_active=True,
                domain_name=test_domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(group)
            await db_sess.flush()

        yield group_id

    @pytest.fixture
    async def test_session_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_group_id: uuid.UUID,
    ) -> AsyncGenerator[SessionId, None]:
        """Create test session in PREPARING status and return session ID."""
        session_id = SessionId(uuid.uuid4())

        async with db_with_cleanup.begin_session() as db_sess:
            session = SessionRow(
                id=session_id,
                creation_id=f"creation-{uuid.uuid4().hex[:8]}",
                name=f"test-session-{uuid.uuid4().hex[:8]}",
                session_type=SessionTypes.INTERACTIVE,
                domain_name=test_domain_name,
                group_id=test_group_id,
                status=SessionStatus.PREPARING,
                status_info="preparing",
                result=SessionResult.UNDEFINED,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                occupying_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                vfolder_mounts={},
                environ={},
                priority=0,
                created_at=datetime.now(tzutc()),
                num_queries=0,
                use_host_network=False,
            )
            db_sess.add(session)
            await db_sess.flush()

        yield session_id

    @pytest.mark.asyncio
    async def test_update_with_history_success(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_session_id: SessionId,
    ) -> None:
        """Test update_with_history updates session and creates history record atomically."""
        # Setup
        db_source = ScheduleDBSource(db_with_cleanup)

        from_status = SessionStatus.PREPARING
        to_status = SessionStatus.PREPARED

        # Create updater and history creator
        updater = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=to_status,
                reason="test-success",
            ),
            conditions=[
                lambda: SessionRow.id.in_([test_session_id]),
                lambda: SessionRow.status.in_([from_status]),
            ],
        )

        bulk_creator = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=test_session_id,
                    phase="prepare",
                    result=SchedulingResult.SUCCESS,
                    message="Preparation completed successfully",
                    from_status=from_status,
                    to_status=to_status,
                )
            ]
        )

        # Execute
        updated_count = await db_source.update_with_history(updater, bulk_creator)

        # Verify - session should be updated
        assert updated_count == 1

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            # Check session status
            stmt = sa.select(SessionRow).where(SessionRow.id == test_session_id)
            updated_session = await db_sess.scalar(stmt)
            assert updated_session is not None
            assert updated_session.status == SessionStatus.PREPARED
            assert updated_session.status_info == "test-success"

            # Check history record
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == test_session_id
            )
            history_record = await db_sess.scalar(history_stmt)
            assert history_record is not None
            assert history_record.phase == "prepare"
            assert history_record.result == str(SchedulingResult.SUCCESS)
            assert history_record.from_status == str(from_status)
            assert history_record.to_status == str(to_status)
            assert history_record.message == "Preparation completed successfully"

    @pytest.mark.asyncio
    async def test_update_with_history_failure(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_session_id: SessionId,
    ) -> None:
        """Test update_with_history records failure status correctly."""
        # Setup
        db_source = ScheduleDBSource(db_with_cleanup)

        from_status = SessionStatus.PREPARING
        to_status = SessionStatus.ERROR

        # Create updater and history creator for failure case
        updater = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=to_status,
                reason="agent-lost",
            ),
            conditions=[
                lambda: SessionRow.id.in_([test_session_id]),
                lambda: SessionRow.status.in_([from_status]),
            ],
        )

        bulk_creator = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=test_session_id,
                    phase="prepare",
                    result=SchedulingResult.FAILURE,
                    message="Agent connection lost during preparation",
                    from_status=from_status,
                    to_status=to_status,
                    error_code="AGENT_LOST",
                )
            ]
        )

        # Execute
        updated_count = await db_source.update_with_history(updater, bulk_creator)

        # Verify
        assert updated_count == 1

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            # Check session status
            stmt = sa.select(SessionRow).where(SessionRow.id == test_session_id)
            updated_session = await db_sess.scalar(stmt)
            assert updated_session is not None
            assert updated_session.status == SessionStatus.ERROR
            assert updated_session.status_info == "agent-lost"

            # Check history record with error code
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == test_session_id
            )
            history_record = await db_sess.scalar(history_stmt)
            assert history_record is not None
            assert history_record.result == str(SchedulingResult.FAILURE)
            assert history_record.error_code == "AGENT_LOST"

    @pytest.mark.asyncio
    async def test_update_with_history_multiple_sessions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_group_id: uuid.UUID,
    ) -> None:
        """Test update_with_history handles multiple sessions."""
        # Create multiple sessions
        session_ids: list[SessionId] = []

        async with db_with_cleanup.begin_session() as db_sess:
            for _ in range(3):
                session_id = SessionId(uuid.uuid4())
                session_ids.append(session_id)
                session = SessionRow(
                    id=session_id,
                    creation_id=f"creation-{uuid.uuid4().hex[:8]}",
                    name=f"test-session-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INTERACTIVE,
                    domain_name=test_domain_name,
                    group_id=test_group_id,
                    status=SessionStatus.PREPARING,
                    status_info="preparing",
                    result=SessionResult.UNDEFINED,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    occupying_slots=ResourceSlot(),
                    requested_slots=ResourceSlot(),
                    vfolder_mounts={},
                    environ={},
                    priority=0,
                    created_at=datetime.now(tzutc()),
                    num_queries=0,
                    use_host_network=False,
                )
                db_sess.add(session)

        # Setup
        db_source = ScheduleDBSource(db_with_cleanup)

        from_status = SessionStatus.PREPARING
        to_status = SessionStatus.PREPARED

        # Create updater for all sessions
        updater = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=to_status,
                reason="batch-success",
            ),
            conditions=[
                lambda: SessionRow.id.in_(session_ids),
                lambda: SessionRow.status.in_([from_status]),
            ],
        )

        # Create history records for all sessions
        bulk_creator = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=session_id,
                    phase="prepare",
                    result=SchedulingResult.SUCCESS,
                    message="Batch preparation completed",
                    from_status=from_status,
                    to_status=to_status,
                )
                for session_id in session_ids
            ]
        )

        # Execute
        updated_count = await db_source.update_with_history(updater, bulk_creator)

        # Verify - all sessions should be updated
        assert updated_count == 3

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            # Check all sessions are updated
            stmt = sa.select(SessionRow).where(SessionRow.id.in_(session_ids))
            result = await db_sess.execute(stmt)
            updated_sessions = result.scalars().all()
            assert len(updated_sessions) == 3
            for session in updated_sessions:
                assert session.status == SessionStatus.PREPARED

            # Check all history records are created
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id.in_(session_ids)
            )
            history_result = await db_sess.execute(history_stmt)
            history_records = history_result.scalars().all()
            assert len(history_records) == 3

    @pytest.mark.asyncio
    async def test_update_with_history_no_matching_sessions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test update_with_history when no sessions match the condition."""
        # Setup with non-existent session ID
        db_source = ScheduleDBSource(db_with_cleanup)
        non_existent_id = SessionId(uuid.uuid4())

        updater = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=SessionStatus.PREPARED,
                reason="test",
            ),
            conditions=[
                lambda: SessionRow.id.in_([non_existent_id]),
            ],
        )

        bulk_creator = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=non_existent_id,
                    phase="prepare",
                    result=SchedulingResult.SUCCESS,
                    message="Test message",
                    from_status=SessionStatus.PREPARING,
                    to_status=SessionStatus.PREPARED,
                )
            ]
        )

        # Execute - should not fail, but update count should be 0
        updated_count = await db_source.update_with_history(updater, bulk_creator)

        # Verify - no sessions updated, but history record is still created
        # (This matches the current behavior where history is always created)
        assert updated_count == 0

    @pytest.mark.asyncio
    async def test_update_with_history_empty_bulk_creator(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_session_id: SessionId,
    ) -> None:
        """Test update_with_history with empty bulk creator."""
        # Setup
        db_source = ScheduleDBSource(db_with_cleanup)

        from_status = SessionStatus.PREPARING
        to_status = SessionStatus.PREPARED

        updater = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=to_status,
                reason="test-empty-history",
            ),
            conditions=[
                lambda: SessionRow.id.in_([test_session_id]),
                lambda: SessionRow.status.in_([from_status]),
            ],
        )

        # Empty bulk creator
        bulk_creator: BulkCreator[SessionSchedulingHistoryRow] = BulkCreator(specs=[])

        # Execute
        updated_count = await db_source.update_with_history(updater, bulk_creator)

        # Verify - session should be updated, no history records
        assert updated_count == 1

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            stmt = sa.select(SessionRow).where(SessionRow.id == test_session_id)
            updated_session = await db_sess.scalar(stmt)
            assert updated_session is not None
            assert updated_session.status == SessionStatus.PREPARED

            # No history records should exist
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == test_session_id
            )
            history_record = await db_sess.scalar(history_stmt)
            assert history_record is None

    @pytest.mark.asyncio
    async def test_update_with_history_merge_same_phase_error_to_status(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_session_id: SessionId,
    ) -> None:
        """Test that repeated calls with same phase+error_code+to_status merge (increment attempts)."""
        db_source = ScheduleDBSource(db_with_cleanup)

        # First call - creates history record
        updater1 = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=SessionStatus.PREPARING,
                reason="retry-1",
            ),
            conditions=[
                lambda: SessionRow.id.in_([test_session_id]),
            ],
        )
        bulk_creator1 = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=test_session_id,
                    phase="schedule",
                    result=SchedulingResult.FAILURE,
                    message="No resources available",
                    from_status=SessionStatus.PENDING,
                    to_status=SessionStatus.PREPARING,
                    error_code="RESOURCE_EXHAUSTED",
                )
            ]
        )
        await db_source.update_with_history(updater1, bulk_creator1)

        # Verify first record created with attempts=1
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == test_session_id
            )
            first_record = await db_sess.scalar(history_stmt)
            assert first_record is not None
            first_record_id = first_record.id
            assert first_record.attempts == 1

        # Second call - same phase + error_code + to_status -> should merge
        updater2 = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=SessionStatus.PREPARING,
                reason="retry-2",
            ),
            conditions=[
                lambda: SessionRow.id.in_([test_session_id]),
            ],
        )
        bulk_creator2 = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=test_session_id,
                    phase="schedule",  # same phase
                    result=SchedulingResult.FAILURE,
                    message="Still no resources",  # different message - doesn't matter
                    from_status=SessionStatus.PENDING,  # different from_status - doesn't matter
                    to_status=SessionStatus.PREPARING,  # same to_status
                    error_code="RESOURCE_EXHAUSTED",  # same error_code
                )
            ]
        )
        await db_source.update_with_history(updater2, bulk_creator2)

        # Verify merged - same record, attempts=2
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == test_session_id
            )
            records = (await db_sess.execute(history_stmt)).scalars().all()
            assert len(records) == 1  # Still only one record
            assert records[0].id == first_record_id  # Same record
            assert records[0].attempts == 2  # Incremented

        # Third call - should merge again
        updater3 = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=SessionStatus.PREPARING,
                reason="retry-3",
            ),
            conditions=[
                lambda: SessionRow.id.in_([test_session_id]),
            ],
        )
        bulk_creator3 = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=test_session_id,
                    phase="schedule",
                    result=SchedulingResult.SUCCESS,  # different result - doesn't matter
                    message="Third attempt",
                    from_status=SessionStatus.SCHEDULED,  # different from_status
                    to_status=SessionStatus.PREPARING,
                    error_code="RESOURCE_EXHAUSTED",
                )
            ]
        )
        await db_source.update_with_history(updater3, bulk_creator3)

        # Verify merged - attempts=3
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == test_session_id
            )
            records = (await db_sess.execute(history_stmt)).scalars().all()
            assert len(records) == 1
            assert records[0].attempts == 3

    @pytest.mark.asyncio
    async def test_update_with_history_no_merge_different_phase(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_session_id: SessionId,
    ) -> None:
        """Test that different phase creates new record (no merge)."""
        db_source = ScheduleDBSource(db_with_cleanup)

        # First call
        updater1 = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=SessionStatus.PREPARING,
                reason="first",
            ),
            conditions=[lambda: SessionRow.id.in_([test_session_id])],
        )
        bulk_creator1 = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=test_session_id,
                    phase="schedule",
                    result=SchedulingResult.FAILURE,
                    message="First",
                    to_status=SessionStatus.PREPARING,
                    error_code="ERROR_A",
                )
            ]
        )
        await db_source.update_with_history(updater1, bulk_creator1)

        # Second call - different phase
        updater2 = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=SessionStatus.PREPARING,
                reason="second",
            ),
            conditions=[lambda: SessionRow.id.in_([test_session_id])],
        )
        bulk_creator2 = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=test_session_id,
                    phase="prepare",  # different phase
                    result=SchedulingResult.FAILURE,
                    message="Second",
                    to_status=SessionStatus.PREPARING,  # same to_status
                    error_code="ERROR_A",  # same error_code
                )
            ]
        )
        await db_source.update_with_history(updater2, bulk_creator2)

        # Verify - two separate records
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == test_session_id
            )
            records = (await db_sess.execute(history_stmt)).scalars().all()
            assert len(records) == 2
            phases = {r.phase for r in records}
            assert phases == {"schedule", "prepare"}
            assert all(r.attempts == 1 for r in records)

    @pytest.mark.asyncio
    async def test_update_with_history_no_merge_different_error_code(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_session_id: SessionId,
    ) -> None:
        """Test that different error_code creates new record (no merge)."""
        db_source = ScheduleDBSource(db_with_cleanup)

        # First call
        updater1 = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=SessionStatus.PREPARING,
                reason="first",
            ),
            conditions=[lambda: SessionRow.id.in_([test_session_id])],
        )
        bulk_creator1 = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=test_session_id,
                    phase="schedule",
                    result=SchedulingResult.FAILURE,
                    message="First",
                    to_status=SessionStatus.PREPARING,
                    error_code="ERROR_A",
                )
            ]
        )
        await db_source.update_with_history(updater1, bulk_creator1)

        # Second call - different error_code
        updater2 = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=SessionStatus.PREPARING,
                reason="second",
            ),
            conditions=[lambda: SessionRow.id.in_([test_session_id])],
        )
        bulk_creator2 = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=test_session_id,
                    phase="schedule",  # same phase
                    result=SchedulingResult.FAILURE,
                    message="Second",
                    to_status=SessionStatus.PREPARING,  # same to_status
                    error_code="ERROR_B",  # different error_code
                )
            ]
        )
        await db_source.update_with_history(updater2, bulk_creator2)

        # Verify - two separate records
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == test_session_id
            )
            records = (await db_sess.execute(history_stmt)).scalars().all()
            assert len(records) == 2
            error_codes = {r.error_code for r in records}
            assert error_codes == {"ERROR_A", "ERROR_B"}

    @pytest.mark.asyncio
    async def test_update_with_history_no_merge_different_to_status(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_session_id: SessionId,
    ) -> None:
        """Test that different to_status creates new record (no merge)."""
        db_source = ScheduleDBSource(db_with_cleanup)

        # First call
        updater1 = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=SessionStatus.PREPARING,
                reason="first",
            ),
            conditions=[lambda: SessionRow.id.in_([test_session_id])],
        )
        bulk_creator1 = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=test_session_id,
                    phase="schedule",
                    result=SchedulingResult.SUCCESS,
                    message="First",
                    to_status=SessionStatus.PREPARING,
                    error_code=None,
                )
            ]
        )
        await db_source.update_with_history(updater1, bulk_creator1)

        # Second call - different to_status
        updater2 = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=SessionStatus.SCHEDULED,
                reason="second",
            ),
            conditions=[lambda: SessionRow.id.in_([test_session_id])],
        )
        bulk_creator2 = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=test_session_id,
                    phase="schedule",  # same phase
                    result=SchedulingResult.SUCCESS,
                    message="Second",
                    to_status=SessionStatus.SCHEDULED,  # different to_status
                    error_code=None,  # same error_code (None)
                )
            ]
        )
        await db_source.update_with_history(updater2, bulk_creator2)

        # Verify - two separate records
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == test_session_id
            )
            records = (await db_sess.execute(history_stmt)).scalars().all()
            assert len(records) == 2
            to_statuses = {r.to_status for r in records}
            assert to_statuses == {str(SessionStatus.PREPARING), str(SessionStatus.SCHEDULED)}

    @pytest.mark.asyncio
    async def test_update_with_history_merge_multiple_sessions_batch(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_group_id: uuid.UUID,
    ) -> None:
        """Test merge logic works correctly with multiple sessions in batch."""
        # Create multiple sessions
        session_ids: list[SessionId] = []
        async with db_with_cleanup.begin_session() as db_sess:
            for _ in range(3):
                session_id = SessionId(uuid.uuid4())
                session_ids.append(session_id)
                session = SessionRow(
                    id=session_id,
                    creation_id=f"creation-{uuid.uuid4().hex[:8]}",
                    name=f"test-session-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INTERACTIVE,
                    domain_name=test_domain_name,
                    group_id=test_group_id,
                    status=SessionStatus.PREPARING,
                    status_info="preparing",
                    result=SessionResult.UNDEFINED,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    occupying_slots=ResourceSlot(),
                    requested_slots=ResourceSlot(),
                    vfolder_mounts={},
                    environ={},
                    priority=0,
                    created_at=datetime.now(tzutc()),
                    num_queries=0,
                    use_host_network=False,
                )
                db_sess.add(session)

        db_source = ScheduleDBSource(db_with_cleanup)

        # First batch call - creates 3 history records
        updater1 = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=SessionStatus.PREPARING,
                reason="batch-1",
            ),
            conditions=[lambda: SessionRow.id.in_(session_ids)],
        )
        bulk_creator1 = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=sid,
                    phase="schedule",
                    result=SchedulingResult.FAILURE,
                    message="First attempt",
                    to_status=SessionStatus.PREPARING,
                    error_code="RESOURCE_EXHAUSTED",
                )
                for sid in session_ids
            ]
        )
        await db_source.update_with_history(updater1, bulk_creator1)

        # Verify 3 records with attempts=1
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id.in_(session_ids)
            )
            records = (await db_sess.execute(history_stmt)).scalars().all()
            assert len(records) == 3
            assert all(r.attempts == 1 for r in records)

        # Second batch call - same phase+error_code+to_status -> all should merge
        updater2 = BatchUpdater(
            spec=SessionStatusBatchUpdaterSpec(
                to_status=SessionStatus.PREPARING,
                reason="batch-2",
            ),
            conditions=[lambda: SessionRow.id.in_(session_ids)],
        )
        bulk_creator2 = BulkCreator(
            specs=[
                SessionSchedulingHistoryCreatorSpec(
                    session_id=sid,
                    phase="schedule",
                    result=SchedulingResult.FAILURE,
                    message="Second attempt",
                    to_status=SessionStatus.PREPARING,
                    error_code="RESOURCE_EXHAUSTED",
                )
                for sid in session_ids
            ]
        )
        await db_source.update_with_history(updater2, bulk_creator2)

        # Verify still 3 records but all with attempts=2
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id.in_(session_ids)
            )
            records = (await db_sess.execute(history_stmt)).scalars().all()
            assert len(records) == 3
            assert all(r.attempts == 2 for r in records)
