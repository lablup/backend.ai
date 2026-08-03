"""Unit tests for AppConfigAdapter DTO conversions and the get input contract."""

from __future__ import annotations

import pytest

from ai.backend.common.dto.manager.v2.app_config.request import (
    MyGetAppConfigsInput,
    PublicGetAppConfigsInput,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.manager.api.adapters.app_config.adapter import AppConfigAdapter
from ai.backend.manager.data.app_config.types import AppConfigData


class TestAppConfigAdapterConverters:
    def test_app_config_to_node_maps_the_merge(self) -> None:
        node = AppConfigAdapter._app_config_to_node(
            AppConfigData(config_name="theme", merged_config={"color": "dark"})
        )

        assert node.config_name == "theme"
        assert node.merged_config == {"color": "dark"}

    def test_app_config_to_node_keeps_an_empty_merge(self) -> None:
        node = AppConfigAdapter._app_config_to_node(
            AppConfigData(config_name="menu", merged_config={})
        )

        assert node.config_name == "menu"
        assert node.merged_config == {}


class TestGetAppConfigsInputs:
    """Both get inputs take the same batch of names — only the scope they imply differs."""

    @pytest.mark.parametrize(
        "input_model",
        [MyGetAppConfigsInput, PublicGetAppConfigsInput],
        ids=lambda model: model.__name__,
    )
    def test_parses_config_names(
        self, input_model: type[MyGetAppConfigsInput] | type[PublicGetAppConfigsInput]
    ) -> None:
        parsed = input_model.model_validate({"config_names": ["theme", "layout"]})

        assert parsed.config_names == ["theme", "layout"]

    @pytest.mark.parametrize(
        "input_model",
        [MyGetAppConfigsInput, PublicGetAppConfigsInput],
        ids=lambda model: model.__name__,
    )
    def test_rejects_empty_config_names(
        self, input_model: type[MyGetAppConfigsInput] | type[PublicGetAppConfigsInput]
    ) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            input_model.model_validate({"config_names": []})
