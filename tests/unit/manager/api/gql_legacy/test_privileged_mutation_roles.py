"""privileged_mutation(ADMIN) lets an admin act within their domain and turns away
every role below it, a monitor included. (BA-8902)

Exercised through createGroup: an empty name fails on the body's first line, so
reaching that error shows the decorator let the call through, without a DB.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import graphene
import pytest
from graphene.types import inputobjecttype
from graphql import GraphQLInputObjectType, Undefined, coerce_input_value

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.api.gql_legacy.group import CreateGroup, GroupInput
from ai.backend.manager.models.user.row import UserRole

DOMAIN = "default"


class TestPrivilegedMutationRoles:
    def _info(self, role: UserRole) -> graphene.ResolveInfo:
        ctx = MagicMock()
        ctx.user = {"role": role, "domain_name": DOMAIN, "uuid": uuid.uuid4()}
        info = MagicMock(spec=graphene.ResolveInfo)
        info.context = ctx
        return info

    def _props(self, domain_name: str, monkeypatch: pytest.MonkeyPatch) -> GroupInput:
        monkeypatch.setattr(inputobjecttype, "_INPUT_OBJECT_TYPE_DEFAULT_VALUE", Undefined)
        schema = graphene.Schema(types=[GroupInput])
        input_type = schema.graphql_schema.get_type("GroupInput")
        assert isinstance(input_type, GraphQLInputObjectType)
        props = coerce_input_value({"domainName": domain_name}, input_type)
        assert isinstance(props, GroupInput)
        return props

    async def _create_group(
        self, role: UserRole, domain_name: str, monkeypatch: pytest.MonkeyPatch
    ) -> CreateGroup:
        result: CreateGroup = await CreateGroup.mutate(
            None, self._info(role), name="", props=self._props(domain_name, monkeypatch)
        )
        return result

    @pytest.mark.parametrize(
        "role", [UserRole.SUPERADMIN, UserRole.ADMIN], ids=["superadmin", "admin"]
    )
    async def test_an_admin_or_above_reaches_the_mutation(
        self, role: UserRole, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with pytest.raises(InvalidAPIParameters):
            await self._create_group(role, DOMAIN, monkeypatch)

    async def test_an_admin_of_another_domain_is_turned_away(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result = await self._create_group(UserRole.ADMIN, "other-domain", monkeypatch)
        assert result.ok is False

    @pytest.mark.parametrize("role", [UserRole.MONITOR, UserRole.USER], ids=["monitor", "user"])
    async def test_a_role_below_admin_is_turned_away(
        self, role: UserRole, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result = await self._create_group(role, DOMAIN, monkeypatch)
        assert result.ok is False
