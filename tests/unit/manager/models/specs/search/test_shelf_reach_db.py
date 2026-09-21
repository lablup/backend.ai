"""Scenario 자: a search narrowed to what the caller's roles reach.

The zones stand in for scopes. Z1 holds its shelves outright; Z2 reaches its two through
a holder it governs under a cap, the shape a relation row writes, with one cap carrying
READ and the other withholding it.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables

from .shelf_fixtures import Seeded, seed_shelves
from .shelf_rows import (
    BoxRow,
    CartLineRow,
    CartRow,
    CategoryRow,
    ShelfData,
    ShelfEntityType,
    ShelfItemRow,
    ShelfRow,
    SpecRow,
    ZoneEntityType,
)
from .shelf_search import ShelfSearches, ids

_DOMAIN_NAME = "test-search-reach"
_POLICY_NAME = "test-search-reach"


@dataclass(frozen=True)
class Reachers:
    """The two callers every scenario reads as."""

    member: UserID
    """Holds a role in both zones."""
    outsider: UserID
    """Holds no role at all."""


async def _node(
    sess: AsyncSession, entity_type: EntityType, entity_id: uuid.UUID
) -> VirtualEntityRow:
    """A node as the graph writer makes one: it owns and governs itself."""
    row = VirtualEntityRow(entity_type=entity_type, entity_id=entity_id)
    sess.add(row)
    await sess.flush()
    sess.add(EntityMembershipRow(virtual_entity_id=row.id, member_entity_id=row.id, capped=False))
    sess.add(ScopeBindingRow(virtual_entity_id=row.id, scope_entity_id=row.id))
    await sess.flush()
    return row


async def _create_in(sess: AsyncSession, scope: VirtualEntityRow, node: VirtualEntityRow) -> None:
    """What creating the node in the scope writes: the scope owns it and governs it."""
    sess.add(
        EntityMembershipRow(virtual_entity_id=scope.id, member_entity_id=node.id, capped=False)
    )
    sess.add(ScopeBindingRow(virtual_entity_id=node.id, scope_entity_id=scope.id))
    await sess.flush()


async def _governed_by(
    sess: AsyncSession, scope: VirtualEntityRow, node: VirtualEntityRow, cap: Permission
) -> None:
    """The scope governs the node under ``cap``, the shape a relation row writes. What
    the node owns is read through the scope only as far as the cap allows."""
    sess.add(
        ScopeBindingRow(virtual_entity_id=node.id, scope_entity_id=scope.id, permission_cap=cap)
    )
    await sess.flush()


async def _share_into(
    sess: AsyncSession, scope: VirtualEntityRow, node: VirtualEntityRow, cap: Permission
) -> None:
    """The node is shared into the scope, letting ``cap`` through on every field."""
    edge = EntityMembershipRow(virtual_entity_id=scope.id, member_entity_id=node.id, capped=True)
    sess.add(edge)
    await sess.flush()
    sess.add_all([
        EntityMembershipCapRow(membership_id=edge.id, permission=bit, all_fields=True)
        for bit in Permission
        if bit and cap & bit
    ])
    await sess.flush()


async def _grant(
    sess: AsyncSession,
    scope: VirtualEntityRow,
    user_id: UserID,
    permissions: Permission,
) -> None:
    """A role in the scope holding the named bits on shelves, assigned to the user."""
    role = RoleRow(
        name=f"role-{uuid.uuid4().hex[:8]}",
        status=RoleStatus.ACTIVE,
        scope_type=scope.entity_type,
        scope_id=scope.entity_id,
    )
    sess.add(role)
    await sess.flush()
    sess.add_all([
        PermissionRow(role_id=role.id, entity_type=ShelfEntityType(), permission=bit)
        for bit in Permission
        if bit and permissions & bit
    ])
    sess.add(UserRoleRow(user_id=user_id, role_id=role.id))
    await sess.flush()


class TestReachableSearch:
    @pytest.fixture
    async def reach_db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                CategoryRow,
                ShelfRow,
                SpecRow,
                BoxRow,
                ShelfItemRow,
                CartRow,
                CartLineRow,
                DomainRow,
                UserResourcePolicyRow,
                UserRow,
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                ScopeBindingRow,
                RoleRow,
                PermissionRow,
                UserRoleRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def seeded(self, reach_db: ExtendedAsyncSAEngine) -> Seeded:
        return await seed_shelves(reach_db)

    @pytest.fixture
    def searches(self, reach_db: ExtendedAsyncSAEngine) -> ShelfSearches:
        return ShelfSearches(OpsRepository[ShelfData](V2DBOpsProvider(reach_db)))

    @pytest.fixture
    async def reachers(self, reach_db: ExtendedAsyncSAEngine, seeded: Seeded) -> Reachers:
        """Z1 holds S1 and S2. Z2 governs two holders under a cap, one carrying READ and
        holding S3, the other withholding it and holding S4. The member holds a role
        granting shelf READ in both zones."""
        member = UserID(uuid.uuid4())
        outsider = UserID(uuid.uuid4())
        async with reach_db.begin_session() as sess:
            await self._write_users(sess, [member, outsider])
            zones = {
                key: await _node(sess, ZoneEntityType(), zone_id)
                for key, zone_id in seeded.zones.items()
            }
            holders = {
                cap: await _node(sess, ZoneEntityType(), uuid.uuid4())
                for cap in (Permission.READ, Permission.UPDATE)
            }
            for cap, holder in holders.items():
                await _governed_by(sess, zones["Z2"], holder, cap)
            owners = {
                "S1": zones["Z1"],
                "S2": zones["Z1"],
                "S3": holders[Permission.READ],
                "S4": holders[Permission.UPDATE],
            }
            for key, shelf in seeded.shelves.items():
                node = await _node(sess, ShelfEntityType(), shelf.id)
                await _create_in(sess, owners[key], node)
            for zone in zones.values():
                await _grant(sess, zone, member, Permission.READ)
            await sess.commit()
        return Reachers(member=member, outsider=outsider)

    async def _write_users(self, sess: AsyncSession, user_ids: list[UserID]) -> None:
        domain_id = DomainID(uuid.uuid4())
        sess.add(
            DomainRow(
                id=domain_id,
                name=_DOMAIN_NAME,
                description="Reachability scenarios",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
        )
        sess.add(
            UserResourcePolicyRow(
                name=_POLICY_NAME,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        await sess.flush()
        sess.add_all([
            UserRow(
                uuid=user_id,
                username=f"user-{uuid.uuid4().hex[:8]}",
                email=f"{uuid.uuid4().hex[:8]}@test.io",
                domain_name=_DOMAIN_NAME,
                domain_id=domain_id,
                role=UserRole.USER,
                resource_policy=_POLICY_NAME,
            )
            for user_id in user_ids
        ])
        await sess.flush()

    async def test_자1_only_the_rows_a_granting_scope_holds_are_read(
        self, searches: ShelfSearches, seeded: Seeded, reachers: Reachers
    ) -> None:
        result = await searches.visible_to(reachers.member)

        assert ids(result) == seeded.shelf_ids("S1", "S2", "S3")
        assert result.total_count == 3

    async def test_자2_a_cap_withholding_the_bit_hides_the_rows(
        self, searches: ShelfSearches, seeded: Seeded, reachers: Reachers
    ) -> None:
        """Z2's role grants READ on both holders; only the cap carrying READ passes."""
        result = await searches.visible_to(reachers.member)

        assert ids(result).isdisjoint(seeded.shelf_ids("S4"))

    async def test_자3_a_caller_holding_no_role_reads_nothing(
        self, searches: ShelfSearches, reachers: Reachers
    ) -> None:
        result = await searches.visible_to(reachers.outsider)

        assert ids(result) == set()
        assert result.total_count == 0

    async def test_자4_a_share_answers_when_its_cap_carries_the_bit(
        self, reach_db: ExtendedAsyncSAEngine, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        """A shelf shared into a scope is read there, under the share's cap."""
        recipient = UserID(uuid.uuid4())
        async with reach_db.begin_session() as sess:
            await self._write_users(sess, [recipient])
            landing = await _node(sess, ZoneEntityType(), uuid.uuid4())
            shared = await _node(sess, ShelfEntityType(), seeded.shelf_id("S3"))
            withheld = await _node(sess, ShelfEntityType(), seeded.shelf_id("S4"))
            await _share_into(sess, landing, shared, Permission.READ)
            await _share_into(sess, landing, withheld, Permission.UPDATE)
            await _grant(sess, landing, recipient, Permission.READ)
            await sess.commit()

        result = await searches.visible_to(recipient)

        assert ids(result) == seeded.shelf_ids("S3")
