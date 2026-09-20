"""Runs the model card creator edge backfill against a real database and reads the
graph rows back."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.model_card import ModelCardEntityType, ModelCardID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, ResourceSlot, VFolderUsageMode
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.alembic.versions import (
    e7a3c1d95f42_backfill_model_card_creator_edges as revision,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    ResourceGroupRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    VirtualEntityRow,
    ScopeBindingRow,
    EntityLabelRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
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
]

type _Edge = tuple[uuid.UUID, uuid.UUID]


@dataclass
class _Card:
    """A card on file with its project edge, and the nodes its edges join."""

    card_node: uuid.UUID
    project_node: uuid.UUID
    creator_node: uuid.UUID | None


@dataclass
class _Edges:
    memberships: set[_Edge]
    bindings: set[_Edge]


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


async def _add_node(
    db: ExtendedAsyncSAEngine, entity_type: EntityType, entity_id: uuid.UUID
) -> uuid.UUID:
    async with db.begin_session() as session:
        node = VirtualEntityRow(entity_type=entity_type, entity_id=entity_id)
        session.add(node)
        await session.flush()
        return node.id


async def _add_edge(db: ExtendedAsyncSAEngine, scope_node: uuid.UUID, node: uuid.UUID) -> None:
    async with db.begin_session() as session:
        session.add(
            EntityMembershipRow(virtual_entity_id=scope_node, member_entity_id=node, capped=False)
        )
        session.add(
            ScopeBindingRow(virtual_entity_id=node, scope_entity_id=scope_node, permission_cap=None)
        )


async def _add_card(db: ExtendedAsyncSAEngine, *, creator_in_graph: bool) -> _Card:
    suffix = uuid.uuid4().hex[:8]
    domain_id = DomainID(uuid.uuid4())
    domain_name = f"domain-{suffix}"
    user_id = UserID(uuid.uuid4())
    project_id = ProjectID(uuid.uuid4())
    vfolder_id = VFolderUUID(uuid.uuid4())
    card_id = ModelCardID(uuid.uuid4())
    async with db.begin_session() as session:
        session.add(
            UserResourcePolicyRow(
                name=f"user-policy-{suffix}",
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=1,
                max_customized_image_count=0,
            )
        )
        session.add(
            ProjectResourcePolicyRow(
                name=f"project-policy-{suffix}",
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=1,
            )
        )
        session.add(
            DomainRow(
                id=domain_id,
                name=domain_name,
                description="",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
        )
        await session.flush()
        session.add(
            UserRow(
                uuid=user_id,
                username=f"user-{suffix}",
                email=f"user-{suffix}@example.com",
                password=PasswordInfo(
                    password="test-password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=1_000,
                    salt_size=32,
                ),
                need_password_change=False,
                domain_id=domain_id,
                domain_name=domain_name,
                resource_policy=f"user-policy-{suffix}",
            )
        )
        session.add(
            ProjectRow(
                id=project_id,
                name=f"project-{suffix}",
                description="",
                is_active=True,
                domain_name=domain_name,
                resource_policy=f"project-policy-{suffix}",
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
            )
        )
        await session.flush()
        session.add(
            VFolderRow(
                id=vfolder_id,
                host="local",
                name=f"vfolder-{suffix}",
                domain_name=domain_name,
                usage_mode=VFolderUsageMode.MODEL,
                quota_scope_id=QuotaScopeID(QuotaScopeType.USER, user_id),
                user=user_id,
            )
        )
        await session.flush()
        card = ModelCardRow()
        card.id = card_id
        card.name = f"card-{suffix}"
        card.vfolder = vfolder_id
        card.domain = domain_name
        card.project = project_id
        card.creator = user_id
        card.framework = []
        card.label = []
        card.access_level = "internal"
        session.add(card)
    card_node = await _add_node(db, ModelCardEntityType(), card_id)
    project_node = await _add_node(db, ProjectEntityType(), project_id)
    creator_node = await _add_node(db, UserEntityType(), user_id) if creator_in_graph else None
    await _add_edge(db, project_node, card_node)
    return _Card(card_node=card_node, project_node=project_node, creator_node=creator_node)


async def _edges(db: ExtendedAsyncSAEngine) -> _Edges:
    """Every own edge on file as (scope node, member node)."""
    async with db.begin_readonly_session() as session:
        memberships = (
            await session.execute(
                sa.select(
                    EntityMembershipRow.virtual_entity_id, EntityMembershipRow.member_entity_id
                ).where(EntityMembershipRow.capped.is_(False))
            )
        ).all()
        bindings = (
            await session.execute(
                sa.select(ScopeBindingRow.scope_entity_id, ScopeBindingRow.virtual_entity_id)
            )
        ).all()
    return _Edges(
        memberships={(scope, node) for scope, node in memberships},
        bindings={(scope, node) for scope, node in bindings},
    )


async def _upgrade(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(revision.add_creator_edges)


async def _downgrade(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(revision.remove_creator_edges)


class TestBackfillModelCardCreatorEdges:
    async def test_a_card_gains_its_creator_edge_and_keeps_its_project_edge(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        card = await _add_card(db, creator_in_graph=True)
        assert card.creator_node is not None

        await _upgrade(db)

        expected = {(card.project_node, card.card_node), (card.creator_node, card.card_node)}
        edges = await _edges(db)
        assert edges.memberships == expected
        assert edges.bindings == expected

    async def test_a_card_whose_creator_has_no_node_keeps_its_project_edge_alone(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        card = await _add_card(db, creator_in_graph=False)

        await _upgrade(db)

        expected = {(card.project_node, card.card_node)}
        edges = await _edges(db)
        assert edges.memberships == expected
        assert edges.bindings == expected

    async def test_a_card_already_holding_its_creator_edge_is_left_as_it_is(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        card = await _add_card(db, creator_in_graph=True)
        assert card.creator_node is not None
        await _add_edge(db, card.creator_node, card.card_node)
        before = await _edges(db)

        await _upgrade(db)
        await _upgrade(db)

        assert await _edges(db) == before

    async def test_every_chunk_is_written(
        self, db: ExtendedAsyncSAEngine, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(revision, "CHUNK_SIZE", 2)
        cards = [await _add_card(db, creator_in_graph=True) for _ in range(5)]

        await _upgrade(db)

        edges = await _edges(db)
        assert {(card.creator_node, card.card_node) for card in cards} <= edges.memberships
        assert {(card.creator_node, card.card_node) for card in cards} <= edges.bindings

    async def test_downgrade_removes_the_creator_edge_and_keeps_the_project_edge(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        card = await _add_card(db, creator_in_graph=True)
        await _upgrade(db)

        await _downgrade(db)

        expected = {(card.project_node, card.card_node)}
        edges = await _edges(db)
        assert edges.memberships == expected
        assert edges.bindings == expected
