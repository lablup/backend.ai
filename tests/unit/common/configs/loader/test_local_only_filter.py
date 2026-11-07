from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import AliasChoices, BaseModel, Field

from ai.backend.common.configs.loader import LoaderChain
from ai.backend.common.configs.loader.local_only_filter import LocalOnlyFieldFilter
from ai.backend.common.configs.loader.types import AbstractConfigLoader
from ai.backend.common.meta.meta import BackendAIConfigMeta


def _meta(*, local_only: bool = False) -> BackendAIConfigMeta:
    return BackendAIConfigMeta(description="test", added_version="1.0.0", local_only=local_only)


class _Endpoint(BaseModel):
    addr: Annotated[str | None, Field(default=None), _meta()]
    token: Annotated[
        str | None,
        Field(default=None, validation_alias=AliasChoices("token", "auth-token")),
        _meta(local_only=True),
    ]


class _Root(BaseModel):
    endpoint: Annotated[_Endpoint | None, Field(default=None), _meta()]
    endpoints: Annotated[dict[str, _Endpoint], Field(default_factory=dict), _meta()]
    endpoint_list: Annotated[list[_Endpoint], Field(default_factory=list), _meta()]
    name: Annotated[str | None, Field(default=None), _meta()]


def _static_loader(config: Mapping[str, Any]) -> AbstractConfigLoader:
    loader = MagicMock(spec=AbstractConfigLoader)
    loader.load = AsyncMock(return_value=config)
    loader.source_name = "etcd:test"
    return loader


class TestLocalOnlyFieldFilter:
    @pytest.mark.parametrize(
        ("remote_config", "expected"),
        [
            pytest.param(
                {"endpoint": {"addr": "a", "token": "t"}},
                {"endpoint": {"addr": "a"}},
                id="nested-model",
            ),
            pytest.param(
                {"endpoint": {"addr": "a", "auth-token": "t"}},
                {"endpoint": {"addr": "a"}},
                id="validation-alias",
            ),
            pytest.param(
                {"endpoints": {"x": {"addr": "a", "token": "t"}, "y": {"token": "t"}}},
                {"endpoints": {"x": {"addr": "a"}, "y": {}}},
                id="dict-values",
            ),
            pytest.param(
                {"endpoint_list": [{"addr": "a", "token": "t"}, {"token": "t"}]},
                {"endpoint_list": [{"addr": "a"}, {}]},
                id="list-items",
            ),
            pytest.param(
                {"endpoint": {"addr": "a"}, "name": "n"},
                {"endpoint": {"addr": "a"}, "name": "n"},
                id="no-local-only-field",
            ),
            pytest.param(
                {"endpoint": "not-a-table", "endpoints": {"x": "not-a-table"}},
                {"endpoint": "not-a-table", "endpoints": {"x": "not-a-table"}},
                id="non-mapping-values",
            ),
        ],
    )
    async def test_drops_local_only_fields(
        self, remote_config: Mapping[str, Any], expected: Mapping[str, Any]
    ) -> None:
        loaded = await LocalOnlyFieldFilter(_static_loader(remote_config), _Root).load()

        assert loaded == expected

    async def test_does_not_mutate_wrapped_loader_output(self) -> None:
        remote_config = {"endpoint": {"token": "t"}}

        await LocalOnlyFieldFilter(_static_loader(remote_config), _Root).load()

        assert remote_config == {"endpoint": {"token": "t"}}

    async def test_local_value_survives_remote_merge(self) -> None:
        local = _static_loader({"endpoint": {"token": "local"}})
        remote = _static_loader({"endpoint": {"addr": "a", "token": "remote"}})

        loaded = await LoaderChain([local, LocalOnlyFieldFilter(remote, _Root)]).load()

        assert loaded == {"endpoint": {"addr": "a", "token": "local"}}
