"""Tests for ModelCardDBSource scan upsert + search_available_presets.

Verifies:
- bulk_upsert_scan populates model_card_resource_requirements (the bug fix
  for the scan path that was previously dropping min_resource entirely).
- Re-running scan with the same specs is idempotent — child rows must not
  duplicate.
- search_available_presets correctly filters presets by min_resource once
  the requirements table is populated (relational division).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, ResourceSlot, VFolderUsageMode
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.model_card.types import ResourceRequirementEntry
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
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
    PresetResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.model_card.db_source.db_source import ModelCardDBSource
from ai.backend.manager.repositories.model_card.upserters import ModelCardScanUpserterSpec
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestModelCardScanResourceRequirements:
    """Verify scan upsert syncs the normalized requirements table.

    Background: ModelCardScanUpserterSpec previously skipped `min_resource`
    in build_insert_values/build_update_values, leaving the
    model_card_resource_requirements table empty even after a full scan.
    That caused search_available_presets's relational division to be
    vacuously true and return every preset regardless of resource needs.
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
                ImageRow,
                VFolderRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ModelCardRow,
                ModelCardResourceRequirementRow,
                AssociationScopesEntitiesRow,
                DeploymentRevisionPresetRow,
                PresetResourceSlotRow,
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

    def _build_scan_spec(
        self,
        *,
        name: str,
        test_domain: DomainRow,
        test_user: UserRow,
        test_group: GroupRow,
        test_vfolder: VFolderRow,
        min_resource: list[ResourceRequirementEntry],
    ) -> ModelCardScanUpserterSpec:
        return ModelCardScanUpserterSpec(
            name=name,
            vfolder_id=test_vfolder.id,
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
            min_resource=min_resource,
            readme=None,
            access_level="internal",
        )

    async def test_scan_populates_resource_requirements(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ModelCardDBSource,
        test_domain: DomainRow,
        test_user: UserRow,
        test_group: GroupRow,
        test_vfolder: VFolderRow,
    ) -> None:
        spec = self._build_scan_spec(
            name="scan-card-with-min-resource",
            test_domain=test_domain,
            test_user=test_user,
            test_group=test_group,
            test_vfolder=test_vfolder,
            min_resource=[
                ResourceRequirementEntry(slot_name="cpu", min_quantity="2"),
                ResourceRequirementEntry(slot_name="mem", min_quantity="4096"),
            ],
        )

        await db_source.bulk_upsert_scan([spec], existing_names=set())

        async with db_with_cleanup.begin_readonly_session() as sess:
            card_id = (
                await sess.execute(sa.select(ModelCardRow.id).where(ModelCardRow.name == spec.name))
            ).scalar_one()
            rows = (
                (
                    await sess.execute(
                        sa.select(ModelCardResourceRequirementRow).where(
                            ModelCardResourceRequirementRow.model_card_id == card_id
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert {(r.slot_name, r.min_quantity) for r in rows} == {
            ("cpu", Decimal("2")),
            ("mem", Decimal("4096")),
        }

    async def test_scan_is_idempotent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ModelCardDBSource,
        test_domain: DomainRow,
        test_user: UserRow,
        test_group: GroupRow,
        test_vfolder: VFolderRow,
    ) -> None:
        # Re-running scan with the same input must NOT duplicate child rows.
        spec = self._build_scan_spec(
            name="scan-idempotent-card",
            test_domain=test_domain,
            test_user=test_user,
            test_group=test_group,
            test_vfolder=test_vfolder,
            min_resource=[
                ResourceRequirementEntry(slot_name="cpu", min_quantity="1"),
            ],
        )

        await db_source.bulk_upsert_scan([spec], existing_names=set())
        await db_source.bulk_upsert_scan([spec], existing_names={spec.name})
        await db_source.bulk_upsert_scan([spec], existing_names={spec.name})

        async with db_with_cleanup.begin_readonly_session() as sess:
            card_id = (
                await sess.execute(sa.select(ModelCardRow.id).where(ModelCardRow.name == spec.name))
            ).scalar_one()
            count = (
                await sess.execute(
                    sa.select(sa.func.count())
                    .select_from(ModelCardResourceRequirementRow)
                    .where(ModelCardResourceRequirementRow.model_card_id == card_id)
                )
            ).scalar_one()

        assert count == 1

    async def test_scan_replaces_requirements_on_change(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ModelCardDBSource,
        test_domain: DomainRow,
        test_user: UserRow,
        test_group: GroupRow,
        test_vfolder: VFolderRow,
    ) -> None:
        # If the model definition changes its min_resource between scans,
        # the new set must replace the old set entirely.
        first = self._build_scan_spec(
            name="scan-replace-card",
            test_domain=test_domain,
            test_user=test_user,
            test_group=test_group,
            test_vfolder=test_vfolder,
            min_resource=[
                ResourceRequirementEntry(slot_name="cpu", min_quantity="1"),
                ResourceRequirementEntry(slot_name="mem", min_quantity="1024"),
            ],
        )
        await db_source.bulk_upsert_scan([first], existing_names=set())

        second = self._build_scan_spec(
            name="scan-replace-card",
            test_domain=test_domain,
            test_user=test_user,
            test_group=test_group,
            test_vfolder=test_vfolder,
            min_resource=[
                # cpu requirement removed, mem requirement increased
                ResourceRequirementEntry(slot_name="mem", min_quantity="8192"),
            ],
        )
        await db_source.bulk_upsert_scan([second], existing_names={second.name})

        async with db_with_cleanup.begin_readonly_session() as sess:
            card_id = (
                await sess.execute(
                    sa.select(ModelCardRow.id).where(ModelCardRow.name == first.name)
                )
            ).scalar_one()
            rows = (
                (
                    await sess.execute(
                        sa.select(ModelCardResourceRequirementRow).where(
                            ModelCardResourceRequirementRow.model_card_id == card_id
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert {(r.slot_name, r.min_quantity) for r in rows} == {
            ("mem", Decimal("8192")),
        }

    async def test_search_available_presets_filters_by_min_resource(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ModelCardDBSource,
        test_domain: DomainRow,
        test_user: UserRow,
        test_group: GroupRow,
        test_vfolder: VFolderRow,
    ) -> None:
        # Once the scan populates requirements, the relational division SQL
        # must reject presets that cannot satisfy them. Before the scan
        # upserter fix this filter was vacuously true and returned everything.
        spec = self._build_scan_spec(
            name="scan-filter-card",
            test_domain=test_domain,
            test_user=test_user,
            test_group=test_group,
            test_vfolder=test_vfolder,
            min_resource=[
                ResourceRequirementEntry(slot_name="cpu", min_quantity="4"),
                ResourceRequirementEntry(slot_name="mem", min_quantity="2048"),
            ],
        )
        await db_source.bulk_upsert_scan([spec], existing_names=set())

        async with db_with_cleanup.begin_session() as sess:
            card_id = (
                await sess.execute(sa.select(ModelCardRow.id).where(ModelCardRow.name == spec.name))
            ).scalar_one()

            runtime_variant = uuid.uuid4()
            image_id = uuid.uuid4()

            # Insert two presets:
            # - "small": cpu=1, mem=1024  → BOTH slots fail → must be excluded
            # - "big": cpu=8, mem=4096    → BOTH slots satisfy → must be included
            small = DeploymentRevisionPresetRow(
                id=uuid.uuid4(),
                runtime_variant=runtime_variant,
                name="small",
                rank=1,
                image_id=image_id,
            )
            big = DeploymentRevisionPresetRow(
                id=uuid.uuid4(),
                runtime_variant=runtime_variant,
                name="big",
                rank=2,
                image_id=image_id,
            )
            sess.add_all([small, big])
            await sess.flush()

            sess.add_all([
                PresetResourceSlotRow(preset_id=small.id, slot_name="cpu", quantity=Decimal("1")),
                PresetResourceSlotRow(
                    preset_id=small.id, slot_name="mem", quantity=Decimal("1024")
                ),
                PresetResourceSlotRow(preset_id=big.id, slot_name="cpu", quantity=Decimal("8")),
                PresetResourceSlotRow(preset_id=big.id, slot_name="mem", quantity=Decimal("4096")),
            ])
            await sess.flush()
            big_id = big.id

        result = await db_source.search_available_presets(
            card_id,
            SearchDeploymentRevisionPresetsInput(),
        )

        returned_ids = {item.id for item in result.items}
        assert big_id in returned_ids
        assert len(returned_ids) == 1, (
            f"Expected only the satisfying preset, got {len(returned_ids)}: "
            "the relational-division filter regressed."
        )
