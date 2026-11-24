"""modifyGroup keeps an admin inside their domain."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest
from graphene.types import inputobjecttype
from graphql import GraphQLInputObjectType, Undefined, coerce_input_value

from ai.backend.manager.api.gql_legacy.group import ModifyGroup, ModifyGroupInput
from ai.backend.manager.models.user.row import UserRole


class TestModifyGroupScope:
    @pytest.fixture
    def make_info(self) -> Callable[[UserRole], graphene.ResolveInfo]:
        """An info whose requester holds ``role`` in the domain ``default``; the project
        update answers no data."""

        def _make(role: UserRole) -> graphene.ResolveInfo:
            ctx = MagicMock()
            ctx.user = {"role": role, "domain_name": "default", "uuid": uuid.uuid4()}
            ctx.processors.project.update_project.run = AsyncMock(return_value=MagicMock(data=None))
            info = MagicMock(spec=graphene.ResolveInfo)
            info.context = ctx
            return info

        return _make

    @pytest.fixture
    def admin_info(
        self, make_info: Callable[[UserRole], graphene.ResolveInfo]
    ) -> graphene.ResolveInfo:
        return make_info(UserRole.ADMIN)

    def _props(
        self, configuration: dict[str, Any], monkeypatch: pytest.MonkeyPatch
    ) -> ModifyGroupInput:
        monkeypatch.setattr(inputobjecttype, "_INPUT_OBJECT_TYPE_DEFAULT_VALUE", Undefined)
        schema = graphene.Schema(types=[ModifyGroupInput])
        input_type = schema.graphql_schema.get_type("ModifyGroupInput")
        assert isinstance(input_type, GraphQLInputObjectType)
        props = coerce_input_value(configuration, input_type)
        assert isinstance(props, ModifyGroupInput)
        return props

    async def _mutate(self, info: graphene.ResolveInfo, props: ModifyGroupInput) -> ModifyGroup:
        # Past the role decorator, which reads the project off the DB.
        mutate = ModifyGroup.mutate.__wrapped__
        return cast(ModifyGroup, await mutate(ModifyGroup, None, info, uuid.uuid4(), props))

    async def test_an_admin_may_not_move_a_project_to_another_domain(
        self, admin_info: graphene.ResolveInfo, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result = await self._mutate(admin_info, self._props({"domainName": "other"}, monkeypatch))
        assert result.ok is False
        assert "domain" in result.msg
        admin_info.context.processors.project.update_project.run.assert_not_awaited()

    async def test_an_admin_edits_a_project_of_their_own_domain(
        self, admin_info: graphene.ResolveInfo, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result = await self._mutate(admin_info, self._props({"domainName": "default"}, monkeypatch))
        assert result.ok is True
        admin_info.context.processors.project.update_project.run.assert_awaited_once()

    async def test_a_superadmin_moves_a_project_to_another_domain(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        info = make_info(UserRole.SUPERADMIN)
        result = await self._mutate(info, self._props({"domainName": "other"}, monkeypatch))
        assert result.ok is True
        info.context.processors.project.update_project.run.assert_awaited_once()
