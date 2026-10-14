"""Tests for EntityShareAdapter node conversion."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.api.adapters.entity_share.adapter import EntityShareAdapter
from ai.backend.manager.data.entity_share.types import EntityShareData, EntityShareStatus


def _share_data(
    *,
    recipient: RuntimeEntityID | None,
    recipient_email: str | None,
    status: EntityShareStatus,
    expires_at: datetime | None,
) -> EntityShareData:
    now = datetime.now(tz=UTC)
    return EntityShareData(
        id=EntityShareID(uuid4()),
        sharer_user_id=UserID(uuid4()),
        recipient=recipient,
        recipient_email=recipient_email,
        target=RuntimeEntityID(VFolderEntityType(), uuid4()),
        permission_cap=Permission.READ,
        expires_at=expires_at,
        status=status,
        created_at=now,
        updated_at=now,
    )


def _adapter(data: EntityShareData) -> EntityShareAdapter:
    processors = MagicMock()
    processors.get.run = AsyncMock(return_value=MagicMock(data=data))
    return EntityShareAdapter(processors)


class TestEntityShareNodeRecipient:
    async def test_user_recipient_fills_type_id_and_expiry(self) -> None:
        recipient_id = uuid4()
        expires_at = datetime.now(tz=UTC) + timedelta(days=1)
        data = _share_data(
            recipient=RuntimeEntityID(UserEntityType(), recipient_id),
            recipient_email=None,
            status=EntityShareStatus.PENDING,
            expires_at=expires_at,
        )

        payload = await _adapter(data).get(data.id)

        assert payload.share.recipient_entity_type == UserEntityType()
        assert payload.share.recipient_entity_id == recipient_id
        assert payload.share.recipient_email is None
        assert payload.share.expires_at == expires_at

    async def test_accepted_email_share_fills_accepting_user(self) -> None:
        recipient_id = uuid4()
        data = _share_data(
            recipient=RuntimeEntityID(UserEntityType(), recipient_id),
            recipient_email="invitee@example.com",
            status=EntityShareStatus.ACCEPTED,
            expires_at=None,
        )

        payload = await _adapter(data).get(data.id)

        assert payload.share.recipient_entity_type == UserEntityType()
        assert payload.share.recipient_entity_id == recipient_id
        assert payload.share.recipient_email == "invitee@example.com"

    async def test_email_only_recipient_leaves_type_and_id_empty(self) -> None:
        data = _share_data(
            recipient=None,
            recipient_email="invitee@example.com",
            status=EntityShareStatus.PENDING,
            expires_at=None,
        )

        payload = await _adapter(data).get(data.id)

        assert payload.share.recipient_entity_type is None
        assert payload.share.recipient_entity_id is None
        assert payload.share.recipient_email == "invitee@example.com"
