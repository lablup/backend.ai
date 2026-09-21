"""The by-name resource policy fields read the caller's own policy within their user
scope and answer for any other name through the lookup."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.api.gql_legacy.schema import Query

_OWN_POLICY = object()
_NAMED_POLICY = object()
_CALLER = uuid.uuid4()


@dataclass(frozen=True)
class _Family:
    label: str
    resolve: Callable[[Any, graphene.ResolveInfo, str | None], Awaitable[Any]]
    processor: str
    own_loader: str
    name_loader: str


_KEYPAIR = _Family(
    label="keypair",
    resolve=Query.resolve_keypair_resource_policy,
    processor="keypair_resource_policy",
    own_loader="KeyPairResourcePolicy.by_ak",
    name_loader="KeyPairResourcePolicy.by_name",
)
_USER = _Family(
    label="user",
    resolve=Query.resolve_user_resource_policy,
    processor="user_resource_policy",
    own_loader="UserResourcePolicy.by_user",
    name_loader="UserResourcePolicy.by_name",
)


@dataclass(frozen=True)
class _ByNameCase:
    label: str
    family: _Family
    own_items: list[object]
    looked_up: list[str]


class TestResourcePolicyByName:
    @pytest.fixture
    def make_info(self) -> Callable[[_Family, list[object]], graphene.ResolveInfo]:
        def _make(family: _Family, own_items: list[object]) -> graphene.ResolveInfo:
            ctx = MagicMock()
            ctx.access_key = "AKIATEST"
            ctx.user = {"uuid": _CALLER}
            processor = getattr(ctx.processors, family.processor)
            processor.search.run = AsyncMock(return_value=MagicMock(items=own_items))
            processor.lookup.run = AsyncMock()
            loaders = {
                family.own_loader: MagicMock(load=AsyncMock(return_value=_OWN_POLICY)),
                family.name_loader: MagicMock(load=AsyncMock(return_value=_NAMED_POLICY)),
            }
            ctx.dataloader_manager.get_loader = MagicMock(
                side_effect=lambda _ctx, key: loaders[key]
            )
            info = MagicMock(spec=graphene.ResolveInfo)
            info.context = ctx
            return info

        return _make

    @pytest.mark.parametrize(
        "case",
        [
            _ByNameCase(
                label="keypair-own",
                family=_KEYPAIR,
                own_items=[object()],
                looked_up=[],
            ),
            _ByNameCase(
                label="keypair-other",
                family=_KEYPAIR,
                own_items=[],
                looked_up=["default"],
            ),
            _ByNameCase(
                label="user-own",
                family=_USER,
                own_items=[object()],
                looked_up=[],
            ),
            _ByNameCase(
                label="user-other",
                family=_USER,
                own_items=[],
                looked_up=["default"],
            ),
        ],
        ids=lambda case: case.label,
    )
    async def test_the_own_policy_is_read_in_the_user_scope_and_any_other_through_the_lookup(
        self,
        make_info: Callable[[_Family, list[object]], graphene.ResolveInfo],
        case: _ByNameCase,
    ) -> None:
        info = make_info(case.family, case.own_items)
        processor = getattr(info.context.processors, case.family.processor)

        result = await case.family.resolve(None, info, "default")

        assert result is _NAMED_POLICY
        own_read = processor.search.run.await_args.args[0]
        assert [scope.scope_id() for scope in own_read.searcher.scopes] == [UserID(_CALLER)]
        assert [call.args[0].name for call in processor.lookup.run.await_args_list] == (
            case.looked_up
        )

    @pytest.mark.parametrize("family", [_KEYPAIR, _USER], ids=lambda family: family.label)
    async def test_without_a_name_the_caller_gets_their_own_policy_unchecked(
        self,
        make_info: Callable[[_Family, list[object]], graphene.ResolveInfo],
        family: _Family,
    ) -> None:
        info = make_info(family, [])
        processor = getattr(info.context.processors, family.processor)

        result = await family.resolve(None, info, None)

        assert result is _OWN_POLICY
        assert processor.search.run.await_count == 0
        assert processor.lookup.run.await_count == 0
