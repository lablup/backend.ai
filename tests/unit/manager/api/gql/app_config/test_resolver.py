"""Unit tests for the merged AppConfig GraphQL type and resolvers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.dto.manager.v2.app_config.request import (
    MyGetAppConfigsInput,
    PublicGetAppConfigsInput,
)
from ai.backend.common.dto.manager.v2.app_config.response import (
    AppConfigNode,
    GetAppConfigsPayload,
)
from ai.backend.manager.api.gql.app_config import resolver
from ai.backend.manager.api.gql.app_config.types import AppConfigGQL


@dataclass(frozen=True)
class _MergedReadCase:
    """One of the two merged-read root fields and the adapter method behind it."""

    field: str
    called_adapter_method: str
    unused_adapter_method: str
    input_type: type[MyGetAppConfigsInput] | type[PublicGetAppConfigsInput]


@pytest.fixture
def payload() -> GetAppConfigsPayload:
    """One merged name, and one nothing contributed to."""
    return GetAppConfigsPayload(
        app_configs=[
            AppConfigNode(config_name="theme", merged_config={"color": "dark"}),
            AppConfigNode(config_name="menu", merged_config={}),
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
    def test_from_pydantic_maps_the_merge(self) -> None:
        gql = AppConfigGQL.from_pydantic(
            AppConfigNode(config_name="theme", merged_config={"color": "dark"})
        )

        assert gql.config_name == "theme"
        assert cast(dict[str, Any], gql.merged_config) == {"color": "dark"}

    def test_from_pydantic_keeps_an_uncontributed_name_as_an_empty_merge(self) -> None:
        gql = AppConfigGQL.from_pydantic(AppConfigNode(config_name="menu", merged_config={}))

        assert gql.config_name == "menu"
        assert cast(dict[str, Any], gql.merged_config) == {}


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
        assert cast(dict[str, Any], result[1].merged_config) == {}
