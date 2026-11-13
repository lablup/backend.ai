"""The legacy groups query keeps the requested project types for a regular user."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest
from pytest_mock import MockerFixture

from ai.backend.manager.api.gql_legacy.group import Group
from ai.backend.manager.api.gql_legacy.schema import Query
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.user.row import UserRole


class TestResolveGroupsForUser:
    @pytest.fixture
    def info(self) -> graphene.ResolveInfo:
        ctx = MagicMock()
        ctx.user = {"role": UserRole.USER, "domain_name": "default", "uuid": uuid.uuid4()}
        info = MagicMock(spec=graphene.ResolveInfo)
        info.context = ctx
        return info

    @pytest.fixture
    def batch_load_by_user(self, mocker: MockerFixture) -> AsyncMock:
        return mocker.patch.object(Group, "batch_load_by_user", AsyncMock(return_value=[[]]))

    @pytest.mark.parametrize(
        ("requested", "expected"),
        [
            (["GENERAL", "MODEL_STORE"], [ProjectType.GENERAL, ProjectType.MODEL_STORE]),
            (["MODEL_STORE"], [ProjectType.MODEL_STORE]),
            (None, [ProjectType.GENERAL]),
        ],
        ids=["general-and-model-store", "model-store-only", "no-type-reads-general"],
    )
    async def test_a_user_reads_the_requested_types_of_their_projects(
        self,
        info: graphene.ResolveInfo,
        batch_load_by_user: AsyncMock,
        requested: list[str] | None,
        expected: list[ProjectType],
    ) -> None:
        await Query.resolve_groups(None, info, is_active=True, type=requested)

        call = batch_load_by_user.await_args
        assert call is not None
        assert call.kwargs["type"] == expected

    async def test_an_unknown_type_is_rejected_as_an_invalid_request(
        self,
        info: graphene.ResolveInfo,
        batch_load_by_user: AsyncMock,
    ) -> None:
        with pytest.raises(InvalidAPIParameters):
            await Query.resolve_groups(None, info, is_active=True, type=["NOPE"])

        batch_load_by_user.assert_not_awaited()
