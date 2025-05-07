from collections.abc import Mapping
from typing import Any

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.config.loader.types import AbstractConfigLoader


class LegacyEtcdLoader(AbstractConfigLoader):
    _etcd: AsyncEtcd

    def __init__(self, etcd: AsyncEtcd):
        self._etcd = etcd

    async def load(self) -> Mapping[str, Any]:
        raw_cfg = await self._etcd.get_prefix("config")
        return raw_cfg


# TODO: Implement this.
# class ETCDCofiCommonLoader(AbstractConfigLoader):
#     _etcd: AsyncEtcd

#     def __init__(self, etcd: AsyncEtcd):
#         self._etcd = etcd

#     async def load(self) -> Mapping[str, Any]:
#         raw_cfg = await self._etcd.get_prefix("ai/backend/config/commn")
#         return raw_cfg


# class ETCDCofigManagerLoader(AbstractConfigLoader):
#     _etcd: AsyncEtcd

#     def __init__(self, etcd: AsyncEtcd):
#         self._etcd = etcd

#     async def load(self) -> Mapping[str, Any]:
#         raw_cfg = await self._etcd.get_prefix("ai/backend/config/manager")
#         return raw_cfg
