"""``AppConfig.config(keys:)``: the merged config narrowed to the named top-level keys."""

from __future__ import annotations

from typing import Any

import pytest
from strawberry.federation import Schema

from ai.backend.common.dto.manager.v2.app_config.response import AppConfigNode
from ai.backend.manager.api.gql.app_config.types import AppConfigGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_federation_type,
    gql_root_field,
)
from ai.backend.manager.api.gql.schema import public_schema, schema

_MERGED: dict[str, Any] = {
    "themeFamily": "dark",
    "banner": {"text": "hi"},
    "pinned": [1, 2],
    "off": None,
}


@gql_federation_type(BackendAIGQLMeta(added_version="26.9.0", description="Test query."))
class _Query:
    @gql_root_field(BackendAIGQLMeta(added_version="26.9.0", description="Test field."))
    def app_configs(self) -> list[AppConfigGQL]:
        return [AppConfigGQL.from_pydantic(AppConfigNode(config_name="theme", config=_MERGED))]


_SCHEMA = Schema(query=_Query)


async def _config(arguments: str) -> dict[str, Any]:
    result = await _SCHEMA.execute(f"{{ appConfigs {{ config{arguments} }} }}")
    assert result.errors is None
    assert result.data is not None
    return result.data["appConfigs"][0]["config"]


class TestConfigKeys:
    async def test_without_keys_the_whole_merge_is_returned(self) -> None:
        assert await _config("") == _MERGED

    async def test_only_the_named_keys_are_returned(self) -> None:
        assert await _config('(keys: ["themeFamily"])') == {"themeFamily": "dark"}

    async def test_a_value_is_returned_whole(self) -> None:
        assert await _config('(keys: ["banner", "pinned"])') == {
            "banner": {"text": "hi"},
            "pinned": [1, 2],
        }

    async def test_a_key_holding_null_is_kept(self) -> None:
        assert await _config('(keys: ["off"])') == {"off": None}

    async def test_a_key_no_fragment_holds_is_left_out(self) -> None:
        assert await _config('(keys: ["themeFamily", "missing"])') == {"themeFamily": "dark"}

    async def test_empty_keys_return_an_empty_object(self) -> None:
        assert await _config("(keys: [])") == {}

    @pytest.mark.parametrize("arguments", ["(keys: null)", ""])
    async def test_null_keys_return_every_key(self, arguments: str) -> None:
        assert await _config(arguments) == _MERGED


class TestSubgraphs:
    @pytest.mark.parametrize("subgraph", ["main", "public"])
    def test_both_subgraphs_expose_the_keys_argument(self, subgraph: str) -> None:
        sdl = (schema if subgraph == "main" else public_schema).as_str()

        app_config = sdl.split("type AppConfig ", 1)[1].split("\n}\n", 1)[0]
        assert "keys: [String!] = null" in app_config
