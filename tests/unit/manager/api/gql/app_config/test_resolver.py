"""Unit tests for the merged AppConfig GraphQL type and resolvers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.app_config.request import (
    MyGetAppConfigsInput,
    PublicGetAppConfigsInput,
)
from ai.backend.common.dto.manager.v2.app_config.response import (
    AppConfigNode,
    GetAppConfigsPayload,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import AppConfigFragmentNode
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.api.gql.app_config import resolver
from ai.backend.manager.api.gql.app_config.types import AppConfigGQL

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass(frozen=True)
class _MergedReadCase:
    """One of the two merged-read root fields and the adapter method behind it."""

    field: str
    called_adapter_method: str
    unused_adapter_method: str
    input_type: type[MyGetAppConfigsInput] | type[PublicGetAppConfigsInput]


@pytest.fixture
def public_fragment() -> AppConfigFragmentNode:
    return AppConfigFragmentNode(
        id=AppConfigFragmentID(uuid.uuid4()),
        config_name="theme",
        scope_type=AppConfigScopeType.PUBLIC,
        scope_id=None,
        config={"color": "light"},
        created_at=_NOW,
        updated_at=_NOW,
    )


@pytest.fixture
def user_fragment() -> AppConfigFragmentNode:
    return AppConfigFragmentNode(
        id=AppConfigFragmentID(uuid.uuid4()),
        config_name="theme",
        scope_type=AppConfigScopeType.USER,
        scope_id=AppConfigScopeID(uuid.uuid4()),
        config={"color": "dark"},
        created_at=_NOW,
        updated_at=_NOW,
    )


@pytest.fixture
def payload(
    public_fragment: AppConfigFragmentNode, user_fragment: AppConfigFragmentNode
) -> GetAppConfigsPayload:
    """One merged name that two fragments contributed to, and one nothing contributed to."""
    return GetAppConfigsPayload(
        app_configs=[
            AppConfigNode(
                config_name="theme",
                merged_config={"color": "dark"},
                fragments=[public_fragment, user_fragment],
            ),
            AppConfigNode(config_name="menu", merged_config={}, fragments=[]),
        ]
    )


@pytest.fixture
def info(case: _MergedReadCase, payload: GetAppConfigsPayload) -> MagicMock:
    info = MagicMock()
    setattr(
        info.context.adapters.app_config,
        case.called_adapter_method,
        AsyncMock(return_value=payload),
    )
    return info


class TestAppConfigGQL:
    def test_from_pydantic_converts_the_nested_fragments_in_order(
        self,
        public_fragment: AppConfigFragmentNode,
        user_fragment: AppConfigFragmentNode,
    ) -> None:
        node = AppConfigNode(
            config_name="theme",
            merged_config={"color": "dark"},
            fragments=[public_fragment, user_fragment],
        )

        gql = AppConfigGQL.from_pydantic(node)

        assert gql.config_name == "theme"
        assert cast(dict[str, Any], gql.merged_config) == {"color": "dark"}
        assert [f.id for f in gql.fragments] == [str(public_fragment.id), str(user_fragment.id)]
        assert [f.scope_type for f in gql.fragments] == [
            AppConfigScopeType.PUBLIC,
            AppConfigScopeType.USER,
        ]

    def test_from_pydantic_keeps_an_uncontributed_name_as_an_empty_merge(self) -> None:
        gql = AppConfigGQL.from_pydantic(
            AppConfigNode(config_name="menu", merged_config={}, fragments=[])
        )

        assert gql.config_name == "menu"
        assert cast(dict[str, Any], gql.merged_config) == {}
        assert gql.fragments == []


@pytest.mark.parametrize(
    "case",
    [
        _MergedReadCase(
            field="my_app_configs",
            called_adapter_method="my_get_app_configs",
            unused_adapter_method="public_get_app_configs",
            input_type=MyGetAppConfigsInput,
        ),
        _MergedReadCase(
            field="public_app_configs",
            called_adapter_method="public_get_app_configs",
            unused_adapter_method="my_get_app_configs",
            input_type=PublicGetAppConfigsInput,
        ),
    ],
    ids=lambda case: case.field,
)
class TestMergedReadResolvers:
    """Both root fields take the same batch of names — only the scope they imply differs."""

    async def test_passes_the_requested_names_to_its_own_adapter_method(
        self, case: _MergedReadCase, info: MagicMock
    ) -> None:
        await getattr(resolver, case.field).base_resolver(info, ["theme", "menu"])

        called = getattr(info.context.adapters.app_config, case.called_adapter_method)
        called.assert_awaited_once_with(case.input_type(config_names=["theme", "menu"]))
        getattr(info.context.adapters.app_config, case.unused_adapter_method).assert_not_called()

    async def test_returns_one_node_per_requested_name_in_order(
        self, case: _MergedReadCase, info: MagicMock
    ) -> None:
        result = await getattr(resolver, case.field).base_resolver(info, ["theme", "menu"])

        assert [node.config_name for node in result] == ["theme", "menu"]
        assert cast(dict[str, Any], result[0].merged_config) == {"color": "dark"}
        assert len(result[0].fragments) == 2
        assert cast(dict[str, Any], result[1].merged_config) == {}
        assert result[1].fragments == []
