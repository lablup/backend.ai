from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional, Union, override

from ai.backend.common import config
from ai.backend.manager.config.loader.types import AbstractConfigLoader


class TomlConfigLoader(AbstractConfigLoader):
    discovered_path: Optional[Path]

    def __init__(self, path: Optional[Union[Path, str]], daemon_name: str) -> None:
        self._path = path
        self._daemon_name = daemon_name
        self.discovered_path = None

    @override
    async def load(self) -> Mapping[str, Any]:
        raw_cfg, discovered_path = config.read_from_file(self._path, self._daemon_name)
        self.discovered_path = discovered_path
        return raw_cfg
