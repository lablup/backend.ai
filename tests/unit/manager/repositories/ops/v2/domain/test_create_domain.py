"""Integration tests for what ``create_domain`` provisions."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.resource_policy import ProjectResourcePolicyEntityType
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.domain.provider import DomainOpsProvider
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    RolePresetRow,
    RolePermissionPresetRow,
    RoleRow,
    PermissionRow,
    UserRoleRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    VirtualEntityRow,
    ScopeBindingRow,
    EntityLabelRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
]


@pytest.fixture
async def db(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(global_entity_ids, _TABLES):
        yield global_entity_ids


@pytest.fixture
def provider(db: ExtendedAsyncSAEngine) -> DomainOpsProvider:
    return DomainOpsProvider(db)


@pytest.fixture
async def resource_policies(db: ExtendedAsyncSAEngine) -> None:
    """The ``default`` policies every provisioned row falls back to."""
    async with db.begin_session() as session:
        session.add(
            ProjectResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
        )
        await session.commit()


def _node_of(entity_type: str, entity_id: uuid.UUID) -> sa.ScalarSelect[VirtualEntityID]:
    return (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == entity_type,
            VirtualEntityRow.entity_id == entity_id,
        )
        .scalar_subquery()
    )


async def _model_store_projects(db: ExtendedAsyncSAEngine, domain_name: str) -> list[ProjectRow]:
    async with db.begin_readonly_session() as session:
        return list(
            (
                await session.scalars(
                    sa.select(ProjectRow).where(
                        ProjectRow.domain_name == domain_name,
                        ProjectRow.type == ProjectType.MODEL_STORE,
                    )
                )
            ).all()
        )


class TestModelStoreProjectProvisioning:
    """Creating a domain registers the model-store project it holds."""

    async def test_creates_the_model_store_project(
        self,
        db: ExtendedAsyncSAEngine,
        provider: DomainOpsProvider,
        resource_policies: None,
    ) -> None:
        name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with provider.write_ops() as w:
            result = await w.create_domain(DomainCreator(name=name))

        projects = await _model_store_projects(db, name)
        assert len(projects) == 1
        assert projects[0].id == result.model_store_project.id
        assert projects[0].name == "model-store"
        assert projects[0].resource_policy == "default"
        assert projects[0].total_resource_slots == ResourceSlot()

    async def test_the_model_store_project_is_created_in_the_domain(
        self,
        db: ExtendedAsyncSAEngine,
        provider: DomainOpsProvider,
        resource_policies: None,
    ) -> None:
        name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with provider.write_ops() as w:
            result = await w.create_domain(DomainCreator(name=name))

        async with db.begin_readonly_session() as session:
            owned = await session.scalar(
                sa.select(
                    sa.exists().where(
                        EntityMembershipRow.virtual_entity_id
                        == _node_of(DomainEntityType(), DomainID(result.domain.id)),
                        EntityMembershipRow.member_entity_id
                        == _node_of(ProjectEntityType(), ProjectID(result.model_store_project.id)),
                    )
                )
            )
        assert owned

    async def test_the_model_store_project_is_lent_its_resource_policy(
        self,
        db: ExtendedAsyncSAEngine,
        provider: DomainOpsProvider,
        resource_policies: None,
    ) -> None:
        name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with provider.write_ops() as w:
            result = await w.create_domain(DomainCreator(name=name))

        async with db.begin_readonly_session() as session:
            policy_id = await session.scalar(
                sa.select(ProjectResourcePolicyRow.uuid).where(
                    ProjectResourcePolicyRow.name == "default"
                )
            )
            assert policy_id is not None
            lent = await session.scalar(
                sa.select(
                    sa.exists().where(
                        EntityMembershipRow.virtual_entity_id
                        == _node_of(ProjectEntityType(), ProjectID(result.model_store_project.id)),
                        EntityMembershipRow.member_entity_id
                        == _node_of(ProjectResourcePolicyEntityType(), policy_id),
                        EntityMembershipRow.capped.is_(True),
                    )
                )
            )
        assert lent
