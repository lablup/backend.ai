"""Unit tests for AuditLogV2GQL.actor resolver (acted_as → user_loader)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

from ai.backend.common.dto.manager.v2.audit_log.response import AuditLogNode
from ai.backend.common.dto.manager.v2.audit_log.types import AuditLogStatus
from ai.backend.manager.api.gql.audit_log.types.node import AuditLogV2GQL


def _make_node(*, acted_as: str | None) -> AuditLogV2GQL:
    dto = AuditLogNode(
        id=uuid.uuid4(),
        action_id=uuid.uuid4(),
        entity_type="vfolder",
        operation="search",
        entity_id="entity-1",
        created_at=datetime(2026, 7, 10, tzinfo=UTC),
        request_id="req-1",
        triggered_by=str(uuid.uuid4()),
        acted_as=acted_as,
        description="test",
        duration=None,
        status=AuditLogStatus.SUCCESS,
    )
    return AuditLogV2GQL.from_pydantic(dto)


def _info_with_loader(loader: AsyncMock) -> Any:
    info = MagicMock()
    info.context.data_loaders.user_loader.load = loader
    return info


async def _resolve_actor(node: AuditLogV2GQL, info: Any) -> Any:
    # On class access the field descriptor exposes the raw resolver function.
    return await cast(Any, AuditLogV2GQL.actor)(node, info)


class TestActorResolver:
    """Tests for AuditLogV2GQL.actor: resolve the acting user from acted_as."""

    async def test_resolves_acting_user_from_acted_as(self) -> None:
        """acted_as UUID should be loaded via user_loader and returned."""
        acted_as = str(uuid.uuid4())
        loader = AsyncMock(return_value="ACTING_USER")
        result = await _resolve_actor(_make_node(acted_as=acted_as), _info_with_loader(loader))
        assert result == "ACTING_USER"
        loader.assert_awaited_once_with(uuid.UUID(acted_as))

    async def test_none_when_acted_as_absent(self) -> None:
        """A system-triggered row (acted_as None) resolves to None without a load."""
        loader = AsyncMock()
        result = await _resolve_actor(_make_node(acted_as=None), _info_with_loader(loader))
        assert result is None
        loader.assert_not_awaited()

    async def test_none_when_acted_as_not_a_uuid(self) -> None:
        """A malformed acted_as resolves to None without a load."""
        loader = AsyncMock()
        result = await _resolve_actor(_make_node(acted_as="not-a-uuid"), _info_with_loader(loader))
        assert result is None
        loader.assert_not_awaited()

    async def test_none_when_user_loader_misses(self) -> None:
        """A dangling acted_as (loader returns None) resolves to None."""
        loader = AsyncMock(return_value=None)
        result = await _resolve_actor(_make_node(acted_as=str(uuid.uuid4())), _info_with_loader(loader))
        assert result is None
