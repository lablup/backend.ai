"""Tests for ModelCardDBSource.search_in_project membership check.

Verifies that the ASE-based membership_check_query on
ProjectModelCardSearchScope correctly gates access:
- A user who IS a project member (via association_scopes_entities) can search.
- A user who is NOT a project member is rejected with GenericForbidden.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest

from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.model_card.db_source.db_source import ModelCardDBSource
from ai.backend.manager.repositories.model_card.types import ProjectModelCardSearchScope
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestSearchInProjectMembership:
    """Verify ASE-based membership gating in search_in_project."""

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
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                VFolderRow,
                SessionRow,
                KernelRow,
                ModelCardRow,
                AssociationScopesEntitiesRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainRow:
        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=f"test-domain-{uuid.uuid4().hex[:8]}",
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()
        return domain

    @pytest.fixture
    async def test_user_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> UserResourcePolicyRow:
        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=f"test-user-policy-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=10,
                max_quota_scope_size=10 * (1024**3),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()
        return policy

    @pytest.fixture
    async def test_project_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ProjectResourcePolicyRow:
        async with db_with_cleanup.begin_session() as db_sess:
            policy = ProjectResourcePolicyRow(
                name=f"test-proj-policy-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=10,
                max_quota_scope_size=100 * (1024**3),
                max_network_count=5,
            )
            db_sess.add(policy)
            await db_sess.flush()
        return policy

    @pytest.fixture
    async def test_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainRow,
        test_project_resource_policy: ProjectResourcePolicyRow,
    ) -> GroupRow:
        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=uuid.uuid4(),
                name=f"test-project-{uuid.uuid4().hex[:8]}",
                description="Test project",
                is_active=True,
                domain_name=test_domain.name,
                resource_policy=test_project_resource_policy.name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
            )
            db_sess.add(group)
            await db_sess.flush()
        return group

    @pytest.fixture
    async def member_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainRow,
        test_user_resource_policy: UserResourcePolicyRow,
        test_project: GroupRow,
    ) -> UserRow:
        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=uuid.uuid4(),
                username=f"member-{uuid.uuid4().hex[:8]}",
                email=f"member-{uuid.uuid4().hex[:8]}@example.com",
                password=PasswordInfo(
                    password="test_password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=100_000,
                    salt_size=32,
                ),
                need_password_change=False,
                full_name="Member User",
                domain_name=test_domain.name,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                status_info="active",
                resource_policy=test_user_resource_policy.name,
            )
            db_sess.add(user)
            await db_sess.flush()
            # Register as project member via ASE
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=str(test_project.id),
                    entity_type=EntityType.USER,
                    entity_id=str(user.uuid),
                )
            )
            await db_sess.flush()
        return user

    @pytest.fixture
    async def non_member_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainRow,
        test_user_resource_policy: UserResourcePolicyRow,
    ) -> UserRow:
        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=uuid.uuid4(),
                username=f"nonmember-{uuid.uuid4().hex[:8]}",
                email=f"nonmember-{uuid.uuid4().hex[:8]}@example.com",
                password=PasswordInfo(
                    password="test_password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=100_000,
                    salt_size=32,
                ),
                need_password_change=False,
                full_name="Non-Member User",
                domain_name=test_domain.name,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                status_info="active",
                resource_policy=test_user_resource_policy.name,
            )
            db_sess.add(user)
            await db_sess.flush()
        return user

    @pytest.fixture
    def db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ModelCardDBSource:
        return ModelCardDBSource(db_with_cleanup)

    async def test_member_can_search(
        self,
        db_source: ModelCardDBSource,
        test_project: GroupRow,
        member_user: UserRow,
    ) -> None:
        scope = ProjectModelCardSearchScope(
            project_id=test_project.id,
            user_id=member_user.uuid,
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        result = await db_source.search_in_project(querier, scope)
        assert result.items == []
        assert result.total_count == 0

    async def test_non_member_is_rejected(
        self,
        db_source: ModelCardDBSource,
        test_project: GroupRow,
        non_member_user: UserRow,
    ) -> None:
        scope = ProjectModelCardSearchScope(
            project_id=test_project.id,
            user_id=non_member_user.uuid,
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        with pytest.raises(GenericForbidden):
            await db_source.search_in_project(querier, scope)
