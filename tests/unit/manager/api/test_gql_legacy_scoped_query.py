"""
Regression test for scoped_query: the `project` parameter must not be
silently overridden by `group_id`. (BA-4280)
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import graphene
import pytest

from ai.backend.manager.api.gql_legacy.base import scoped_query
from ai.backend.manager.models.user import UserRole


class TestScopedQuery:
    """Test fixes for scoped_query bugs BA-4280."""

    @pytest.fixture
    def mock_graphene_info(self) -> MagicMock:
        """Mock GraphQL ResolveInfo with SUPERADMIN context."""
        ctx = MagicMock()
        ctx.user = {"role": UserRole.SUPERADMIN, "domain_name": "default", "uuid": uuid.uuid4()}
        ctx.access_key = "test-key"
        info = MagicMock(spec=graphene.ResolveInfo)
        info.context = ctx
        return info

    @pytest.mark.asyncio
    async def test_project_param_preserved(self, mock_graphene_info: MagicMock) -> None:
        """Regression: project was silently overridden by group_id in scoped_query."""
        project_id = uuid.uuid4()
        group_id = uuid.uuid4()
        received: dict[str, Any] = {}

        @scoped_query(autofill_user=False, user_key="user_uuid")
        async def _mock_resolver(
            _root: Any,
            _info: graphene.ResolveInfo,
            *,
            project: uuid.UUID | None = None,
            group_id: uuid.UUID | None = None,
            domain_name: str | None = None,
            user_uuid: uuid.UUID | None = None,
        ) -> None:
            received.update(project=project, group_id=group_id)

        await _mock_resolver(None, mock_graphene_info, project=project_id, group_id=group_id)

        assert received["project"] == project_id
        assert received["group_id"] == group_id
