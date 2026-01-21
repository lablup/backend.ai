from collections.abc import Mapping
from pathlib import Path
from typing import Any, override

from ai.backend.common import config
from ai.backend.manager.config.loader.types import AbstractConfigLoader


class TomlConfigLoader(AbstractConfigLoader):
    _config_path: Path
    _daemon_name: str

    def __init__(self, config_path: Path | str, daemon_name: str) -> None:
        self._config_path = Path(config_path)
        self._daemon_name = daemon_name

    @override
    async def load(self) -> Mapping[str, Any]:
        raw_cfg, _ = config.read_from_file(self._config_path, self._daemon_name)
        return raw_cfg
