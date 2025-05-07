from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional, Union

from ai.backend.common import config
from ai.backend.manager.config.loader.type import AbstractConfigLoader


class TomlConfigLoader(AbstractConfigLoader):
    discovered_path: Optional[Path]

    def __init__(self, path: Optional[Union[Path, str]], daemon_name: str):
        self.path = path
        self.daemon_name = daemon_name
        self.discovered_path = None

    async def load(self) -> Mapping[str, Any]:
        raw_cfg, discovered_path = config.read_from_file(self.path, self.daemon_name)
        self.discovered_path = discovered_path
        return raw_cfg
