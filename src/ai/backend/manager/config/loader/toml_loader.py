from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from ai.backend.common import config
from ai.backend.manager.config.loader.types import AbstractConfigLoader


@dataclass
class TomlConfigLoaderArgs:
    path: Optional[Union[Path, str]]
    daemon_name: str


class TomlConfigLoader(AbstractConfigLoader):
    discovered_path: Optional[Path]

    def __init__(self, loader_args: TomlConfigLoaderArgs):
        self.path = loader_args.path
        self.daemon_name = loader_args.daemon_name
        self.discovered_path = None

    async def load(self) -> Mapping[str, Any]:
        raw_cfg, discovered_path = config.read_from_file(self.path, self.daemon_name)
        self.discovered_path = discovered_path
        return raw_cfg
