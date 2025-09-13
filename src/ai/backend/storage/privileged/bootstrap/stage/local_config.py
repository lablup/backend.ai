import sys
from dataclasses import dataclass
from pathlib import Path
from typing import override

from ai.backend.common.config import ConfigurationError
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.logging import LogLevel

from ...config import StorageProxyPrivilegedWorkerConfig, load_local_config


@dataclass
class ConfigSpec:
    config_path: Path
    log_level: LogLevel


class ConfigSpecGenerator(ArgsSpecGenerator[ConfigSpec]):
    pass


@dataclass
class ConfigResult:
    local_config: StorageProxyPrivilegedWorkerConfig


class ConfigProvisioner(Provisioner[ConfigSpec, ConfigResult]):
    @property
    @override
    def name(self) -> str:
        return "storage-worker-config"

    @override
    async def setup(self, spec: ConfigSpec) -> ConfigResult:
        try:
            local_config = load_local_config(spec.config_path, log_level=spec.log_level)
        except ConfigurationError:
            print(
                "ConfigurationError: Could not read or validate the storage-proxy local config:",
                file=sys.stderr,
            )
            raise
        return ConfigResult(local_config=local_config)

    @override
    async def teardown(self, resource: ConfigResult) -> None:
        pass


class ConfigStage(ProvisionStage[ConfigSpec, ConfigResult]):
    pass
