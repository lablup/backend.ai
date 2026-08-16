"""
Tests for NotificationRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.notification import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookSpec,
)
from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.notification import (
    NotificationChannelRow,
    NotificationRuleRow,
)
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.notification import NotificationRepository
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFixtureData


class TestNotificationRepository:
    """Test cases for NotificationRepository"""

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
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ContainerRegistryRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                RuntimeVariantRow,
                DeploymentRevisionPresetRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                ReplicaGroupRow,
                RoutingRow,
                ResourcePresetRow,
                # RBAC association
                AssociationScopesEntitiesRow,
                # Test-specific rows
                NotificationChannelRow,
                NotificationRuleRow,
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
                description="Test domain for notification",
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
    async def test_user(
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
    async def sample_channel_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> uuid.UUID:
        """Create sample notification channel directly in DB and return its ID"""
        channel_id = uuid.uuid4()
        config = WebhookSpec(url="https://example.com/webhook", method="POST")

        async with db_with_cleanup.begin_session() as db_sess:
            channel = NotificationChannelRow(
                id=channel_id,
                name="Sample Channel",
                description="Sample channel for testing",
                channel_type=NotificationChannelType.WEBHOOK,
                config=config.model_dump(),
                enabled=True,
                created_by=test_user,
                created_at=datetime.now(tz=UTC),
                updated_at=datetime.now(tz=UTC),
            )
            db_sess.add(channel)
            await db_sess.commit()

        return channel_id

    @pytest.fixture
    async def sample_rule_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_channel_id: uuid.UUID,
        test_user: uuid.UUID,
    ) -> uuid.UUID:
        """Create sample notification rule directly in DB and return its ID"""
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
                created_at=datetime.now(tz=UTC),
                updated_at=datetime.now(tz=UTC),
            )
            db_sess.add(rule)
            await db_sess.commit()

        return rule_id

    @pytest.fixture
    async def sample_channels_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Create 25 sample channels for pagination testing"""
        channel_ids: list[uuid.UUID] = []
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(25):
                channel_id = uuid.uuid4()
                config = WebhookSpec(url=f"https://example{i}.com/webhook")
                channel = NotificationChannelRow(
                    id=channel_id,
                    name=f"Channel {i:02d}",
                    description=None,
                    channel_type=NotificationChannelType.WEBHOOK,
                    config=config.model_dump(),
                    enabled=True,
                    created_by=test_user,
                    created_at=datetime.now(tz=UTC),
                    updated_at=datetime.now(tz=UTC),
                )
                db_sess.add(channel)
                channel_ids.append(channel_id)
            await db_sess.commit()

        return channel_ids

    @pytest.fixture
    async def sample_channels_small(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Create 5 sample channels for boundary testing"""
        channel_ids: list[uuid.UUID] = []
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(5):
                channel_id = uuid.uuid4()
                config = WebhookSpec(url=f"https://example{i}.com/webhook")
                channel = NotificationChannelRow(
                    id=channel_id,
                    name=f"Channel {i}",
                    description=None,
                    channel_type=NotificationChannelType.WEBHOOK,
                    config=config.model_dump(),
                    enabled=True,
                    created_by=test_user,
                    created_at=datetime.now(tz=UTC),
                    updated_at=datetime.now(tz=UTC),
                )
                db_sess.add(channel)
                channel_ids.append(channel_id)
            await db_sess.commit()

        return channel_ids

    @pytest.fixture
    async def sample_channels_mixed_enabled(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Create 20 sample channels (10 enabled, 10 disabled) for filter testing"""
        channel_ids: list[uuid.UUID] = []
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(20):
                channel_id = uuid.uuid4()
                config = WebhookSpec(url=f"https://example{i}.com/webhook")
                channel = NotificationChannelRow(
                    id=channel_id,
                    name=f"Channel {i:02d}",
                    description=None,
                    channel_type=NotificationChannelType.WEBHOOK,
                    config=config.model_dump(),
                    enabled=(i % 2 == 0),  # Even indexes enabled
                    created_by=test_user,
                    created_at=datetime.now(tz=UTC),
                    updated_at=datetime.now(tz=UTC),
                )
                db_sess.add(channel)
                channel_ids.append(channel_id)
            await db_sess.commit()

        return channel_ids

    @pytest.fixture
    async def sample_channels_medium(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Create 15 sample channels for no-pagination testing"""
        channel_ids: list[uuid.UUID] = []
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(15):
                channel_id = uuid.uuid4()
                config = WebhookSpec(url=f"https://example{i}.com/webhook")
                channel = NotificationChannelRow(
                    id=channel_id,
                    name=f"Channel {i}",
                    description=None,
                    channel_type=NotificationChannelType.WEBHOOK,
                    config=config.model_dump(),
                    enabled=True,
                    created_by=test_user,
                    created_at=datetime.now(tz=UTC),
                    updated_at=datetime.now(tz=UTC),
                )
                db_sess.add(channel)
                channel_ids.append(channel_id)
            await db_sess.commit()

        return channel_ids

    @pytest.fixture
    def notification_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> NotificationRepository:
        """Create NotificationRepository instance with database"""
        return NotificationRepository(db=db_with_cleanup)

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

    async def test_get_matching_rules(
        self,
        notification_repository: NotificationRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_channel_id: uuid.UUID,
        test_user: uuid.UUID,
    ) -> None:
        """Test retrieving rules matching a rule type"""

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
                created_at=datetime.now(tz=UTC),
                updated_at=datetime.now(tz=UTC),
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
                created_at=datetime.now(tz=UTC),
                updated_at=datetime.now(tz=UTC),
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
                created_at=datetime.now(tz=UTC),
                updated_at=datetime.now(tz=UTC),
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
        assert all(m.rule.rule_type == NotificationRuleType.SESSION_STARTED for m in matching_rules)
        assert all(m.rule.enabled and m.channel.enabled for m in matching_rules)
