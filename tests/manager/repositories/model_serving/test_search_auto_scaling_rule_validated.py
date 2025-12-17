"""
Tests for search_auto_scaling_rules_validated functionality.
Tests the repository layer for searching auto scaling rules with real database.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.types import ClusterMode, ResourceSlot, RuntimeVariant
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.data.model_serving.types import (
    EndpointAutoScalingRuleListResult,
    EndpointLifecycle,
)
from ai.backend.manager.models import (
    DomainRow,
    GroupRow,
    ImageRow,
    ProjectResourcePolicyRow,
    ScalingGroupRow,
    UserResourcePolicyRow,
    UserRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.endpoint import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointAutoScalingRuleRow,
    EndpointRow,
)
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository


class TestSearchAutoScalingRulesValidated:
    """Test cases for search_auto_scaling_rules_validated in ModelServingRepository."""

    # =========================================================================
    # Fixtures
    # =========================================================================

    @pytest.fixture
    async def test_scaling_group(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create a scaling group for testing"""
        name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        async with database_engine.begin_session() as db_sess:
            scaling_group = ScalingGroupRow(
                name=name,
                driver="static",
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(scaling_group)
            await db_sess.flush()

        yield name

        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(ScalingGroupRow).where(ScalingGroupRow.name == name))

    @pytest.fixture
    async def test_domain(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create a domain for testing"""
        name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with database_engine.begin_session() as db_sess:
            domain = DomainRow(name=name, total_resource_slots={})
            db_sess.add(domain)
            await db_sess.flush()

        yield name

        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(DomainRow).where(DomainRow.name == name))

    @pytest.fixture
    async def test_user_resource_policy(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create a user resource policy for testing"""
        name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        async with database_engine.begin_session() as db_sess:
            user_resource_policy = UserResourcePolicyRow(
                name=name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            db_sess.add(user_resource_policy)
            await db_sess.flush()

        yield name

        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(
                sa.delete(UserResourcePolicyRow).where(UserResourcePolicyRow.name == name)
            )

    @pytest.fixture
    async def test_project_resource_policy(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create a project resource policy for testing"""
        name = f"test-project-policy-{uuid.uuid4().hex[:8]}"
        async with database_engine.begin_session() as db_sess:
            project_resource_policy = ProjectResourcePolicyRow(
                name=name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            db_sess.add(project_resource_policy)
            await db_sess.flush()

        yield name

        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(
                sa.delete(ProjectResourcePolicyRow).where(ProjectResourcePolicyRow.name == name)
            )

    @pytest.fixture
    async def test_group_id(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_domain: str,
        test_project_resource_policy: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create a group for testing and return its ID"""
        group_id = uuid.uuid4()
        name = f"test-group-{uuid.uuid4().hex[:8]}"

        async with database_engine.begin_session() as db_sess:
            group = GroupRow(
                id=group_id,
                name=name,
                domain_name=test_domain,
                total_resource_slots={},
                resource_policy=test_project_resource_policy,
            )
            db_sess.add(group)
            await db_sess.flush()

        yield group_id

        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(GroupRow).where(GroupRow.id == group_id))

    @pytest.fixture
    async def test_user_id(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_domain: str,
        test_user_resource_policy: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create a user for testing and return its ID"""
        user_id = uuid.uuid4()
        email = f"test-{uuid.uuid4().hex[:8]}@test.com"
        username = f"testuser-{uuid.uuid4().hex[:8]}"

        async with database_engine.begin_session() as db_sess:
            password_info = PasswordInfo(
                password="test_password",
                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                rounds=1,
                salt_size=16,
            )
            user = UserRow(
                uuid=user_id,
                email=email,
                username=username,
                password=password_info,
                domain_name=test_domain,
                resource_policy=test_user_resource_policy,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
            )
            db_sess.add(user)
            await db_sess.flush()

        yield user_id

        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(UserRow).where(UserRow.uuid == user_id))

    @pytest.fixture
    async def test_container_registry_id(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create a container registry for testing and return its ID"""
        registry_id = uuid.uuid4()

        async with database_engine.begin_session() as db_sess:
            registry = ContainerRegistryRow(
                url="http://test-registry.local",
                registry_name=f"test-registry-{uuid.uuid4().hex[:8]}",
                type=ContainerRegistryType.DOCKER,
            )
            registry.id = registry_id
            db_sess.add(registry)
            await db_sess.flush()

        yield registry_id

        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(
                sa.delete(ContainerRegistryRow).where(ContainerRegistryRow.id == registry_id)
            )

    @pytest.fixture
    async def test_image_id(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_container_registry_id: uuid.UUID,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create an image for testing and return its ID"""
        image_id = uuid.uuid4()

        async with database_engine.begin_session() as db_sess:
            image = ImageRow(
                name=f"test-image-{uuid.uuid4().hex[:8]}",
                project=None,
                image=f"test-image-{uuid.uuid4().hex[:8]}",
                tag="latest",
                registry=f"test-registry-{uuid.uuid4().hex[:8]}",
                registry_id=test_container_registry_id,
                architecture="x86_64",
                config_digest="sha256:" + "a" * 64,
                size_bytes=1024,
                type=ImageType.COMPUTE,
                labels={},
                resources={"cpu": {"min": "1"}, "mem": {"min": "1g"}},
            )
            image.id = image_id
            db_sess.add(image)
            await db_sess.flush()

        yield image_id

        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(ImageRow).where(ImageRow.id == image_id))

    @pytest.fixture
    async def sample_endpoint_id(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_user_id: uuid.UUID,
        test_domain: str,
        test_group_id: uuid.UUID,
        test_scaling_group: str,
        test_image_id: uuid.UUID,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create a sample endpoint directly in DB and return its ID"""
        endpoint_id = uuid.uuid4()

        async with database_engine.begin_session() as db_sess:
            endpoint = EndpointRow(
                id=endpoint_id,
                name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                created_user=test_user_id,
                session_owner=test_user_id,
                domain=test_domain,
                project=test_group_id,
                resource_group=test_scaling_group,
                image=test_image_id,
                model=None,
                model_mount_destination="/models",
                runtime_variant=RuntimeVariant.CUSTOM,
                lifecycle_stage=EndpointLifecycle.CREATED,
                replicas=1,
                resource_slots=ResourceSlot({"cpu": "1", "mem": "1g"}),
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
            )
            db_sess.add(endpoint)
            await db_sess.flush()

        yield endpoint_id

        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(EndpointRow).where(EndpointRow.id == endpoint_id))

    @pytest.fixture
    async def sample_auto_scaling_rules(
        self,
        database_engine: ExtendedAsyncSAEngine,
        sample_endpoint_id: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create multiple sample auto scaling rules for testing"""
        rule_ids: list[uuid.UUID] = []
        metric_names = ["cpu_util", "memory_util", "gpu_util", "request_rate", "latency"]

        async with database_engine.begin_session() as db_sess:
            for i, metric_name in enumerate(metric_names):
                rule_id = uuid.uuid4()
                rule = EndpointAutoScalingRuleRow(
                    id=rule_id,
                    endpoint=sample_endpoint_id,
                    metric_source=AutoScalingMetricSource.KERNEL,
                    metric_name=metric_name,
                    threshold=Decimal(str(50.0 + i * 10)),
                    comparator=AutoScalingMetricComparator.GREATER_THAN,
                    step_size=1 + i,
                    cooldown_seconds=300 + i * 60,
                    min_replicas=1,
                    max_replicas=10 + i,
                    created_at=datetime.now(timezone.utc),
                )
                db_sess.add(rule)
                rule_ids.append(rule_id)
            await db_sess.flush()

        yield rule_ids

        async with database_engine.begin_session() as db_sess:
            for rule_id in rule_ids:
                await db_sess.execute(
                    sa.delete(EndpointAutoScalingRuleRow).where(
                        EndpointAutoScalingRuleRow.id == rule_id
                    )
                )

    @pytest.fixture
    async def sample_rules_for_pagination(
        self,
        database_engine: ExtendedAsyncSAEngine,
        sample_endpoint_id: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 25 sample auto scaling rules for pagination testing"""
        rule_ids: list[uuid.UUID] = []

        async with database_engine.begin_session() as db_sess:
            for i in range(25):
                rule_id = uuid.uuid4()
                rule = EndpointAutoScalingRuleRow(
                    id=rule_id,
                    endpoint=sample_endpoint_id,
                    metric_source=AutoScalingMetricSource.KERNEL,
                    metric_name=f"metric_{i:02d}",
                    threshold=Decimal(str(50.0 + i)),
                    comparator=AutoScalingMetricComparator.GREATER_THAN,
                    step_size=1,
                    cooldown_seconds=300,
                    min_replicas=1,
                    max_replicas=10,
                    created_at=datetime.now(timezone.utc),
                )
                db_sess.add(rule)
                rule_ids.append(rule_id)
            await db_sess.flush()

        yield rule_ids

        async with database_engine.begin_session() as db_sess:
            for rule_id in rule_ids:
                await db_sess.execute(
                    sa.delete(EndpointAutoScalingRuleRow).where(
                        EndpointAutoScalingRuleRow.id == rule_id
                    )
                )

    @pytest.fixture
    async def model_serving_repository(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> ModelServingRepository:
        """Create ModelServingRepository instance with real database"""
        return ModelServingRepository(db=database_engine)

    # =========================================================================
    # Tests - Basic Search
    # =========================================================================

    async def test_search_success(
        self,
        model_serving_repository: ModelServingRepository,
        sample_auto_scaling_rules: list[uuid.UUID],
    ) -> None:
        """Test successful search of auto scaling rules."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
        )

        assert result is not None
        assert isinstance(result, EndpointAutoScalingRuleListResult)
        assert len(result.items) == len(sample_auto_scaling_rules)
        assert result.total_count == len(sample_auto_scaling_rules)

    async def test_search_empty_result(
        self,
        model_serving_repository: ModelServingRepository,
        sample_endpoint_id: uuid.UUID,
    ) -> None:
        """Test search returns empty result when no rules exist."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
        )

        assert result is not None
        assert len(result.items) == 0
        assert result.total_count == 0

    # =========================================================================
    # Tests - Pagination
    # =========================================================================

    async def test_pagination_first_page(
        self,
        model_serving_repository: ModelServingRepository,
        sample_rules_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test first page of offset-based pagination."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
        )

        assert len(result.items) == 10
        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is False

    async def test_pagination_second_page(
        self,
        model_serving_repository: ModelServingRepository,
        sample_rules_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test second page of offset-based pagination."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )

        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
        )

        assert len(result.items) == 10
        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True

    async def test_pagination_last_page(
        self,
        model_serving_repository: ModelServingRepository,
        sample_rules_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test last page of offset-based pagination with partial results."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=20),
            conditions=[],
            orders=[],
        )

        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
        )

        assert len(result.items) == 5
        assert result.total_count == 25
        assert result.has_next_page is False
        assert result.has_previous_page is True

    # =========================================================================
    # Tests - Ordering
    # =========================================================================

    async def test_order_by_threshold_ascending(
        self,
        model_serving_repository: ModelServingRepository,
        sample_auto_scaling_rules: list[uuid.UUID],
    ) -> None:
        """Test searching rules ordered by threshold ascending."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[EndpointAutoScalingRuleRow.threshold.asc()],
        )

        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
        )

        thresholds = [float(item.threshold) for item in result.items]
        assert thresholds == sorted(thresholds)

    async def test_order_by_metric_name_descending(
        self,
        model_serving_repository: ModelServingRepository,
        sample_auto_scaling_rules: list[uuid.UUID],
    ) -> None:
        """Test searching rules ordered by metric_name descending."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[EndpointAutoScalingRuleRow.metric_name.desc()],
        )

        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
        )

        metric_names = [item.metric_name for item in result.items]
        assert metric_names == sorted(metric_names, reverse=True)
