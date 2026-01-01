"""
Tests for NotificationRepository query options (conditions and orders).
Tests the filter and ordering functionality with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta

import pytest
import sqlalchemy as sa

from ai.backend.common.types import BinarySize
from ai.backend.manager.data.notification import NotificationChannelType, NotificationRuleType
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.notification import (
    NotificationChannelRow,
    NotificationRuleRow,
    WebhookConfig,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
)
from ai.backend.manager.repositories.notification import NotificationRepository
from ai.backend.manager.repositories.notification.options import (
    NotificationChannelConditions,
    NotificationChannelOrders,
    NotificationRuleConditions,
    NotificationRuleOrders,
)
from ai.backend.testutils.db import with_tables


class TestNotificationOptions:
    """Test cases for notification query conditions and orders"""

    # Fixtures

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                NotificationChannelRow,
                NotificationRuleRow,
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
                description="Test domain for notification",
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
                max_quota_scope_size=BinarySize.from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_user(
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
    def notification_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> NotificationRepository:
        """Create NotificationRepository instance with database"""
        return NotificationRepository(db=db_with_cleanup)

    @pytest.fixture
    async def sample_channels_for_filter(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Create sample channels with various names and types for filter testing"""
        channel_ids: list[uuid.UUID] = []
        async with db_with_cleanup.begin_session() as db_sess:
            channels_data = [
                ("Test Channel", NotificationChannelType.WEBHOOK, True),
                ("test channel", NotificationChannelType.WEBHOOK, True),
                ("Production Alert", NotificationChannelType.WEBHOOK, True),
                ("Dev Notification", NotificationChannelType.WEBHOOK, False),
                ("ALERT System", NotificationChannelType.WEBHOOK, True),
            ]

            for name, channel_type, enabled in channels_data:
                channel_id = uuid.uuid4()
                config = WebhookConfig(url=f"https://example.com/webhook/{channel_id}")
                channel = NotificationChannelRow(
                    id=channel_id,
                    name=name,
                    description=None,
                    channel_type=channel_type,
                    config=config.model_dump(),
                    enabled=enabled,
                    created_by=test_user,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db_sess.add(channel)
                channel_ids.append(channel_id)
            await db_sess.commit()

        return channel_ids

    @pytest.fixture
    async def sample_channels_for_order(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Create sample channels with different timestamps for order testing"""
        channel_ids: list[uuid.UUID] = []
        base_time = datetime.now()

        async with db_with_cleanup.begin_session() as db_sess:
            channels_data = [
                ("Zebra Channel", base_time - timedelta(days=3), base_time - timedelta(hours=1)),
                ("Alpha Channel", base_time - timedelta(days=2), base_time - timedelta(hours=2)),
                ("Beta Channel", base_time - timedelta(days=1), base_time - timedelta(hours=3)),
            ]

            for name, created_at, updated_at in channels_data:
                channel_id = uuid.uuid4()
                config = WebhookConfig(url=f"https://example.com/webhook/{channel_id}")
                channel = NotificationChannelRow(
                    id=channel_id,
                    name=name,
                    description=None,
                    channel_type=NotificationChannelType.WEBHOOK,
                    config=config.model_dump(),
                    enabled=True,
                    created_by=test_user,
                    created_at=created_at,
                    updated_at=updated_at,
                )
                db_sess.add(channel)
                channel_ids.append(channel_id)
            await db_sess.commit()

        return channel_ids

    @pytest.fixture
    async def sample_channel_for_rules(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> uuid.UUID:
        """Create a single channel for rule testing"""
        channel_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            config = WebhookConfig(url="https://example.com/webhook")
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
            db_sess.add(channel)
            await db_sess.commit()

        return channel_id

    @pytest.fixture
    async def sample_rules_for_filter(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
        sample_channel_for_rules: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Create sample rules with various names and types for filter testing"""
        rule_ids: list[uuid.UUID] = []
        async with db_with_cleanup.begin_session() as db_sess:
            rules_data = [
                ("Test Rule", NotificationRuleType.SESSION_STARTED, True),
                ("test rule", NotificationRuleType.SESSION_TERMINATED, True),
                ("Production Alert", NotificationRuleType.SESSION_STARTED, True),
                ("Dev Notification", NotificationRuleType.SESSION_TERMINATED, False),
                ("ALERT System", NotificationRuleType.SESSION_STARTED, True),
            ]

            for name, rule_type, enabled in rules_data:
                rule_id = uuid.uuid4()
                rule = NotificationRuleRow(
                    id=rule_id,
                    name=name,
                    description=None,
                    rule_type=rule_type,
                    channel_id=sample_channel_for_rules,
                    message_template="Test message",
                    enabled=enabled,
                    created_by=test_user,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db_sess.add(rule)
                rule_ids.append(rule_id)
            await db_sess.commit()

        return rule_ids

    @pytest.fixture
    async def sample_rules_for_order(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
        sample_channel_for_rules: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Create sample rules with different timestamps for order testing"""
        rule_ids: list[uuid.UUID] = []
        base_time = datetime.now()

        async with db_with_cleanup.begin_session() as db_sess:
            rules_data = [
                ("Zebra Rule", base_time - timedelta(days=3), base_time - timedelta(hours=1)),
                ("Alpha Rule", base_time - timedelta(days=2), base_time - timedelta(hours=2)),
                ("Beta Rule", base_time - timedelta(days=1), base_time - timedelta(hours=3)),
            ]

            for name, created_at, updated_at in rules_data:
                rule_id = uuid.uuid4()
                rule = NotificationRuleRow(
                    id=rule_id,
                    name=name,
                    description=None,
                    rule_type=NotificationRuleType.SESSION_STARTED,
                    channel_id=sample_channel_for_rules,
                    message_template="Test message",
                    enabled=True,
                    created_by=test_user,
                    created_at=created_at,
                    updated_at=updated_at,
                )
                db_sess.add(rule)
                rule_ids.append(rule_id)
            await db_sess.commit()

        return rule_ids

    # NotificationChannelConditions Tests

    @pytest.mark.asyncio
    async def test_channel_by_name_contains_case_sensitive(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_filter: list[uuid.UUID],
    ) -> None:
        """Test case-sensitive name contains filter"""
        # sample_channels_for_filter creates channels with various names
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[
                NotificationChannelConditions.by_name_contains("Test", case_insensitive=False)
            ],
            orders=[],
        )
        channels = await notification_repository.search_channels(querier=querier)

        # Should match "Test Channel" only, not "test channel"
        assert len(channels.items) == 1
        assert channels.items[0].name == "Test Channel"

    @pytest.mark.asyncio
    async def test_channel_by_name_contains_case_insensitive(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_filter: list[uuid.UUID],
    ) -> None:
        """Test case-insensitive name contains filter"""
        # sample_channels_for_filter creates channels with various names
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[
                NotificationChannelConditions.by_name_contains("test", case_insensitive=True)
            ],
            orders=[],
        )
        channels = await notification_repository.search_channels(querier=querier)

        # Should match both "Test Channel" and "test channel"
        assert len(channels.items) == 2
        names = {ch.name for ch in channels.items}
        assert names == {"Test Channel", "test channel"}

    @pytest.mark.asyncio
    async def test_channel_by_name_equals_case_sensitive(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_filter: list[uuid.UUID],
    ) -> None:
        """Test case-sensitive name equals filter"""
        # sample_channels_for_filter creates channels with various names
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[
                NotificationChannelConditions.by_name_equals("Test Channel", case_insensitive=False)
            ],
            orders=[],
        )
        channels = await notification_repository.search_channels(querier=querier)

        # Should match exactly "Test Channel"
        assert len(channels.items) == 1
        assert channels.items[0].name == "Test Channel"

    @pytest.mark.asyncio
    async def test_channel_by_name_equals_case_insensitive(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_filter: list[uuid.UUID],
    ) -> None:
        """Test case-insensitive name equals filter"""
        # sample_channels_for_filter creates channels with various names
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[
                NotificationChannelConditions.by_name_equals("test channel", case_insensitive=True)
            ],
            orders=[],
        )
        channels = await notification_repository.search_channels(querier=querier)

        # Should match both "Test Channel" and "test channel"
        assert len(channels.items) == 2
        names = {ch.name for ch in channels.items}
        assert names == {"Test Channel", "test channel"}

    @pytest.mark.asyncio
    async def test_channel_by_channel_types(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_filter: list[uuid.UUID],
    ) -> None:
        """Test filter by channel types"""
        # sample_channels_for_filter creates all WEBHOOK type channels
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[
                NotificationChannelConditions.by_channel_types([NotificationChannelType.WEBHOOK])
            ],
            orders=[],
        )
        channels = await notification_repository.search_channels(querier=querier)

        # Should match all 5 channels
        assert len(channels.items) == 5
        assert all(ch.channel_type == NotificationChannelType.WEBHOOK for ch in channels.items)

    @pytest.mark.asyncio
    async def test_channel_by_enabled_true(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_filter: list[uuid.UUID],
    ) -> None:
        """Test filter by enabled=True"""
        # sample_channels_for_filter creates 4 enabled and 1 disabled
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[NotificationChannelConditions.by_enabled(True)],
            orders=[],
        )
        channels = await notification_repository.search_channels(querier=querier)

        assert len(channels.items) == 4
        assert all(ch.enabled for ch in channels.items)

    @pytest.mark.asyncio
    async def test_channel_by_enabled_false(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_filter: list[uuid.UUID],
    ) -> None:
        """Test filter by enabled=False"""
        # sample_channels_for_filter creates 4 enabled and 1 disabled
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[NotificationChannelConditions.by_enabled(False)],
            orders=[],
        )
        channels = await notification_repository.search_channels(querier=querier)

        assert len(channels.items) == 1
        assert not channels.items[0].enabled
        assert channels.items[0].name == "Dev Notification"

    # NotificationChannelOrders Tests

    @pytest.mark.asyncio
    async def test_channel_order_by_name_ascending(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_order: list[uuid.UUID],
    ) -> None:
        """Test ordering by name ascending (A-Z)"""
        # sample_channels_for_order creates: Zebra, Alpha, Beta
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[NotificationChannelOrders.name(ascending=True)],
        )
        channels = await notification_repository.search_channels(querier=querier)

        assert len(channels.items) == 3
        assert channels.items[0].name == "Alpha Channel"
        assert channels.items[1].name == "Beta Channel"
        assert channels.items[2].name == "Zebra Channel"

    @pytest.mark.asyncio
    async def test_channel_order_by_name_descending(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_order: list[uuid.UUID],
    ) -> None:
        """Test ordering by name descending (Z-A)"""
        # sample_channels_for_order creates: Zebra, Alpha, Beta
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[NotificationChannelOrders.name(ascending=False)],
        )
        channels = await notification_repository.search_channels(querier=querier)

        assert len(channels.items) == 3
        assert channels.items[0].name == "Zebra Channel"
        assert channels.items[1].name == "Beta Channel"
        assert channels.items[2].name == "Alpha Channel"

    @pytest.mark.asyncio
    async def test_channel_order_by_created_at_ascending(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_order: list[uuid.UUID],
    ) -> None:
        """Test ordering by created_at ascending (oldest first)"""
        # sample_channels_for_order creates with different created_at timestamps
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[NotificationChannelOrders.created_at(ascending=True)],
        )
        channels = await notification_repository.search_channels(querier=querier)

        assert len(channels.items) == 3
        # Oldest to newest
        assert channels.items[0].name == "Zebra Channel"
        assert channels.items[1].name == "Alpha Channel"
        assert channels.items[2].name == "Beta Channel"

    @pytest.mark.asyncio
    async def test_channel_order_by_created_at_descending(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_order: list[uuid.UUID],
    ) -> None:
        """Test ordering by created_at descending (newest first)"""
        # sample_channels_for_order creates with different created_at timestamps
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[NotificationChannelOrders.created_at(ascending=False)],
        )
        channels = await notification_repository.search_channels(querier=querier)

        assert len(channels.items) == 3
        # Newest to oldest
        assert channels.items[0].name == "Beta Channel"
        assert channels.items[1].name == "Alpha Channel"
        assert channels.items[2].name == "Zebra Channel"

    @pytest.mark.asyncio
    async def test_channel_order_by_updated_at_ascending(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_order: list[uuid.UUID],
    ) -> None:
        """Test ordering by updated_at ascending"""
        # sample_channels_for_order creates with different updated_at timestamps
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[NotificationChannelOrders.updated_at(ascending=True)],
        )
        channels = await notification_repository.search_channels(querier=querier)

        assert len(channels.items) == 3
        # Oldest update to newest update
        assert channels.items[0].name == "Beta Channel"
        assert channels.items[1].name == "Alpha Channel"
        assert channels.items[2].name == "Zebra Channel"

    @pytest.mark.asyncio
    async def test_channel_order_by_updated_at_descending(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_order: list[uuid.UUID],
    ) -> None:
        """Test ordering by updated_at descending"""
        # sample_channels_for_order creates with different updated_at timestamps
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[NotificationChannelOrders.updated_at(ascending=False)],
        )
        channels = await notification_repository.search_channels(querier=querier)

        assert len(channels.items) == 3
        # Newest update to oldest update
        assert channels.items[0].name == "Zebra Channel"
        assert channels.items[1].name == "Alpha Channel"
        assert channels.items[2].name == "Beta Channel"

    # NotificationRuleConditions Tests

    @pytest.mark.asyncio
    async def test_rule_by_name_contains_case_sensitive(
        self,
        notification_repository: NotificationRepository,
        sample_rules_for_filter: list[uuid.UUID],
    ) -> None:
        """Test case-sensitive name contains filter for rules"""
        # sample_rules_for_filter creates rules with various names
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[
                NotificationRuleConditions.by_name_contains("Test", case_insensitive=False)
            ],
            orders=[],
        )
        rules = await notification_repository.search_rules(querier=querier)

        # Should match "Test Rule" only, not "test rule"
        assert len(rules.items) == 1
        assert rules.items[0].name == "Test Rule"

    @pytest.mark.asyncio
    async def test_rule_by_name_contains_case_insensitive(
        self,
        notification_repository: NotificationRepository,
        sample_rules_for_filter: list[uuid.UUID],
    ) -> None:
        """Test case-insensitive name contains filter for rules"""
        # sample_rules_for_filter creates rules with various names
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[NotificationRuleConditions.by_name_contains("test", case_insensitive=True)],
            orders=[],
        )
        rules = await notification_repository.search_rules(querier=querier)

        # Should match both "Test Rule" and "test rule"
        assert len(rules.items) == 2
        names = {rule.name for rule in rules.items}
        assert names == {"Test Rule", "test rule"}

    @pytest.mark.asyncio
    async def test_rule_by_name_equals_case_sensitive(
        self,
        notification_repository: NotificationRepository,
        sample_rules_for_filter: list[uuid.UUID],
    ) -> None:
        """Test case-sensitive name equals filter for rules"""
        # sample_rules_for_filter creates rules with various names
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[
                NotificationRuleConditions.by_name_equals("Test Rule", case_insensitive=False)
            ],
            orders=[],
        )
        rules = await notification_repository.search_rules(querier=querier)

        # Should match exactly "Test Rule"
        assert len(rules.items) == 1
        assert rules.items[0].name == "Test Rule"

    @pytest.mark.asyncio
    async def test_rule_by_name_equals_case_insensitive(
        self,
        notification_repository: NotificationRepository,
        sample_rules_for_filter: list[uuid.UUID],
    ) -> None:
        """Test case-insensitive name equals filter for rules"""
        # sample_rules_for_filter creates rules with various names
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[
                NotificationRuleConditions.by_name_equals("test rule", case_insensitive=True)
            ],
            orders=[],
        )
        rules = await notification_repository.search_rules(querier=querier)

        # Should match both "Test Rule" and "test rule"
        assert len(rules.items) == 2
        names = {rule.name for rule in rules.items}
        assert names == {"Test Rule", "test rule"}

    @pytest.mark.asyncio
    async def test_rule_by_rule_types(
        self,
        notification_repository: NotificationRepository,
        sample_rules_for_filter: list[uuid.UUID],
    ) -> None:
        """Test filter by rule types"""
        # sample_rules_for_filter creates 3 SESSION_STARTED and 2 SESSION_TERMINATED
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[
                NotificationRuleConditions.by_rule_types([NotificationRuleType.SESSION_STARTED])
            ],
            orders=[],
        )
        rules = await notification_repository.search_rules(querier=querier)

        # Should match 3 SESSION_STARTED rules
        assert len(rules.items) == 3
        assert all(rule.rule_type == NotificationRuleType.SESSION_STARTED for rule in rules.items)

    @pytest.mark.asyncio
    async def test_rule_by_enabled_true(
        self,
        notification_repository: NotificationRepository,
        sample_rules_for_filter: list[uuid.UUID],
    ) -> None:
        """Test filter by enabled=True"""
        # sample_rules_for_filter creates 4 enabled and 1 disabled
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[NotificationRuleConditions.by_enabled(True)],
            orders=[],
        )
        rules = await notification_repository.search_rules(querier=querier)

        assert len(rules.items) == 4
        assert all(rule.enabled for rule in rules.items)

    @pytest.mark.asyncio
    async def test_rule_by_enabled_false(
        self,
        notification_repository: NotificationRepository,
        sample_rules_for_filter: list[uuid.UUID],
    ) -> None:
        """Test filter by enabled=False"""
        # sample_rules_for_filter creates 4 enabled and 1 disabled
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[NotificationRuleConditions.by_enabled(False)],
            orders=[],
        )
        rules = await notification_repository.search_rules(querier=querier)

        assert len(rules.items) == 1
        assert not rules.items[0].enabled
        assert rules.items[0].name == "Dev Notification"

    # NotificationRuleOrders Tests

    @pytest.mark.asyncio
    async def test_rule_order_by_name_ascending(
        self,
        notification_repository: NotificationRepository,
        sample_rules_for_order: list[uuid.UUID],
    ) -> None:
        """Test ordering by name ascending (A-Z)"""
        # sample_rules_for_order creates: Zebra, Alpha, Beta
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[NotificationRuleOrders.name(ascending=True)],
        )
        rules = await notification_repository.search_rules(querier=querier)

        assert len(rules.items) == 3
        assert rules.items[0].name == "Alpha Rule"
        assert rules.items[1].name == "Beta Rule"
        assert rules.items[2].name == "Zebra Rule"

    @pytest.mark.asyncio
    async def test_rule_order_by_name_descending(
        self,
        notification_repository: NotificationRepository,
        sample_rules_for_order: list[uuid.UUID],
    ) -> None:
        """Test ordering by name descending (Z-A)"""
        # sample_rules_for_order creates: Zebra, Alpha, Beta
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[NotificationRuleOrders.name(ascending=False)],
        )
        rules = await notification_repository.search_rules(querier=querier)

        assert len(rules.items) == 3
        assert rules.items[0].name == "Zebra Rule"
        assert rules.items[1].name == "Beta Rule"
        assert rules.items[2].name == "Alpha Rule"

    @pytest.mark.asyncio
    async def test_rule_order_by_created_at_ascending(
        self,
        notification_repository: NotificationRepository,
        sample_rules_for_order: list[uuid.UUID],
    ) -> None:
        """Test ordering by created_at ascending (oldest first)"""
        # sample_rules_for_order creates with different created_at timestamps
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[NotificationRuleOrders.created_at(ascending=True)],
        )
        rules = await notification_repository.search_rules(querier=querier)

        assert len(rules.items) == 3
        # Oldest to newest
        assert rules.items[0].name == "Zebra Rule"
        assert rules.items[1].name == "Alpha Rule"
        assert rules.items[2].name == "Beta Rule"

    @pytest.mark.asyncio
    async def test_rule_order_by_created_at_descending(
        self,
        notification_repository: NotificationRepository,
        sample_rules_for_order: list[uuid.UUID],
    ) -> None:
        """Test ordering by created_at descending (newest first)"""
        # sample_rules_for_order creates with different created_at timestamps
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[NotificationRuleOrders.created_at(ascending=False)],
        )
        rules = await notification_repository.search_rules(querier=querier)

        assert len(rules.items) == 3
        # Newest to oldest
        assert rules.items[0].name == "Beta Rule"
        assert rules.items[1].name == "Alpha Rule"
        assert rules.items[2].name == "Zebra Rule"

    @pytest.mark.asyncio
    async def test_rule_order_by_updated_at_ascending(
        self,
        notification_repository: NotificationRepository,
        sample_rules_for_order: list[uuid.UUID],
    ) -> None:
        """Test ordering by updated_at ascending"""
        # sample_rules_for_order creates with different updated_at timestamps
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[NotificationRuleOrders.updated_at(ascending=True)],
        )
        rules = await notification_repository.search_rules(querier=querier)

        assert len(rules.items) == 3
        # Oldest update to newest update
        assert rules.items[0].name == "Beta Rule"
        assert rules.items[1].name == "Alpha Rule"
        assert rules.items[2].name == "Zebra Rule"

    @pytest.mark.asyncio
    async def test_rule_order_by_updated_at_descending(
        self,
        notification_repository: NotificationRepository,
        sample_rules_for_order: list[uuid.UUID],
    ) -> None:
        """Test ordering by updated_at descending"""
        # sample_rules_for_order creates with different updated_at timestamps
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[NotificationRuleOrders.updated_at(ascending=False)],
        )
        rules = await notification_repository.search_rules(querier=querier)

        assert len(rules.items) == 3
        # Newest update to oldest update
        assert rules.items[0].name == "Zebra Rule"
        assert rules.items[1].name == "Alpha Rule"
        assert rules.items[2].name == "Beta Rule"

    @pytest.mark.asyncio
    async def test_channel_no_match_returns_empty(
        self,
        notification_repository: NotificationRepository,
        sample_channels_for_filter: list[uuid.UUID],
    ) -> None:
        """Test that searching for non-existent channel returns empty with total_count=0"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[NotificationChannelConditions.by_name_equals("NonexistentChannelName")],
            orders=[],
        )
        channels = await notification_repository.search_channels(querier=querier)

        # WHERE condition matches nothing
        assert len(channels.items) == 0
        assert channels.total_count == 0

    @pytest.mark.asyncio
    async def test_rule_no_match_returns_empty(
        self,
        notification_repository: NotificationRepository,
        sample_rules_for_filter: list[uuid.UUID],
    ) -> None:
        """Test that searching for non-existent rule returns empty with total_count=0"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[NotificationRuleConditions.by_name_equals("NonexistentRuleName")],
            orders=[],
        )
        rules = await notification_repository.search_rules(querier=querier)

        # WHERE condition matches nothing
        assert len(rules.items) == 0
        assert rules.total_count == 0


class TestNotificationCursorPagination:
    """Test cases for cursor-based pagination with notification channels.

    Validates that forward/backward cursor pagination works correctly:
    - Forward (first/after): DESC order, newest first, next page shows older items
    - Backward (last/before): ASC order, fetches older items (reversed for display)
    """

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                NotificationChannelRow,
                NotificationRuleRow,
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
                description="Test domain for cursor pagination",
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
                max_quota_scope_size=BinarySize.from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_user(
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
    def notification_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> NotificationRepository:
        """Create NotificationRepository instance with database"""
        return NotificationRepository(db=db_with_cleanup)

    @pytest.fixture
    async def channels_for_cursor_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Create 5 channels with distinct created_at times for cursor pagination testing.

        Created order (oldest to newest): Channel-1, Channel-2, Channel-3, Channel-4, Channel-5
        """
        channel_ids: list[uuid.UUID] = []
        base_time = datetime.now()

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(1, 6):
                channel_id = uuid.uuid4()
                config = WebhookConfig(url=f"https://example.com/webhook/{i}")
                channel = NotificationChannelRow(
                    id=channel_id,
                    name=f"Channel-{i}",
                    description=None,
                    channel_type=NotificationChannelType.WEBHOOK,
                    config=config.model_dump(),
                    enabled=True,
                    created_by=test_user,
                    created_at=base_time
                    - timedelta(days=5 - i),  # Channel-1 oldest, Channel-5 newest
                    updated_at=base_time,
                )
                db_sess.add(channel)
                channel_ids.append(channel_id)
            await db_sess.commit()

        return channel_ids

    @pytest.mark.asyncio
    async def test_forward_pagination_first_page_shows_newest_first(
        self,
        notification_repository: NotificationRepository,
        channels_for_cursor_pagination: list[uuid.UUID],
    ) -> None:
        """Test forward pagination first page shows newest items first (DESC order).

        With 5 channels (oldest to newest: Channel-1 to Channel-5),
        first page with first=3 should return: Channel-5, Channel-4, Channel-3
        """
        querier = BatchQuerier(
            pagination=CursorForwardPagination(
                first=3,
                cursor_order=NotificationChannelOrders.created_at(ascending=False),  # DESC
                cursor_condition=None,  # No cursor = first page
            ),
        )
        result = await notification_repository.search_channels(querier=querier)

        assert len(result.items) == 3
        # Should be newest first
        assert result.items[0].name == "Channel-5"
        assert result.items[1].name == "Channel-4"
        assert result.items[2].name == "Channel-3"
        assert result.has_previous_page is False  # First page
        assert result.has_next_page is True  # More items exist

    @pytest.mark.asyncio
    async def test_forward_pagination_with_cursor_shows_older_items(
        self,
        notification_repository: NotificationRepository,
        channels_for_cursor_pagination: list[uuid.UUID],
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test forward pagination with cursor shows older items (next page).

        After viewing Channel-5, Channel-4, Channel-3 (first page),
        using Channel-3's cursor should return: Channel-2, Channel-1
        """
        # First, get the cursor value (Channel-3's ID)
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            result = await db_sess.execute(
                sa.select(NotificationChannelRow.id).where(
                    NotificationChannelRow.name == "Channel-3"
                )
            )
            channel_3_id = result.scalar_one()

        # Forward cursor condition: created_at < cursor's created_at
        cursor_condition = NotificationChannelConditions.by_cursor_forward(str(channel_3_id))

        querier = BatchQuerier(
            pagination=CursorForwardPagination(
                first=3,
                cursor_order=NotificationChannelOrders.created_at(ascending=False),  # DESC
                cursor_condition=cursor_condition,
            ),
        )
        result = await notification_repository.search_channels(querier=querier)

        # Should return older items (Channel-2, Channel-1)
        assert len(result.items) == 2
        assert result.items[0].name == "Channel-2"
        assert result.items[1].name == "Channel-1"
        assert result.has_previous_page is True  # Has items before (cursor was provided)
        assert result.has_next_page is False  # No more items

    @pytest.mark.asyncio
    async def test_backward_pagination_last_page_fetches_oldest_first(
        self,
        notification_repository: NotificationRepository,
        channels_for_cursor_pagination: list[uuid.UUID],
    ) -> None:
        """Test backward pagination without cursor fetches from the end (oldest first in DB order).

        With 5 channels, last=3 without cursor should fetch the 3 newest items
        but in ASC order for DB query, then results need to be reversed for display.
        """
        querier = BatchQuerier(
            pagination=CursorBackwardPagination(
                last=3,
                cursor_order=NotificationChannelOrders.created_at(ascending=True),  # ASC
                cursor_condition=None,  # No cursor = last page
            ),
        )
        result = await notification_repository.search_channels(querier=querier)

        # Backward pagination returns in ascending order (oldest first in this slice)
        # These are the 3 oldest items: Channel-1, Channel-2, Channel-3
        assert len(result.items) == 3
        assert result.items[0].name == "Channel-1"
        assert result.items[1].name == "Channel-2"
        assert result.items[2].name == "Channel-3"
        assert result.has_previous_page is True  # More items exist before
        assert result.has_next_page is False  # No cursor = last page

    @pytest.mark.asyncio
    async def test_backward_pagination_with_cursor_shows_newer_items(
        self,
        notification_repository: NotificationRepository,
        channels_for_cursor_pagination: list[uuid.UUID],
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test backward pagination with cursor shows newer items (previous page).

        If we're at Channel-1, Channel-2, Channel-3 and go back (before Channel-3),
        we should get Channel-4, Channel-5 (items newer than the current view).
        """
        # Get the cursor value (Channel-3's ID)
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            result = await db_sess.execute(
                sa.select(NotificationChannelRow.id).where(
                    NotificationChannelRow.name == "Channel-3"
                )
            )
            channel_3_id = result.scalar_one()

        # Backward cursor condition: created_at > cursor's created_at
        cursor_condition = NotificationChannelConditions.by_cursor_backward(str(channel_3_id))

        querier = BatchQuerier(
            pagination=CursorBackwardPagination(
                last=3,
                cursor_order=NotificationChannelOrders.created_at(ascending=True),  # ASC
                cursor_condition=cursor_condition,
            ),
        )
        result = await notification_repository.search_channels(querier=querier)

        # Should return newer items (Channel-4, Channel-5) in ASC order
        assert len(result.items) == 2
        assert result.items[0].name == "Channel-4"
        assert result.items[1].name == "Channel-5"
        assert result.has_previous_page is False  # No more newer items
        assert result.has_next_page is True  # Has items after (cursor was provided)
