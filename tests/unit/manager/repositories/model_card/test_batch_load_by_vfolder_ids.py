"""Tests for ModelCardDBSource.batch_load_by_vfolder_ids.

Backs the GraphQL ``VFolderGQL.model_cards`` resolver via DataLoader. The
behavior matrix the test covers:

* a vfolder with no card maps to an empty list,
* a vfolder with one card maps to a single-element list,
* a vfolder with sibling cards maps to all of them, sorted most-recently
  created first, and
* the result list mirrors the input order.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest

from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, ResourceSlot, VFolderUsageMode
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.types import RBACElementRef, RBACElementType
from ai.backend.manager.models.agent import AgentRow
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
from ai.backend.manager.models.resource_slot.row import (
    ModelCardResourceRequirementRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.model_card.creators import ModelCardCreatorSpec
from ai.backend.manager.repositories.model_card.db_source.db_source import ModelCardDBSource
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestBatchLoadByVFolderIds:
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
                ImageRow,
                VFolderRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ModelCardRow,
                ModelCardResourceRequirementRow,
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
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainRow,
        test_user_resource_policy: UserResourcePolicyRow,
    ) -> UserRow:
        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=uuid.uuid4(),
                username=f"test-user-{uuid.uuid4().hex[:8]}",
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                password=PasswordInfo(
                    password="test_password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=100_000,
                    salt_size=32,
                ),
                need_password_change=False,
                full_name="Test User",
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
    async def test_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainRow,
        test_project_resource_policy: ProjectResourcePolicyRow,
    ) -> GroupRow:
        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=uuid.uuid4(),
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                description="Test group",
                is_active=True,
                domain_name=test_domain.name,
                resource_policy=test_project_resource_policy.name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
            )
            db_sess.add(group)
            await db_sess.flush()
        return group

    async def _make_vfolder(
        self,
        db: ExtendedAsyncSAEngine,
        test_domain: DomainRow,
        test_user: UserRow,
    ) -> VFolderRow:
        async with db.begin_session() as db_sess:
            vfolder = VFolderRow(
                id=uuid.uuid4(),
                host="local",
                name=f"test-vfolder-{uuid.uuid4().hex[:8]}",
                domain_name=test_domain.name,
                usage_mode=VFolderUsageMode.MODEL,
                quota_scope_id=QuotaScopeID(QuotaScopeType.USER, test_user.uuid),
                user=test_user.uuid,
            )
            db_sess.add(vfolder)
            await db_sess.flush()
        return vfolder

    @pytest.fixture
    def db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ModelCardDBSource:
        return ModelCardDBSource(db_with_cleanup)

    def _build_creator(
        self,
        *,
        test_domain: DomainRow,
        test_user: UserRow,
        test_group: GroupRow,
        vfolder: VFolderRow,
    ) -> RBACEntityCreator[ModelCardRow]:
        return RBACEntityCreator(
            spec=ModelCardCreatorSpec(
                name=f"test-model-{uuid.uuid4().hex[:8]}",
                vfolder_id=vfolder.id,
                domain=test_domain.name,
                project_id=test_group.id,
                creator_id=test_user.uuid,
                author=None,
                title=None,
                model_version=None,
                description=None,
                task=None,
                category=None,
                architecture=None,
                framework=[],
                label=[],
                license=None,
                min_resource=[],
                readme=None,
                access_level="internal",
            ),
            element_type=RBACElementType.MODEL_CARD,
            scope_ref=RBACElementRef(
                element_type=RBACElementType.PROJECT,
                element_id=str(test_group.id),
            ),
        )

    async def test_groups_cards_per_vfolder_in_input_order(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ModelCardDBSource,
        test_domain: DomainRow,
        test_user: UserRow,
        test_group: GroupRow,
    ) -> None:
        empty_vfolder = await self._make_vfolder(db_with_cleanup, test_domain, test_user)
        single_vfolder = await self._make_vfolder(db_with_cleanup, test_domain, test_user)
        sibling_vfolder = await self._make_vfolder(db_with_cleanup, test_domain, test_user)

        single_card = await db_source.create(
            self._build_creator(
                test_domain=test_domain,
                test_user=test_user,
                test_group=test_group,
                vfolder=single_vfolder,
            )
        )
        first_sibling = await db_source.create(
            self._build_creator(
                test_domain=test_domain,
                test_user=test_user,
                test_group=test_group,
                vfolder=sibling_vfolder,
            )
        )
        # ``created_at`` is timestamped server-side at second precision in some
        # environments. Sleep briefly so the second card is unambiguously newer
        # and the most-recent-first ordering is testable.
        await asyncio.sleep(0.01)
        second_sibling = await db_source.create(
            self._build_creator(
                test_domain=test_domain,
                test_user=test_user,
                test_group=test_group,
                vfolder=sibling_vfolder,
            )
        )

        result = await db_source.batch_load_by_vfolder_ids([
            VFolderUUID(empty_vfolder.id),
            VFolderUUID(single_vfolder.id),
            VFolderUUID(sibling_vfolder.id),
        ])

        assert len(result) == 3
        assert result[0] == []
        assert [card.id for card in result[1]] == [single_card.id]

        sibling_ids = [card.id for card in result[2]]
        assert set(sibling_ids) == {first_sibling.id, second_sibling.id}
        # The newer card appears first.
        assert sibling_ids[0] == second_sibling.id

    async def test_empty_input_returns_empty_list(
        self,
        db_source: ModelCardDBSource,
    ) -> None:
        assert await db_source.batch_load_by_vfolder_ids([]) == []

    async def test_unknown_vfolder_id_yields_empty_group(
        self,
        db_source: ModelCardDBSource,
    ) -> None:
        unknown_id = VFolderUUID(uuid.uuid4())
        result = await db_source.batch_load_by_vfolder_ids([unknown_id])
        assert result == [[]]
