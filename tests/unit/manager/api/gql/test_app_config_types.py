"""Unit tests for the merged AppConfig GraphQL type."""

from __future__ import annotations

from typing import Any, cast

from ai.backend.common.dto.manager.v2.app_config.response import AppConfigNode
from ai.backend.manager.api.gql.app_config.types import AppConfigGQL


class TestAppConfigGQL:
    def test_from_pydantic_maps_the_merge(self) -> None:
        gql = AppConfigGQL.from_pydantic(
            AppConfigNode(config_name="theme", config={"color": "dark"})
        )

        assert gql.config_name == "theme"
        assert cast(dict[str, Any], gql.config) == {"color": "dark"}

    def test_from_pydantic_keeps_an_uncontributed_name_as_an_empty_merge(self) -> None:
        gql = AppConfigGQL.from_pydantic(AppConfigNode(config_name="menu", config={}))

        assert gql.config_name == "menu"
        assert cast(dict[str, Any], gql.config) == {}
