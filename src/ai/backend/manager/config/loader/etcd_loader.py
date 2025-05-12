from collections.abc import Mapping
from typing import Any, override

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.config.loader.types import AbstractConfigLoader


class EtcdCommonConfigLoader(AbstractConfigLoader):
    _etcd: AsyncEtcd

    def __init__(self, etcd: AsyncEtcd):
        self._etcd = etcd

    @override
    async def load(self) -> Mapping[str, Any]:
        raw_cfg = await self._etcd.get_prefix("ai/backend/config/common")
        return raw_cfg


class EtcdManagerConfigLoader(AbstractConfigLoader):
    _etcd: AsyncEtcd

    def __init__(self, etcd: AsyncEtcd):
        self._etcd = etcd

    @override
    async def load(self) -> Mapping[str, Any]:
        raw_cfg = await self._etcd.get_prefix("ai/backend/config/manager")
        return raw_cfg
