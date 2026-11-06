"""modifyGroup keeps an admin inside their domain and off the resource policy. (BA-8902)"""

from __future__ import annotations

import uuid
from typing import Any, cast
from unittest.mock import MagicMock

import graphene
import pytest
from graphene.types import inputobjecttype
from graphql import GraphQLInputObjectType, Undefined, coerce_input_value

from ai.backend.manager.api.gql_legacy.group import ModifyGroup, ModifyGroupInput
from ai.backend.manager.models.user.row import UserRole


class TestModifyGroupScope:
    @pytest.fixture
    def admin_info(self) -> graphene.ResolveInfo:
        ctx = MagicMock()
        ctx.user = {"role": UserRole.ADMIN, "domain_name": "default", "uuid": uuid.uuid4()}
        info = MagicMock(spec=graphene.ResolveInfo)
        info.context = ctx
        return info

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

    async def test_an_admin_may_not_change_the_resource_policy(
        self, admin_info: graphene.ResolveInfo, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result = await self._mutate(
            admin_info, self._props({"resourcePolicy": "tier-2"}, monkeypatch)
        )
        assert result.ok is False
        assert "resource policy" in result.msg
