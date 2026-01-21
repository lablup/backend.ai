from collections.abc import Mapping, MutableMapping, Sequence
from copy import deepcopy
from typing import Any, Optional, cast, override

from ai.backend.manager.config.loader.types import AbstractConfigLoader


def merge_configs(
    dst: MutableMapping[str, Any], src: Mapping[str, Any]
) -> MutableMapping[str, Any]:
    for k, v in src.items():
        if isinstance(v, Mapping) and isinstance(dst.get(k), Mapping):
            merge_configs(dst[k], v)
        else:
            dst[k] = deepcopy(v)
    return dst


class LoaderChain(AbstractConfigLoader):
    _loaders: Sequence[AbstractConfigLoader]
    _base_config: Mapping[str, Any]

    def __init__(
        self,
        loaders: Sequence[AbstractConfigLoader],
        base_config: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self._loaders = loaders
        self._base_config = base_config or {}

    @override
    async def load(self) -> Mapping[str, Any]:
        base_config = cast(MutableMapping, deepcopy(self._base_config))
        merged: MutableMapping[str, Any] = base_config
        for loader in self._loaders:
            cfg = await loader.load()
            merged = merge_configs(merged, cfg)

        return merged
