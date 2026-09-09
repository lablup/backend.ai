"""What the World seeded, and what each persona may do because of it.

Needs the scenario tree's database fixtures, which is why it lives here rather than
beside the generic surface in ``tests/unit/testutils``.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow, ProjectType
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.virtual_entity.queries import user_scope_membership_query
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from bai_scenario.infra.db import TemplateDatabase
from bai_scenario.infra.personas import ALL_PERSONAS, DOMAIN_ADMIN, MEMBER, OTHER_MEMBER, SUPERADMIN

# --- World seed --------------------------------------------------------------------------


class TestWorldSeed:
    async def test_every_persona_has_user_default_keypair_and_personal_project(
        self, world_template: TemplateDatabase, engine: Any
    ) -> None:
        world = world_template.world
        async with engine.begin_readonly_session() as sess:
            for persona in ALL_PERSONAS:
                seeded = world.users[persona]
                user = await sess.scalar(sa.select(UserRow).where(UserRow.uuid == seeded.id))
                assert user is not None and user.domain_name == world.domain_name
                keypair = await sess.scalar(
                    sa.select(KeyPairRow).where(KeyPairRow.user == seeded.id, KeyPairRow.is_default)
                )
                assert keypair is not None and keypair.access_key == seeded.access_key
                personal = await sess.scalar(
                    sa.select(sa.func.count())
                    .select_from(ProjectRow)
                    .where(
                        ProjectRow.creator_id == seeded.id, ProjectRow.type == ProjectType.PERSONAL
                    )
                )
                assert personal == 1

    async def test_the_world_holds_exactly_one_domain(self, engine: Any) -> None:
        async with engine.begin_readonly_session() as sess:
            names = (await sess.scalars(sa.select(DomainRow.name))).all()
        assert names == ["default"]

    async def test_superadmin_persona_is_a_superadmin(
        self, world_template: TemplateDatabase
    ) -> None:
        assert world_template.world.users[SUPERADMIN].role == "superadmin"


# --- what each persona may do, which is what the scenario tables lean on -------------


class TestPersonaPermissions:
    async def test_each_persona_holds_the_roles_the_world_granted(self, engine: Any) -> None:
        """The four personas differ, and the difference is what a permission scenario
        is written against."""
        world_users = dict.fromkeys(ALL_PERSONAS)
        assert len(world_users) == 4

    async def test_the_member_is_on_the_project_roster_and_the_other_is_not(
        self, world_template: TemplateDatabase, engine: Any
    ) -> None:
        world = world_template.world
        async with engine.begin_readonly_session() as sess:
            rows = (
                await sess.execute(
                    user_scope_membership_query(PROJECT_SCOPE_TYPE).where(
                        VirtualEntityRow.entity_id == world.project_id
                    )
                )
            ).all()
        on_roster = {r[0] for r in rows}
        assert world.users[MEMBER].id in on_roster
        assert world.users[OTHER_MEMBER].id not in on_roster

    async def test_personas_other_than_the_superadmin_hold_roles(
        self, world_template: TemplateDatabase, engine: Any
    ) -> None:
        """Without a granted role a member could not be told apart from a stranger, and
        every "allowed" scenario would be unwritable."""
        world = world_template.world
        async with engine.begin_readonly_session() as sess:
            for persona in (DOMAIN_ADMIN, MEMBER, OTHER_MEMBER):
                count = await sess.scalar(
                    sa.select(sa.func.count())
                    .select_from(UserRoleRow)
                    .where(UserRoleRow.user_id == world.users[persona].id)
                )
                assert count and count >= 1, persona
