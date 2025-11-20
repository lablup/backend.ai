from collections.abc import AsyncGenerator, Iterable, Mapping
from typing import ChainMap, MutableMapping, Optional, cast, override

from etcd_client import CondVar

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.common.etcd import (
    AbstractKVStore,
    AsyncEtcd,
    ConfigScopes,
    Event,
    GetPrefixValue,
    NestedStrKeyedMapping,
)
from ai.backend.common.types import QueueSentinel


class AgentEtcdClientView(AbstractKVStore):
    _etcd: AsyncEtcd
    _config: AgentUnifiedConfig

    def __init__(
        self,
        etcd: AsyncEtcd,
        config: AgentUnifiedConfig,
    ) -> None:
        self._etcd = etcd
        self._config = config

    @property
    def _agent_scope_prefix_map(self) -> Mapping[ConfigScopes, str]:
        """
        This is kept as a @property method instead of a simple variable, because this way any
        updates that are made to the config object (e.g. scaling group) is correctly applied as the
        scope prefix mapping is recalculated every time.
        """
        return {
            ConfigScopes.SGROUP: f"sgroup/{self._config.agent.scaling_group}",
            ConfigScopes.NODE: f"nodes/agents/{self._config.agent.defaulted_id}",
        }

    def _augment_scope_prefix_map(
        self,
        override: Optional[Mapping[ConfigScopes, str]],
    ) -> Mapping[ConfigScopes, str]:
        """
        This stub ensures immutable usage of the ChainMap because ChainMap does *not*
        have the immutable version in typeshed.
        (ref: https://github.com/python/typeshed/issues/6042)
        """
        if not override:
            return self._agent_scope_prefix_map

        return ChainMap(
            cast(MutableMapping, override), cast(MutableMapping, self._agent_scope_prefix_map)
        )

    @override
    async def put(
        self,
        key: str,
        val: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Optional[Mapping[ConfigScopes, str]] = None,
    ):
        scope_prefix_map = self._augment_scope_prefix_map(scope_prefix_map)
        await self._etcd.put(key, val, scope=scope, scope_prefix_map=scope_prefix_map)

    @override
    async def put_prefix(
        self,
        key: str,
        dict_obj: NestedStrKeyedMapping,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Optional[Mapping[ConfigScopes, str]] = None,
    ):
        scope_prefix_map = self._augment_scope_prefix_map(scope_prefix_map)
        await self._etcd.put_prefix(key, dict_obj, scope=scope, scope_prefix_map=scope_prefix_map)

    @override
    async def put_dict(
        self,
        flattened_dict_obj: Mapping[str, str],
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Optional[Mapping[ConfigScopes, str]] = None,
    ):
        scope_prefix_map = self._augment_scope_prefix_map(scope_prefix_map)
        await self._etcd.put_dict(
            flattened_dict_obj, scope=scope, scope_prefix_map=scope_prefix_map
        )

    @override
    async def get(
        self,
        key: str,
        *,
        scope: ConfigScopes = ConfigScopes.MERGED,
        scope_prefix_map: Optional[Mapping[ConfigScopes, str]] = None,
    ) -> Optional[str]:
        scope_prefix_map = self._augment_scope_prefix_map(scope_prefix_map)
        return await self._etcd.get(key, scope=scope, scope_prefix_map=scope_prefix_map)

    @override
    async def get_prefix(
        self,
        key_prefix: str,
        *,
        scope: ConfigScopes = ConfigScopes.MERGED,
        scope_prefix_map: Optional[Mapping[ConfigScopes, str]] = None,
    ) -> GetPrefixValue:
        scope_prefix_map = self._augment_scope_prefix_map(scope_prefix_map)
        return await self._etcd.get_prefix(
            key_prefix,
            scope=scope,
            scope_prefix_map=scope_prefix_map,
        )

    @override
    async def replace(
        self,
        key: str,
        initial_val: str,
        new_val: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Optional[Mapping[ConfigScopes, str]] = None,
    ) -> bool:
        scope_prefix_map = self._augment_scope_prefix_map(scope_prefix_map)
        return await self._etcd.replace(
            key,
            initial_val,
            new_val,
            scope=scope,
            scope_prefix_map=scope_prefix_map,
        )

    @override
    async def delete(
        self,
        key: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Optional[Mapping[ConfigScopes, str]] = None,
    ):
        scope_prefix_map = self._augment_scope_prefix_map(scope_prefix_map)
        await self._etcd.delete(key, scope=scope, scope_prefix_map=scope_prefix_map)

    @override
    async def delete_multi(
        self,
        keys: Iterable[str],
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Optional[Mapping[ConfigScopes, str]] = None,
    ):
        scope_prefix_map = self._augment_scope_prefix_map(scope_prefix_map)
        await self._etcd.delete_multi(keys, scope=scope, scope_prefix_map=scope_prefix_map)

    @override
    async def delete_prefix(
        self,
        key_prefix: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Optional[Mapping[ConfigScopes, str]] = None,
    ):
        scope_prefix_map = self._augment_scope_prefix_map(scope_prefix_map)
        await self._etcd.delete_prefix(key_prefix, scope=scope, scope_prefix_map=scope_prefix_map)

    @override
    async def watch(
        self,
        key: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Optional[Mapping[ConfigScopes, str]] = None,
        once: bool = False,
        ready_event: Optional[CondVar] = None,
        cleanup_event: Optional[CondVar] = None,
        wait_timeout: Optional[float] = None,
    ) -> AsyncGenerator[QueueSentinel | Event, None]:
        scope_prefix_map = self._augment_scope_prefix_map(scope_prefix_map)
        watch_result = self._etcd.watch(
            key,
            scope=scope,
            scope_prefix_map=scope_prefix_map,
            once=once,
            ready_event=ready_event,
            cleanup_event=cleanup_event,
            wait_timeout=wait_timeout,
        )
        async for item in watch_result:
            yield item

    @override
    async def watch_prefix(
        self,
        key_prefix: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Optional[Mapping[ConfigScopes, str]] = None,
        once: bool = False,
        ready_event: Optional[CondVar] = None,
        cleanup_event: Optional[CondVar] = None,
        wait_timeout: Optional[float] = None,
    ) -> AsyncGenerator[QueueSentinel | Event, None]:
        scope_prefix_map = self._augment_scope_prefix_map(scope_prefix_map)
        watch_prefix_result = self._etcd.watch_prefix(
            key_prefix,
            scope=scope,
            scope_prefix_map=scope_prefix_map,
            once=once,
            ready_event=ready_event,
            cleanup_event=cleanup_event,
            wait_timeout=wait_timeout,
        )
        async for item in watch_prefix_result:
            yield item
