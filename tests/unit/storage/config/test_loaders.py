from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.common.config import ConfigurationError
from ai.backend.common.exception import InvalidConfigError
from ai.backend.storage.config import loaders
from ai.backend.storage.config.loaders import load_local_config
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig


class TestLoadLocalConfig:
    @pytest.fixture
    def raw_cfg(self) -> dict[str, Any]:
        return {"etcd": {"password": "s3cr3t-value"}}

    @pytest.fixture
    def config_source(
        self, raw_cfg: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            loaders,
            "read_from_file",
            MagicMock(return_value=(raw_cfg, tmp_path / "storage-proxy.toml")),
        )

    @pytest.mark.usefixtures("config_source")
    def test_validation_error_is_reported_without_input_values(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(ConfigurationError):
            load_local_config(None)

        assert "s3cr3t-value" not in capsys.readouterr().err

    @pytest.mark.usefixtures("config_source")
    def test_backend_ai_error_from_a_validator_becomes_configuration_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        message = "vfs config is required when storage_type is 'vfs'"
        monkeypatch.setattr(
            StorageProxyUnifiedConfig,
            "model_validate",
            MagicMock(side_effect=InvalidConfigError(message)),
        )

        with pytest.raises(ConfigurationError):
            load_local_config(None)

        assert message in capsys.readouterr().err
