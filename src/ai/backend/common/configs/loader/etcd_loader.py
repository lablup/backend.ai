from collections.abc import Mapping
from typing import Any, override

from ai.backend.common.configs.loader.types import AbstractConfigLoader
from ai.backend.common.etcd import AsyncEtcd


class EtcdConfigLoader(AbstractConfigLoader):
    _etcd: AsyncEtcd
    _prefix: str

    def __init__(self, etcd: AsyncEtcd, prefix: str) -> None:
        self._etcd = etcd
        self._prefix = prefix

    @override
    async def load(self) -> Mapping[str, Any]:
        return await self._etcd.get_prefix(self._prefix)

    @property
    def source_name(self) -> str:
        return f"etcd:{self._prefix}"
