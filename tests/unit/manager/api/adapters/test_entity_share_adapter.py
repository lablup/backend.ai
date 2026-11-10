"""Tests for EntityShareAdapter node and filter conversion."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.dialects import postgresql

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.entity_share.request import EntityShareFilter
from ai.backend.manager.api.adapters.entity_share.adapter import EntityShareAdapter
from ai.backend.manager.data.entity_share.types import EntityShareData, EntityShareStatus
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import combine_conditions_and

_TARGET_ID = UUID("11111111-1111-1111-1111-111111111111")
_RECIPIENT_ID = UUID("22222222-2222-2222-2222-222222222222")
_pg_dialect_cls: Any = postgresql.dialect
_PG_DIALECT = _pg_dialect_cls()


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


def _to_sql(conditions: list[QueryCondition]) -> str:
    return str(
        combine_conditions_and(conditions)().compile(
            dialect=_PG_DIALECT, compile_kwargs={"literal_binds": True}
        )
    )


class TestEntityShareConvertFilter:
    @pytest.mark.parametrize(
        ("filter", "expected"),
        [
            (
                EntityShareFilter(target_entity_id=UUIDFilter(equals=_TARGET_ID)),
                f"entity_shares.target_entity_id = '{_TARGET_ID}'",
            ),
            (
                EntityShareFilter(recipient_entity_id=UUIDFilter(in_=[_RECIPIENT_ID])),
                f"entity_shares.recipient_entity_id IN ('{_RECIPIENT_ID}')",
            ),
            (
                EntityShareFilter(recipient_email=StringFilter(equals="a@example.com")),
                "entity_shares.recipient_email = 'a@example.com'",
            ),
            (
                EntityShareFilter(recipient_email=StringFilter(i_equals="A@Example.com")),
                "lower(entity_shares.recipient_email) = 'a@example.com'",
            ),
        ],
    )
    def test_each_field_narrows(self, filter: EntityShareFilter, expected: str) -> None:
        adapter = EntityShareAdapter(MagicMock())
        assert _to_sql(adapter._convert_filter(filter)) == expected
