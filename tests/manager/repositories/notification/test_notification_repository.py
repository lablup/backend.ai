"""
Tests for NotificationRepository functionality.
Tests the repository layer with real database operations.
"""

import uuid
from datetime import datetime
from typing import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import BinarySize
from ai.backend.manager.data.notification import (
    NotificationChannelCreator,
    NotificationChannelModifier,
    NotificationRuleCreator,
    NotificationRuleModifier,
    NotificationRuleType,
)
from ai.backend.manager.errors.notification import (
    NotificationChannelNotFound,
    NotificationRuleNotFound,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.notification import (
    NotificationChannelRow,
    NotificationChannelType,
    NotificationRuleRow,
    WebhookConfig,
)
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import OffsetPagination, Querier
from ai.backend.manager.repositories.notification import NotificationRepository
from ai.backend.manager.repositories.notification.db_source import NotificationDBSource
from ai.backend.manager.repositories.notification.options import (
    NotificationChannelConditions,
    NotificationChannelOrders,
)


class TestNotificationRepository:
    """Test cases for NotificationRepository"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database engine that auto-cleans notification data after each test"""
        yield database_engine

        # Cleanup all notification data after test
        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(NotificationRuleRow))
            await db_sess.execute(sa.delete(NotificationChannelRow))

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test domain and return domain name"""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain for notification",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()

        try:
            yield domain_name
        finally:
            # Cleanup
            async with db_with_cleanup.begin_session() as db_sess:
                await db_sess.execute(sa.delete(DomainRow).where(DomainRow.name == domain_name))

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test resource policy and return policy name"""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

        try:
            yield policy_name
        finally:
            # Cleanup
            async with db_with_cleanup.begin_session() as db_sess:
                await db_sess.execute(
                    sa.delete(UserResourcePolicyRow).where(
                        UserResourcePolicyRow.name == policy_name
                    )
                )

    @pytest.fixture
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
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
            await db_sess.flush()

        try:
            yield user_uuid
        finally:
            # Cleanup
            async with db_with_cleanup.begin_session() as db_sess:
                await db_sess.execute(sa.delete(UserRow).where(UserRow.uuid == user_uuid))

    @pytest.fixture
    async def sample_channel_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create sample notification channel directly in DB and return its ID"""
        from datetime import datetime

        channel_id = uuid.uuid4()
        config = WebhookConfig(url="https://example.com/webhook", method="POST")

        async with db_with_cleanup.begin_session() as db_sess:
            channel = NotificationChannelRow(
                id=channel_id,
                name="Sample Channel",
                description="Sample channel for testing",
                channel_type=NotificationChannelType.WEBHOOK,
                config=config.model_dump(),
                enabled=True,
                created_by=test_user,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db_sess.add(channel)
            await db_sess.flush()

        yield channel_id

    @pytest.fixture
    async def sample_rule_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_channel_id: uuid.UUID,
        test_user: uuid.UUID,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create sample notification rule directly in DB and return its ID"""
        from datetime import datetime

        rule_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            rule = NotificationRuleRow(
                id=rule_id,
                name="Sample Rule",
                description="Sample rule for testing",
                rule_type="session.started",
                channel_id=sample_channel_id,
                message_template="Session {{ session_id }} started",
                enabled=True,
                created_by=test_user,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db_sess.add(rule)
            await db_sess.flush()

        yield rule_id

    @pytest.fixture
    async def sample_channels_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 25 sample channels for pagination testing"""
        channel_ids = []
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(25):
                channel_id = uuid.uuid4()
                config = WebhookConfig(url=f"https://example{i}.com/webhook")
                channel = NotificationChannelRow(
                    id=channel_id,
                    name=f"Channel {i:02d}",
                    description=None,
                    channel_type=NotificationChannelType.WEBHOOK,
                    config=config.model_dump(),
                    enabled=True,
                    created_by=test_user,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db_sess.add(channel)
                channel_ids.append(channel_id)
            await db_sess.flush()

        yield channel_ids

    @pytest.fixture
    async def sample_channels_small(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 5 sample channels for boundary testing"""
        channel_ids = []
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(5):
                channel_id = uuid.uuid4()
                config = WebhookConfig(url=f"https://example{i}.com/webhook")
                channel = NotificationChannelRow(
                    id=channel_id,
                    name=f"Channel {i}",
                    description=None,
                    channel_type=NotificationChannelType.WEBHOOK,
                    config=config.model_dump(),
                    enabled=True,
                    created_by=test_user,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db_sess.add(channel)
                channel_ids.append(channel_id)
            await db_sess.flush()

        yield channel_ids

    @pytest.fixture
    async def sample_channels_mixed_enabled(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 20 sample channels (10 enabled, 10 disabled) for filter testing"""
        channel_ids = []
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(20):
                channel_id = uuid.uuid4()
                config = WebhookConfig(url=f"https://example{i}.com/webhook")
                channel = NotificationChannelRow(
                    id=channel_id,
                    name=f"Channel {i:02d}",
                    description=None,
                    channel_type=NotificationChannelType.WEBHOOK,
                    config=config.model_dump(),
                    enabled=(i % 2 == 0),  # Even indexes enabled
                    created_by=test_user,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db_sess.add(channel)
                channel_ids.append(channel_id)
            await db_sess.flush()

        yield channel_ids

    @pytest.fixture
    async def sample_channels_medium(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 15 sample channels for no-pagination testing"""
        channel_ids = []
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(15):
                channel_id = uuid.uuid4()
                config = WebhookConfig(url=f"https://example{i}.com/webhook")
                channel = NotificationChannelRow(
                    id=channel_id,
                    name=f"Channel {i}",
                    description=None,
                    channel_type=NotificationChannelType.WEBHOOK,
                    config=config.model_dump(),
                    enabled=True,
                    created_by=test_user,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db_sess.add(channel)
                channel_ids.append(channel_id)
            await db_sess.flush()

        yield channel_ids

    @pytest.fixture
    async def notification_db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[NotificationDBSource, None]:
        """Create NotificationDBSource instance with real database"""
        db_source = NotificationDBSource(db=db_with_cleanup)
        yield db_source

    @pytest.fixture
    async def notification_repository(
        self,
        notification_db_source: NotificationDBSource,
    ) -> AsyncGenerator[NotificationRepository, None]:
        """Create NotificationRepository instance with DB source"""
        repo = NotificationRepository(db_source=notification_db_source)
        yield repo

    @pytest.mark.asyncio
    async def test_create_channel(
        self,
        notification_repository: NotificationRepository,
        test_user: uuid.UUID,
    ) -> None:
        """Test creating notification channel"""
        config = WebhookConfig(
            url="https://example.com/webhook",
            method="POST",
            headers={"Authorization": "Bearer token123"},
            timeout=30,
            success_status_codes=[200, 201, 202],
        )

        creator = NotificationChannelCreator(
            name="Test Webhook",
            channel_type=NotificationChannelType.WEBHOOK,
            config=config,
            created_by=test_user,
            description="Test webhook channel",
            enabled=True,
        )

        channel = await notification_repository.create_channel(creator)

        assert channel.name == "Test Webhook"
        assert channel.channel_type == NotificationChannelType.WEBHOOK
        assert channel.config.url == "https://example.com/webhook"
        assert channel.config.method == "POST"
        assert channel.config.timeout == 30
        assert channel.enabled is True
        assert channel.description == "Test webhook channel"

    @pytest.mark.asyncio
    async def test_get_channel_by_id(
        self,
        notification_repository: NotificationRepository,
        sample_channel_id: uuid.UUID,
    ) -> None:
        """Test retrieving channel by ID"""
        retrieved_channel = await notification_repository.get_channel_by_id(sample_channel_id)

        assert retrieved_channel is not None
        assert retrieved_channel.id == sample_channel_id
        assert retrieved_channel.name == "Sample Channel"

    @pytest.mark.asyncio
    async def test_update_channel(
        self,
        notification_repository: NotificationRepository,
        sample_channel_id: uuid.UUID,
    ) -> None:
        """Test updating notification channel"""
        from ai.backend.manager.types import OptionalState

        new_config = WebhookConfig(
            url="https://example.com/new-webhook",
            method="GET",
        )

        modifier = NotificationChannelModifier(
            name=OptionalState.update("Updated Name"),
            config=OptionalState.update(new_config),
            enabled=OptionalState.update(False),
        )

        updated_channel = await notification_repository.update_channel(
            channel_id=sample_channel_id,
            modifier=modifier,
        )

        assert updated_channel is not None
        assert updated_channel.name == "Updated Name"
        assert updated_channel.config.url == "https://example.com/new-webhook"
        assert updated_channel.config.method == "GET"
        assert updated_channel.enabled is False

    @pytest.mark.asyncio
    async def test_delete_channel(
        self,
        notification_repository: NotificationRepository,
        sample_channel_id: uuid.UUID,
    ) -> None:
        """Test deleting notification channel"""
        deleted = await notification_repository.delete_channel(sample_channel_id)
        assert deleted is True

        with pytest.raises(NotificationChannelNotFound):
            await notification_repository.get_channel_by_id(sample_channel_id)

    @pytest.mark.asyncio
    async def test_list_channels(
        self,
        notification_repository: NotificationRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> None:
        """Test listing all channels"""
        from datetime import datetime

        config = WebhookConfig(url="https://example.com/webhook")

        # Create channels directly in DB
        async with db_with_cleanup.begin_session() as db_sess:
            enabled_channel = NotificationChannelRow(
                id=uuid.uuid4(),
                name="Enabled Channel",
                description=None,
                channel_type=NotificationChannelType.WEBHOOK,
                config=config.model_dump(),
                enabled=True,
                created_by=test_user,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            disabled_channel = NotificationChannelRow(
                id=uuid.uuid4(),
                name="Disabled Channel",
                description=None,
                channel_type=NotificationChannelType.WEBHOOK,
                config=config.model_dump(),
                enabled=False,
                created_by=test_user,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db_sess.add(enabled_channel)
            db_sess.add(disabled_channel)
            await db_sess.flush()

        result = await notification_repository.search_channels()
        assert len(result.items) >= 2
        assert result.total_count >= 2

        enabled_querier = Querier(
            conditions=[NotificationChannelConditions.by_enabled(True)],
            orders=[],
        )
        enabled_result = await notification_repository.search_channels(querier=enabled_querier)
        assert all(ch.enabled for ch in enabled_result.items)

    @pytest.mark.asyncio
    async def test_create_rule(
        self,
        notification_repository: NotificationRepository,
        test_user: uuid.UUID,
    ) -> None:
        """Test creating notification rule"""
        config = WebhookConfig(url="https://example.com/webhook")

        channel_creator = NotificationChannelCreator(
            name="Test Channel",
            channel_type=NotificationChannelType.WEBHOOK,
            config=config,
            created_by=test_user,
        )

        channel = await notification_repository.create_channel(channel_creator)

        rule_creator = NotificationRuleCreator(
            name="Session Started Rule",
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=channel.id,
            message_template="Session {{ session_id }} started",
            created_by=test_user,
            description="Notify when session starts",
            enabled=True,
        )

        rule = await notification_repository.create_rule(rule_creator)

        assert rule.name == "Session Started Rule"
        assert rule.rule_type == NotificationRuleType.SESSION_STARTED
        assert rule.message_template == "Session {{ session_id }} started"
        assert rule.channel.id == channel.id
        assert rule.enabled is True

    @pytest.mark.asyncio
    async def test_get_matching_rules(
        self,
        notification_repository: NotificationRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_channel_id: uuid.UUID,
        test_user: uuid.UUID,
    ) -> None:
        """Test retrieving rules matching a rule type"""
        from datetime import datetime

        # Create rules directly in DB
        async with db_with_cleanup.begin_session() as db_sess:
            # Create matching enabled rule
            matching_rule = NotificationRuleRow(
                id=uuid.uuid4(),
                name="Session Started Rule",
                description=None,
                rule_type="session.started",
                channel_id=sample_channel_id,
                message_template="Session started",
                enabled=True,
                created_by=test_user,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            # Create non-matching rule
            non_matching_rule = NotificationRuleRow(
                id=uuid.uuid4(),
                name="Session Terminated Rule",
                description=None,
                rule_type="session.terminated",
                channel_id=sample_channel_id,
                message_template="Session terminated",
                enabled=True,
                created_by=test_user,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            # Create disabled matching rule
            disabled_rule = NotificationRuleRow(
                id=uuid.uuid4(),
                name="Disabled Rule",
                description=None,
                rule_type="session.started",
                channel_id=sample_channel_id,
                message_template="Disabled",
                enabled=False,
                created_by=test_user,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db_sess.add(matching_rule)
            db_sess.add(non_matching_rule)
            db_sess.add(disabled_rule)
            await db_sess.flush()

        matching_rules = await notification_repository.get_matching_rules(
            rule_type=NotificationRuleType.SESSION_STARTED,
            enabled_only=True,
        )

        # Since DB session persists data between tests, use >= instead of exact count
        assert len(matching_rules) >= 1
        assert all(r.rule_type == NotificationRuleType.SESSION_STARTED for r in matching_rules)
        assert all(r.enabled for r in matching_rules)

    @pytest.mark.asyncio
    async def test_update_rule(
        self,
        notification_repository: NotificationRepository,
        sample_rule_id: uuid.UUID,
    ) -> None:
        """Test updating notification rule"""
        from ai.backend.manager.types import OptionalState

        modifier = NotificationRuleModifier(
            name=OptionalState.update("Updated Rule"),
            message_template=OptionalState.update("Updated template: {{ session_id }}"),
            enabled=OptionalState.update(False),
        )

        updated_rule = await notification_repository.update_rule(
            rule_id=sample_rule_id,
            modifier=modifier,
        )

        assert updated_rule is not None
        assert updated_rule.name == "Updated Rule"
        assert updated_rule.message_template == "Updated template: {{ session_id }}"
        assert updated_rule.enabled is False

    @pytest.mark.asyncio
    async def test_delete_rule(
        self,
        notification_repository: NotificationRepository,
        sample_rule_id: uuid.UUID,
    ) -> None:
        """Test deleting notification rule"""
        deleted = await notification_repository.delete_rule(sample_rule_id)
        assert deleted is True

        with pytest.raises(NotificationRuleNotFound):
            await notification_repository.get_rule_by_id(sample_rule_id)

    @pytest.mark.asyncio
    async def test_list_rules(
        self,
        notification_repository: NotificationRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_channel_id: uuid.UUID,
        test_user: uuid.UUID,
    ) -> None:
        """Test listing notification rules with filters"""
        from datetime import datetime

        # Create rules directly in DB
        async with db_with_cleanup.begin_session() as db_sess:
            # Create session.started rule (enabled)
            rule1 = NotificationRuleRow(
                id=uuid.uuid4(),
                name="Session Started 1",
                description=None,
                rule_type="session.started",
                channel_id=sample_channel_id,
                message_template="Test",
                enabled=True,
                created_by=test_user,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            # Create another session.started rule (disabled)
            rule2 = NotificationRuleRow(
                id=uuid.uuid4(),
                name="Session Started 2",
                description=None,
                rule_type="session.started",
                channel_id=sample_channel_id,
                message_template="Test",
                enabled=False,
                created_by=test_user,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            # Create session.terminated rule (enabled)
            rule3 = NotificationRuleRow(
                id=uuid.uuid4(),
                name="Session Terminated",
                description=None,
                rule_type="session.terminated",
                channel_id=sample_channel_id,
                message_template="Test",
                enabled=True,
                created_by=test_user,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db_sess.add(rule1)
            db_sess.add(rule2)
            db_sess.add(rule3)
            await db_sess.flush()

        from ai.backend.manager.repositories.base import Querier
        from ai.backend.manager.repositories.notification.options import NotificationRuleConditions

        # List all rules
        all_result = await notification_repository.search_rules()
        assert len(all_result.items) >= 3
        assert all_result.total_count >= 3

        # List enabled rules only
        enabled_querier = Querier(
            conditions=[NotificationRuleConditions.by_enabled(True)],
            orders=[],
        )
        enabled_result = await notification_repository.search_rules(querier=enabled_querier)
        assert all(r.enabled for r in enabled_result.items)

        # List rules by rule_type
        started_querier = Querier(
            conditions=[
                NotificationRuleConditions.by_rule_types([NotificationRuleType.SESSION_STARTED])
            ],
            orders=[],
        )
        started_result = await notification_repository.search_rules(querier=started_querier)
        assert len(started_result.items) >= 2
        assert all(
            r.rule_type == NotificationRuleType.SESSION_STARTED for r in started_result.items
        )

    @pytest.mark.asyncio
    async def test_delete_channel_with_rules(
        self,
        notification_repository: NotificationRepository,
        test_user: uuid.UUID,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test deleting a channel that has associated rules"""
        from datetime import datetime

        config = WebhookConfig(url="https://example.com/webhook")
        channel_id = uuid.uuid4()
        rule_id = uuid.uuid4()

        # Create channel and rule directly in DB
        async with db_with_cleanup.begin_session() as db_sess:
            channel = NotificationChannelRow(
                id=channel_id,
                name="Test Channel",
                description=None,
                channel_type=NotificationChannelType.WEBHOOK,
                config=config.model_dump(),
                enabled=True,
                created_by=test_user,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            rule = NotificationRuleRow(
                id=rule_id,
                name="Test Rule",
                description=None,
                rule_type="session.started",
                channel_id=channel_id,
                message_template="Test",
                enabled=True,
                created_by=test_user,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db_sess.add(channel)
            db_sess.add(rule)
            await db_sess.flush()

        # Delete channel - without FK, this should succeed
        result = await notification_repository.delete_channel(channel_id)
        assert result is True

        # Verify channel is deleted
        with pytest.raises(NotificationChannelNotFound):
            await notification_repository.get_channel_by_id(channel_id)

    # Pagination Tests

    @pytest.mark.asyncio
    async def test_list_channels_offset_pagination_first_page(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test first page of offset-based pagination"""
        # sample_channels_for_pagination fixture creates 25 channels
        querier = Querier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )
        result = await notification_repository.search_channels(querier=querier)
        assert len(result.items) == 10
        assert result.total_count == 25

    @pytest.mark.asyncio
    async def test_list_channels_offset_pagination_second_page(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test second page of offset-based pagination"""
        # sample_channels_for_pagination fixture creates 25 channels
        querier = Querier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=10),
        )
        result = await notification_repository.search_channels(querier=querier)
        assert len(result.items) == 10
        assert result.total_count == 25

    @pytest.mark.asyncio
    async def test_list_channels_offset_pagination_last_page(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test last page of offset-based pagination with partial results"""
        # sample_channels_for_pagination fixture creates 25 channels
        querier = Querier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=20),
        )
        result = await notification_repository.search_channels(querier=querier)
        assert len(result.items) == 5
        assert result.total_count == 25

    @pytest.mark.asyncio
    async def test_list_channels_pagination_limit_exceeds_total(
        self,
        notification_repository: NotificationRepository,
        sample_channels_small: list[uuid.UUID],
    ) -> None:
        """Test pagination when limit exceeds total count"""
        # sample_channels_small fixture creates 5 channels
        querier = Querier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=100, offset=0),
        )
        result = await notification_repository.search_channels(querier=querier)
        assert len(result.items) == 5
        assert result.total_count == 5

    @pytest.mark.asyncio
    async def test_list_channels_pagination_offset_exceeds_total(
        self,
        notification_repository: NotificationRepository,
        sample_channels_small: list[uuid.UUID],
    ) -> None:
        """Test pagination when offset exceeds total count returns empty"""
        # sample_channels_small fixture creates 5 channels
        querier = Querier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=100),
        )
        result = await notification_repository.search_channels(querier=querier)
        assert len(result.items) == 0
        assert result.total_count == 5

    @pytest.mark.asyncio
    async def test_list_channels_pagination_with_filter_and_order(
        self,
        notification_repository: NotificationRepository,
        sample_channels_mixed_enabled: list[uuid.UUID],
    ) -> None:
        """Test pagination combined with filtering and ordering"""
        # sample_channels_mixed_enabled fixture creates 20 channels (10 enabled, 10 disabled)
        querier = Querier(
            conditions=[NotificationChannelConditions.by_enabled(True)],
            orders=[NotificationChannelOrders.name(ascending=True)],
            pagination=OffsetPagination(limit=5, offset=0),
        )
        result = await notification_repository.search_channels(querier=querier)
        assert len(result.items) == 5
        assert result.total_count == 10  # Only enabled channels
        assert all(c.enabled for c in result.items)
        # Verify ordering (Channel 00, 02, 04, 06, 08)
        assert result.items[0].name == "Channel 00"
        assert result.items[1].name == "Channel 02"

    @pytest.mark.asyncio
    async def test_list_channels_no_pagination(
        self,
        notification_repository: NotificationRepository,
        sample_channels_medium: list[uuid.UUID],
    ) -> None:
        """Test listing channels without pagination returns all items"""
        # sample_channels_medium fixture creates 15 channels
        querier = Querier(
            conditions=[],
            orders=[],
            pagination=None,
        )
        result = await notification_repository.search_channels(querier=querier)
        assert len(result.items) == 15
        assert result.total_count == 15
