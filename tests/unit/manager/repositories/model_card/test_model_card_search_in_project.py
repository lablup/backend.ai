"""Tests for the project-scoped model card search.

``ProjectModelCardOperationScope`` bounds its rows through the virtual-scope chain,
so a card is returned only while it is enrolled in its project's virtual scope.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, ResourceSlot, VFolderUsageMode
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.model_card.scopes import ProjectModelCardOperationScope
from ai.backend.manager.models.model_card.searchers import ModelCardSearcher
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_scope import VirtualScopeSeeder


@dataclass
class TestData:
    project_a_id: ProjectID
    project_b_id: ProjectID
    card_a1_id: ModelCardID
    card_a2_id: ModelCardID
    card_a_unenrolled_id: ModelCardID
    card_b1_id: ModelCardID


class TestModelCardSearchInProject:
    """Tests for the project-scoped model card search."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                VirtualScopeRow,
                ScopeBindingRow,
                EntityMembershipRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
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
    def ops_provider(self, db_with_cleanup: ExtendedAsyncSAEngine) -> V2DBOpsProvider:
        return V2DBOpsProvider(db_with_cleanup)

    @pytest.fixture
    async def test_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[TestData, None]:
        """Project A holds two enrolled cards plus one whose virtual-scope membership
        was never written; project B holds one enrolled card."""
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        user_policy_name = f"test-upolicy-{uuid.uuid4().hex[:8]}"
        project_policy_name = f"test-ppolicy-{uuid.uuid4().hex[:8]}"
        user_id = uuid.uuid4()
        project_a_id = ProjectID(uuid.uuid4())
        project_b_id = ProjectID(uuid.uuid4())
        vfolder_id = VFolderUUID(uuid.uuid4())
        card_a1_id = ModelCardID(uuid.uuid4())
        card_a2_id = ModelCardID(uuid.uuid4())
        card_a_unenrolled_id = ModelCardID(uuid.uuid4())
        card_b1_id = ModelCardID(uuid.uuid4())

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name=user_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=10 * (1024**3),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=project_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=100 * (1024**3),
                    max_network_count=5,
                )
            )
            await db_sess.flush()

            db_sess.add(
                UserRow(
                    uuid=user_id,
                    username=f"test-user-{uuid.uuid4().hex[:8]}",
                    email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                    password=PasswordInfo(
                        password="test_password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1,
                        salt_size=16,
                    ),
                    need_password_change=False,
                    domain_id=domain_id,
                    domain_name=domain_name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    resource_policy=user_policy_name,
                )
            )
            await db_sess.flush()

            for project_id, project_name in [
                (project_a_id, f"project-a-{uuid.uuid4().hex[:8]}"),
                (project_b_id, f"project-b-{uuid.uuid4().hex[:8]}"),
            ]:
                db_sess.add(
                    ProjectRow(
                        id=project_id,
                        name=project_name,
                        domain_name=domain_name,
                        description="Test project",
                        is_active=True,
                        total_resource_slots=ResourceSlot(),
                        allowed_vfolder_hosts={},
                        resource_policy=project_policy_name,
                        type=ProjectType.MODEL_STORE,
                    )
                )
            await db_sess.flush()

            db_sess.add(
                VFolderRow(
                    id=vfolder_id,
                    name=f"test-vfolder-{uuid.uuid4().hex[:8]}",
                    host="local",
                    domain_name=domain_name,
                    usage_mode=VFolderUsageMode.MODEL,
                    quota_scope_id=QuotaScopeID(QuotaScopeType.USER, user_id),
                    user=user_id,
                )
            )
            await db_sess.flush()

            for card_id, project_id, card_name in [
                (card_a1_id, project_a_id, "card-a1"),
                (card_a2_id, project_a_id, "card-a2"),
                (card_a_unenrolled_id, project_a_id, "card-a-unenrolled"),
                (card_b1_id, project_b_id, "card-b1"),
            ]:
                db_sess.add(
                    ModelCardRow(
                        id=card_id,
                        name=card_name,
                        vfolder=vfolder_id,
                        domain=domain_name,
                        project=project_id,
                        creator=user_id,
                    )
                )
            await db_sess.flush()

            seeder = VirtualScopeSeeder()
            for card_id, project_id in [
                (card_a1_id, project_a_id),
                (card_a2_id, project_a_id),
                (card_b1_id, project_b_id),
            ]:
                await seeder.enroll_entity_in_scope(
                    db_sess, ScopeType.PROJECT, project_id, EntityType.MODEL_CARD, card_id
                )

        yield TestData(
            project_a_id=project_a_id,
            project_b_id=project_b_id,
            card_a1_id=card_a1_id,
            card_a2_id=card_a2_id,
            card_a_unenrolled_id=card_a_unenrolled_id,
            card_b1_id=card_b1_id,
        )

    @staticmethod
    async def _search(ops_provider: V2DBOpsProvider, project_id: ProjectID) -> list[uuid.UUID]:
        async with ops_provider.read_ops() as read_ops:
            result = await read_ops.search_with_scopes(
                [ProjectModelCardOperationScope(project_id=project_id)],
                ModelCardSearcher(pagination=OffsetPagination(limit=10, offset=0)),
            )
        return [item.id for item in result.items]

    async def test_returns_only_cards_in_target_project(
        self,
        ops_provider: V2DBOpsProvider,
        test_data: TestData,
    ) -> None:
        found = await self._search(ops_provider, test_data.project_a_id)
        assert set(found) == {test_data.card_a1_id, test_data.card_a2_id}

    async def test_does_not_return_cards_from_other_project(
        self,
        ops_provider: V2DBOpsProvider,
        test_data: TestData,
    ) -> None:
        found = await self._search(ops_provider, test_data.project_b_id)
        assert set(found) == {test_data.card_b1_id}

    async def test_card_without_membership_is_not_returned(
        self,
        ops_provider: V2DBOpsProvider,
        test_data: TestData,
    ) -> None:
        """A card row carrying the project column but no virtual-scope membership stays
        out, so a missed backfill cannot pass unnoticed."""
        found = await self._search(ops_provider, test_data.project_a_id)
        assert test_data.card_a_unenrolled_id not in found

    async def test_unknown_project_raises_project_not_found(
        self,
        ops_provider: V2DBOpsProvider,
        test_data: TestData,
    ) -> None:
        with pytest.raises(ProjectNotFound):
            await self._search(ops_provider, ProjectID(uuid.uuid4()))
