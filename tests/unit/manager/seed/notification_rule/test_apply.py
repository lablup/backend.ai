"""`mgr seed apply` writes the rules through the notification rule upserter."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.notification.row import NotificationRuleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_STARTED_ID = "0198a5a0-0000-7000-8000-00000000d001"
_DOWNLOADED_ID = "0198a5a0-0000-7000-8000-00000000d002"
_API_CREATOR = uuid.UUID("0198a5a0-0000-7000-8000-0000000000ff")


@pytest.fixture
def plan(notification_rule_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([notification_rule_seed_dir])


@pytest.fixture
async def rule_created_through_the_api(db: ExtendedAsyncSAEngine) -> None:
    """A row under the session-started rule's id whose every value differs from the seed."""
    async with db.begin_session() as sess:
        await sess.execute(
            sa.insert(NotificationRuleRow).values(
                id=uuid.UUID(_STARTED_ID),
                name="renamed",
                description="set through the API",
                rule_type="session.terminated",
                channel_id=uuid.UUID("0198a5a0-0000-7000-8000-00000000c0ff"),
                message_template="changed",
                enabled=False,
                created_by=_API_CREATOR,
            )
        )


async def _rules(db: ExtendedAsyncSAEngine) -> dict[str, dict[str, Any]]:
    """Each rule's stated columns, by id."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(NotificationRuleRow))
        return {
            str(row.id): {
                "name": row.name,
                "description": row.description,
                "rule_type": row.rule_type,
                "channel_id": str(row.channel_id),
                "message_template": row.message_template,
                "enabled": row.enabled,
                "created_by": str(row.created_by),
            }
            for row in rows
        }


async def _global_members(db: ExtendedAsyncSAEngine) -> set[str]:
    """The rules the global node holds as members."""
    global_node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == GlobalEntityType(),
            VirtualEntityRow.entity_id == global_entity_id(GlobalEntityName.GLOBAL),
        )
        .scalar_subquery()
    )
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(VirtualEntityRow.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == VirtualEntityRow.id)
            .where(
                EntityMembershipRow.virtual_entity_id == global_node,
                VirtualEntityRow.entity_type == "notification_rule",
            )
        )
        return {str(row.entity_id) for row in rows}


class TestApply:
    async def test_an_empty_database_gets_every_rule(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.NOTIFICATION_RULE].succeeded == [_STARTED_ID, _DOWNLOADED_ID]
        rules = await _rules(db)
        assert rules[_STARTED_ID]["rule_type"] == "session.started"
        assert rules[_STARTED_ID]["enabled"] is True
        assert rules[_DOWNLOADED_ID]["channel_id"] == "0198a5a0-0000-7000-8000-00000000c002"
        assert rules[_DOWNLOADED_ID]["enabled"] is False

    async def test_a_created_rule_is_created_in_global(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _global_members(db) == {_STARTED_ID, _DOWNLOADED_ID}

    @pytest.mark.usefixtures("rule_created_through_the_api")
    async def test_an_existing_rule_is_skipped_and_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        existing = (await _rules(db))[_STARTED_ID]

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.NOTIFICATION_RULE].succeeded == [_DOWNLOADED_ID]
        assert [skip.reason for skip in results[SeedKind.NOTIFICATION_RULE].skipped] == ["exists"]
        assert (await _rules(db))[_STARTED_ID] == existing

    @pytest.mark.usefixtures("rule_created_through_the_api")
    async def test_an_overwrite_rewrites_the_stated_values_and_keeps_the_creator(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert results[SeedKind.NOTIFICATION_RULE].succeeded == [_STARTED_ID, _DOWNLOADED_ID]
        assert (await _rules(db))[_STARTED_ID] == {
            "name": "session-started",
            "description": "set through the API",
            "rule_type": "session.started",
            "channel_id": "0198a5a0-0000-7000-8000-00000000c001",
            "message_template": "Session {{ session_id }} started",
            "enabled": True,
            "created_by": str(_API_CREATOR),
        }
        assert _STARTED_ID in await _global_members(db)
