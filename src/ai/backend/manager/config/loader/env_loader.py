import os
from collections.abc import Mapping, Sequence
from typing import Any, override

from ai.backend.manager.config.loader.types import AbstractConfigLoader


class EnvLoader(AbstractConfigLoader):
    _envs: list[tuple[tuple[str, ...], str]]

    def __init__(self, envs: list[tuple[tuple[str, ...], str]]) -> None:
        self._envs = envs

    @override
    async def load(self) -> Mapping[str, Any]:
        cfg: dict[str, Any] = {}

        def set_key(path: Sequence[str], value: Any) -> None:
            node = cfg
            for key in path[:-1]:
                node = node.setdefault(key, {})
            node[path[-1]] = value

        for key_path, env in self._envs:
            if (val := os.getenv(env)) is not None:
                set_key(key_path, val)

        return cfg
