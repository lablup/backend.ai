from typing import Any, Mapping, Sequence, override

from ai.backend.manager.config.loader.types import AbstractConfigLoader


class ConfigOverrider(AbstractConfigLoader):
    def __init__(
        self,
        overrides: Sequence[tuple[tuple[str, ...], Any]],
    ) -> None:
        self._overrides = overrides

    @override
    async def load(self) -> Mapping[str, Any]:
        cfg: dict[str, Any] = {}

        def set_key(path: Sequence[str], value: Any) -> None:
            node = cfg
            for key in path[:-1]:
                node = node.setdefault(key, {})
            node[path[-1]] = value

        for path, val in self._overrides:
            set_key(path, val)

        return cfg
