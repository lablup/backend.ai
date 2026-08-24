from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, ResourceSlot, VFolderUsageMode
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.model_card.types import (
    ModelCardData,
    ModelCardResourceRequirementData,
    ResourceRequirementEntry,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.model_card.creators import (
    ModelCardCreator,
    ModelCardResourceRequirementCreator,
)
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.model_card.updaters import ModelCardUpdater
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
from ai.backend.manager.models.resource_slot.row import (
    ModelCardResourceRequirementRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.model_card.db_source.db_source import ModelCardDBSource
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.types import TriState
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.data.permission.types import ScopeType
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow


@dataclass(frozen=True)
class _CardCreators:
    """A card and the requirement rows created with it, as one write takes them."""

    card: ModelCardCreator
    requirements: list[ModelCardResourceRequirementCreator]


class TestModelCardCreatorResourceRequirements:
    """Tests for creating a model card together with its requirement rows."""

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
                EntityLabelRow,
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
                ResourceSlotTypeRow,
                ModelCardRow,
                ModelCardResourceRequirementRow,
                AssociationScopesEntitiesRow,
            ],
        ):
            async with database_connection.begin_session() as sess:
                for slot_name, slot_type in [("cpu", "count"), ("mem", "bytes")]:
                    await sess.execute(
                        sa.text(
                            "INSERT INTO resource_slot_types (slot_name, slot_type, rank)"
                            " VALUES (:slot_name, :slot_type, 0)"
                            " ON CONFLICT DO NOTHING"
                        ),
                        {"slot_name": slot_name, "slot_type": slot_type},
                    )
            yield database_connection

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainRow:
        async with db_with_cleanup.begin_session() as db_sess:
            domain_id = DomainID(uuid.uuid4())
            domain = DomainRow(
                id=domain_id,
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
                domain_id=DomainID(test_domain.id),
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
    ) -> ProjectRow:
        async with db_with_cleanup.begin_session() as db_sess:
            group = ProjectRow(
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
            db_sess.add(VirtualScopeRow(scope_type=ScopeType.PROJECT.value, scope_id=group.id))
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
        return ModelCardDBSource(db_with_cleanup, V2DBOpsProvider(db_with_cleanup))

    @pytest.fixture
    def ops(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> OpsRepository[ModelCardData]:
        return OpsRepository(V2DBOpsProvider(db_with_cleanup))

    def _build_creator(
        self,
        *,
        test_domain: DomainRow,
        test_user: UserRow,
        test_group: ProjectRow,
        test_vfolder: VFolderRow,
        min_resource: list[ResourceRequirementEntry],
    ) -> _CardCreators:
        return _CardCreators(
            card=ModelCardCreator(
                name=f"test-model-{uuid.uuid4().hex[:8]}",
                vfolder_id=test_vfolder.id,
                domain=test_domain.name,
                project_id=ProjectID(test_group.id),
                creator_id=UserID(test_user.uuid),
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
                readme=None,
                access_level="internal",
            ),
            requirements=[
                ModelCardResourceRequirementCreator(entry=entry) for entry in min_resource
            ],
        )

    @pytest.fixture
    def creator_with_min_resource(
        self,
        test_domain: DomainRow,
        test_user: UserRow,
        test_group: ProjectRow,
        test_vfolder: VFolderRow,
    ) -> _CardCreators:
        return self._build_creator(
            test_domain=test_domain,
            test_user=test_user,
            test_group=test_group,
            test_vfolder=test_vfolder,
            min_resource=[
                ResourceRequirementEntry(slot_name="cpu", min_quantity="2"),
                ResourceRequirementEntry(slot_name="mem", min_quantity="4096"),
            ],
        )

    @pytest.fixture
    def creator_without_min_resource(
        self,
        test_domain: DomainRow,
        test_user: UserRow,
        test_group: ProjectRow,
        test_vfolder: VFolderRow,
    ) -> _CardCreators:
        return self._build_creator(
            test_domain=test_domain,
            test_user=test_user,
            test_group=test_group,
            test_vfolder=test_vfolder,
            min_resource=[],
        )

    async def test_create_with_min_resource(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ModelCardDBSource,
        ops: OpsRepository[ModelCardData],
        creator_with_min_resource: _CardCreators,
    ) -> None:
        data: ModelCardData = (
            await ops.create_entity_with_fields(
                creator_with_min_resource.card, creator_with_min_resource.requirements
            )
        ).data
        entries = await self._requirements(db_with_cleanup, data.id)
        assert len(entries) == 2
        assert {(r.slot_name, r.min_quantity) for r in entries} == {
            ("cpu", "2"),
            ("mem", "4096"),
        }

    async def test_create_without_min_resource(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ModelCardDBSource,
        ops: OpsRepository[ModelCardData],
        creator_without_min_resource: _CardCreators,
    ) -> None:
        data: ModelCardData = (
            await ops.create_entity_with_fields(
                creator_without_min_resource.card, creator_without_min_resource.requirements
            )
        ).data
        assert await self._requirements(db_with_cleanup, data.id) == []

    async def _requirements(
        self, db: ExtendedAsyncSAEngine, card_id: UUID
    ) -> list[ModelCardResourceRequirementData]:
        """The card's requirement rows as their data type, quantities formatted."""
        async with db.begin_readonly_session() as session:
            rows = (
                (
                    await session.execute(
                        sa.select(ModelCardResourceRequirementRow).where(
                            ModelCardResourceRequirementRow.model_card_id == card_id
                        )
                    )
                )
                .scalars()
                .all()
            )
        return [row.to_data() for row in rows]

    async def test_resource_requirements_persisted_in_db(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ModelCardDBSource,
        ops: OpsRepository[ModelCardData],
        creator_with_min_resource: _CardCreators,
    ) -> None:
        data: ModelCardData = (
            await ops.create_entity_with_fields(
                creator_with_min_resource.card, creator_with_min_resource.requirements
            )
        ).data
        async with db_with_cleanup.begin_readonly_session() as session:
            stmt = sa.select(ModelCardResourceRequirementRow).where(
                ModelCardResourceRequirementRow.model_card_id == data.id
            )
            rows = (await session.execute(stmt)).scalars().all()
        assert len(rows) == 2
        assert {r.slot_name for r in rows} == {"cpu", "mem"}
        quantities = {r.slot_name: r.min_quantity for r in rows}
        assert quantities["cpu"] == Decimal("2")
        assert quantities["mem"] == Decimal("4096")

    async def test_update_replaces_min_resource(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ModelCardDBSource,
        ops: OpsRepository[ModelCardData],
        creator_with_min_resource: _CardCreators,
    ) -> None:
        """Regression: update() must sync model_card_resource_requirements.

        Previously the update spec's build_values ignored min_resource, so
        a min_resource-only update produced an empty UPDATE payload and
        db_source.update raised ModelCardNotFound. After the fix the child
        rows must be rewritten and the returned ModelCardData must reflect
        the new requirements.
        """
        # Seed the card with the original (cpu=2, mem=4096) requirements.
        created = (
            await ops.create_entity_with_fields(
                creator_with_min_resource.card, creator_with_min_resource.requirements
            )
        ).data

        # Swap in a completely different requirement set via update().
        # Reuse only slot_types seeded by the fixture (cpu, mem) so the
        # FK into resource_slot_types holds.
        updater = ModelCardUpdater(
            card_id=ModelCardID(created.id),
            min_resource=TriState.update([
                ResourceRequirementEntry(slot_name="cpu", min_quantity="8"),
                ResourceRequirementEntry(slot_name="mem", min_quantity="16384"),
            ]),
        )
        await db_source.update(updater)

        async with db_with_cleanup.begin_readonly_session() as session:
            rows = (
                (
                    await session.execute(
                        sa.select(ModelCardResourceRequirementRow).where(
                            ModelCardResourceRequirementRow.model_card_id == created.id
                        )
                    )
                )
                .scalars()
                .all()
            )
        assert {(r.slot_name, r.min_quantity) for r in rows} == {
            ("cpu", Decimal("8")),
            ("mem", Decimal("16384")),
        }

    async def test_update_nullify_clears_min_resource(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ModelCardDBSource,
        ops: OpsRepository[ModelCardData],
        creator_with_min_resource: _CardCreators,
    ) -> None:
        """TriState.nullify() on min_resource must drop every child row."""
        created = (
            await ops.create_entity_with_fields(
                creator_with_min_resource.card, creator_with_min_resource.requirements
            )
        ).data

        updater = ModelCardUpdater(card_id=ModelCardID(created.id), min_resource=TriState.nullify())
        await db_source.update(updater)

        async with db_with_cleanup.begin_readonly_session() as session:
            rows = (
                (
                    await session.execute(
                        sa.select(ModelCardResourceRequirementRow).where(
                            ModelCardResourceRequirementRow.model_card_id == created.id
                        )
                    )
                )
                .scalars()
                .all()
            )
        assert rows == []

    async def test_update_nop_min_resource_preserves_existing(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ModelCardDBSource,
        ops: OpsRepository[ModelCardData],
        creator_with_min_resource: _CardCreators,
    ) -> None:
        """Default NOP updater must leave child rows untouched and not 404.

        Previously an all-NOP updater (no field changes) returned None from
        execute_updater and db_source raised ModelCardNotFound. The fix must
        re-read the row instead and pass through without touching the
        normalized requirements.
        """
        created = (
            await ops.create_entity_with_fields(
                creator_with_min_resource.card, creator_with_min_resource.requirements
            )
        ).data

        # every field defaults to nop
        updater = ModelCardUpdater(card_id=ModelCardID(created.id))
        await db_source.update(updater)

        async with db_with_cleanup.begin_readonly_session() as session:
            count = (
                await session.execute(
                    sa.select(sa.func.count())
                    .select_from(ModelCardResourceRequirementRow)
                    .where(ModelCardResourceRequirementRow.model_card_id == created.id)
                )
            ).scalar_one()
        assert count == 2
