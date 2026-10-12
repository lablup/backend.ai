"""`mgr seed apply` writes the channels through the notification channel upserter."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.notification.row import NotificationChannelRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_WEBHOOK_ID = "0198a5a0-0000-7000-8000-00000000c001"
_EMAIL_ID = "0198a5a0-0000-7000-8000-00000000c002"
_API_CREATOR = uuid.UUID("0198a5a0-0000-7000-8000-0000000000ff")


@pytest.fixture
def plan(notification_channel_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([notification_channel_seed_dir])


@pytest.fixture
async def channel_created_through_the_api(db: ExtendedAsyncSAEngine) -> None:
    """A row under the webhook's id whose every value differs from the seed."""
    async with db.begin_session() as sess:
        await sess.execute(
            sa.insert(NotificationChannelRow).values(
                id=uuid.UUID(_WEBHOOK_ID),
                name="renamed",
                description="set through the API",
                channel_type="email",
                config={},
                enabled=False,
                created_by=_API_CREATOR,
            )
        )


async def _channels(db: ExtendedAsyncSAEngine) -> dict[str, dict[str, Any]]:
    """Each channel's stated columns, by id."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(NotificationChannelRow))
        return {
            str(row.id): {
                "name": row.name,
                "description": row.description,
                "channel_type": row.channel_type,
                "config": row.config,
                "enabled": row.enabled,
                "created_by": str(row.created_by),
            }
            for row in rows
        }


async def _global_members(db: ExtendedAsyncSAEngine) -> set[str]:
    """The channels the global node holds as members."""
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
                VirtualEntityRow.entity_type == "notification_channel",
            )
        )
        return {str(row.entity_id) for row in rows}


class TestApply:
    async def test_an_empty_database_gets_every_channel(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.NOTIFICATION_CHANNEL].succeeded == [_WEBHOOK_ID, _EMAIL_ID]
        channels = await _channels(db)
        assert channels[_WEBHOOK_ID]["config"]["url"] == "https://hooks.example.com/ops"
        assert channels[_WEBHOOK_ID]["enabled"] is True
        assert channels[_EMAIL_ID]["channel_type"] == "email"
        assert channels[_EMAIL_ID]["config"]["smtp"]["host"] == "smtp.example.com"
        assert channels[_EMAIL_ID]["enabled"] is False

    async def test_a_created_channel_is_created_in_global(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _global_members(db) == {_WEBHOOK_ID, _EMAIL_ID}

    @pytest.mark.usefixtures("channel_created_through_the_api")
    async def test_an_existing_channel_is_skipped_and_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        existing = (await _channels(db))[_WEBHOOK_ID]

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.NOTIFICATION_CHANNEL].succeeded == [_EMAIL_ID]
        assert [skip.reason for skip in results[SeedKind.NOTIFICATION_CHANNEL].skipped] == [
            "exists"
        ]
        assert (await _channels(db))[_WEBHOOK_ID] == existing

    @pytest.mark.usefixtures("channel_created_through_the_api")
    async def test_an_overwrite_rewrites_the_stated_values_and_keeps_the_creator(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert results[SeedKind.NOTIFICATION_CHANNEL].succeeded == [_WEBHOOK_ID, _EMAIL_ID]
        assert (await _channels(db))[_WEBHOOK_ID] == {
            "name": "ops-webhook",
            "description": None,
            "channel_type": "webhook",
            "config": {
                "url": "https://hooks.example.com/ops",
                "method": "POST",
                "content_type": "application/json",
                "headers": {},
                "timeout": 30,
                "success_status_codes": [200, 201, 202, 204],
            },
            "enabled": True,
            "created_by": str(_API_CREATOR),
        }
        assert _WEBHOOK_ID in await _global_members(db)
