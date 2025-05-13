from collections.abc import Mapping, MutableMapping, Sequence
from copy import deepcopy
from typing import Any, override

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

    def __init__(self, loaders: Sequence[AbstractConfigLoader]) -> None:
        self._loaders = loaders

    @override
    async def load(self) -> Mapping[str, Any]:
        merged: MutableMapping[str, Any] = {}
        for loader in self._loaders:
            cfg = await loader.load()
            merged = merge_configs(merged, cfg)

        return merged
