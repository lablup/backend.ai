"""Tests for ModelCardDBSource.delete sibling-card cascade behavior."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Protocol

import pytest
import sqlalchemy as sa

from ai.backend.common.dto.manager.v2.model_card.request import DeleteModelCardOptions
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import (
    MountPermission,
    QuotaScopeID,
    QuotaScopeType,
    ResourceSlot,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.data.permission.types import RBACElementRef, RBACElementType
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus
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
from ai.backend.manager.models.resource_slot.row import (
    ModelCardResourceRequirementRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.model_card.creators import ModelCardCreatorSpec
from ai.backend.manager.repositories.model_card.db_source.db_source import ModelCardDBSource
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@dataclass(frozen=True)
class DeleteCase:
    """Parameter set for delete option-on/off coverage."""

    options: DeleteModelCardOptions
    expects_sibling_deleted: bool
    expects_vfolder_status: VFolderOperationStatus


class _MakeCardFn(Protocol):
    async def __call__(self, *, vfolder_id: VFolderUUID | None = None) -> ModelCardData: ...


_DELETE_CASES = [
    pytest.param(
        DeleteCase(
            options=DeleteModelCardOptions(delete_associated_vfolder=False),
            expects_sibling_deleted=False,
            expects_vfolder_status=VFolderOperationStatus.READY,
        ),
        id="option_off",
    ),
    pytest.param(
        DeleteCase(
            options=DeleteModelCardOptions(delete_associated_vfolder=True),
            expects_sibling_deleted=True,
            expects_vfolder_status=VFolderOperationStatus.DELETE_PENDING,
        ),
        id="option_on",
    ),
]


class TestModelCardDelete:
    """Behavioral coverage for ``ModelCardDBSource.delete``.

    With ``delete_associated_vfolder`` off the linked VFolder and any sibling
    card pointing at it must stay untouched. With the option on, every model
    card on the VFolder is hard-deleted in the same transaction and the
    VFolder flips to ``DELETE_PENDING`` so no orphan card lingers.
    """

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
                ResourceSlotTypeRow,
                ModelCardRow,
                ModelCardResourceRequirementRow,
                AssociationScopesEntitiesRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def test_domain_id(self) -> DomainID:
        return DomainID(uuid.uuid4())

    @pytest.fixture
    def test_scaling_group_id(self) -> ResourceGroupID:
        return ResourceGroupID(uuid.uuid4())

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
    ) -> DomainRow:
        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                id=test_domain_id,
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
    async def test_scaling_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_id: ResourceGroupID,
    ) -> ScalingGroupRow:
        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ScalingGroupRow(
                id=test_scaling_group_id,
                name=f"test-sgroup-{uuid.uuid4().hex[:8]}",
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(sgroup)
            await db_sess.flush()
        return sgroup

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

    @pytest.fixture
    async def test_vfolder(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainRow,
        test_user: UserRow,
    ) -> VFolderRow:
        async with db_with_cleanup.begin_session() as db_sess:
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

    @pytest.fixture
    async def mounted_vfolder(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainRow,
        test_domain_id: DomainID,
        test_scaling_group: ScalingGroupRow,
        test_scaling_group_id: ResourceGroupID,
        test_user: UserRow,
        test_group: GroupRow,
    ) -> VFolderRow:
        """A model VFolder pinned by a RUNNING session — bulk delete must refuse to touch it."""
        quota_scope_id = QuotaScopeID(QuotaScopeType.USER, test_user.uuid)
        vfolder_id = VFolderUUID(uuid.uuid4())
        async with db_with_cleanup.begin_session() as db_sess:
            vfolder = VFolderRow(
                id=vfolder_id,
                host="local",
                name=f"test-vfolder-mounted-{uuid.uuid4().hex[:8]}",
                domain_name=test_domain.name,
                usage_mode=VFolderUsageMode.MODEL,
                quota_scope_id=quota_scope_id,
                user=test_user.uuid,
            )
            db_sess.add(vfolder)
            await db_sess.flush()
            scaling_group = ScalingGroupRow(
                name="test-sg",
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(scaling_group)
            await db_sess.flush()
            mount_holder = SessionRow(
                id=uuid.uuid4(),
                domain_id=test_domain_id,
                domain_name=test_domain.name,
                resource_group_id=test_scaling_group_id,
                scaling_group_name=test_scaling_group.name,
                group_id=test_group.id,
                user_uuid=test_user.uuid,
                occupying_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                status=SessionStatus.RUNNING,
                vfolder_mounts=[
                    VFolderMount(
                        name="test-mount",
                        vfid=VFolderID(quota_scope_id=quota_scope_id, folder_id=vfolder_id),
                        vfsubpath=PurePosixPath("/"),
                        host_path=PurePosixPath("/host/test"),
                        kernel_path=PurePosixPath("/work"),
                        mount_perm=MountPermission.READ_WRITE,
                        usage_mode=VFolderUsageMode.MODEL,
                    ),
                ],
            )
            db_sess.add(mount_holder)
            await db_sess.flush()
        return vfolder

    @pytest.fixture
    def make_card(
        self,
        db_source: ModelCardDBSource,
        test_domain: DomainRow,
        test_user: UserRow,
        test_group: GroupRow,
        test_vfolder: VFolderRow,
    ) -> _MakeCardFn:
        """Factory that creates a model card on ``test_vfolder`` (or an override vfolder)."""

        async def _make(*, vfolder_id: VFolderUUID | None = None) -> ModelCardData:
            creator: RBACEntityCreator[ModelCardRow] = RBACEntityCreator(
                spec=ModelCardCreatorSpec(
                    name=f"test-model-{uuid.uuid4().hex[:8]}",
                    vfolder_id=vfolder_id if vfolder_id is not None else test_vfolder.id,
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
            return await db_source.create(creator)

        return _make

    @pytest.mark.parametrize("case", _DELETE_CASES)
    async def test_delete(
        self,
        case: DeleteCase,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ModelCardDBSource,
        make_card: _MakeCardFn,
        test_vfolder: VFolderRow,
    ) -> None:
        target = await make_card()
        sibling = await make_card()
        assert target.vfolder_id == sibling.vfolder_id

        await db_source.delete(
            Purger(row_class=ModelCardRow, pk_value=target.id),
            case.options,
        )

        async with db_with_cleanup.begin_readonly_session() as session:
            remaining_card_ids = set(
                (
                    await session.execute(
                        sa.select(ModelCardRow.id).where(
                            ModelCardRow.id.in_([target.id, sibling.id])
                        )
                    )
                )
                .scalars()
                .all()
            )
            vfolder_status = (
                await session.execute(
                    sa.select(VFolderRow.status).where(VFolderRow.id == test_vfolder.id)
                )
            ).scalar_one()

        expected_remaining = set() if case.expects_sibling_deleted else {sibling.id}
        assert remaining_card_ids == expected_remaining
        assert vfolder_status == case.expects_vfolder_status

    async def test_bulk_delete_partial_failure_with_missing_card(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ModelCardDBSource,
        make_card: _MakeCardFn,
    ) -> None:
        """A nonexistent ID must surface as a single failure without aborting the rest."""
        valid_a = await make_card()
        valid_b = await make_card()
        missing_id = uuid.uuid4()

        result = await db_source.bulk_delete(
            [
                Purger(row_class=ModelCardRow, pk_value=valid_a.id),
                Purger(row_class=ModelCardRow, pk_value=missing_id),
                Purger(row_class=ModelCardRow, pk_value=valid_b.id),
            ],
            DeleteModelCardOptions(delete_associated_vfolder=False),
        )

        assert set(result.successes) == {valid_a.id, valid_b.id}
        assert [failure.card_id for failure in result.failures] == [missing_id]

        async with db_with_cleanup.begin_readonly_session() as session:
            remaining_card_ids = (
                (
                    await session.execute(
                        sa.select(ModelCardRow.id).where(
                            ModelCardRow.id.in_([valid_a.id, valid_b.id])
                        )
                    )
                )
                .scalars()
                .all()
            )
        assert list(remaining_card_ids) == []

    async def test_bulk_delete_partial_failure_with_mounted_vfolder(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ModelCardDBSource,
        make_card: _MakeCardFn,
        test_vfolder: VFolderRow,
        mounted_vfolder: VFolderRow,
    ) -> None:
        """A vfolder mounted on a live session rejects only the affected card."""
        free_card = await make_card()
        mounted_card = await make_card(vfolder_id=VFolderUUID(mounted_vfolder.id))

        result = await db_source.bulk_delete(
            [
                Purger(row_class=ModelCardRow, pk_value=free_card.id),
                Purger(row_class=ModelCardRow, pk_value=mounted_card.id),
            ],
            DeleteModelCardOptions(delete_associated_vfolder=True),
        )

        assert set(result.successes) == {free_card.id}
        assert [failure.card_id for failure in result.failures] == [mounted_card.id]

        async with db_with_cleanup.begin_readonly_session() as session:
            remaining_card_ids = set(
                (
                    await session.execute(
                        sa.select(ModelCardRow.id).where(
                            ModelCardRow.id.in_([free_card.id, mounted_card.id])
                        )
                    )
                )
                .scalars()
                .all()
            )
            free_vfolder_status = (
                await session.execute(
                    sa.select(VFolderRow.status).where(VFolderRow.id == test_vfolder.id)
                )
            ).scalar_one()
            mounted_vfolder_status = (
                await session.execute(
                    sa.select(VFolderRow.status).where(VFolderRow.id == mounted_vfolder.id)
                )
            ).scalar_one()
        assert remaining_card_ids == {mounted_card.id}
        assert free_vfolder_status == VFolderOperationStatus.DELETE_PENDING
        assert mounted_vfolder_status == VFolderOperationStatus.READY
