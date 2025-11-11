from collections.abc import AsyncGenerator, Iterable, Mapping
from typing import Optional, override

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
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.types import QueueSentinel


class AgentEtcdError(BackendAIError):
    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


# AgentEtcdClientView inherits from AsyncEtcd, but really it's just composing an AsyncEtcd instance
# and acting as an adaptor. Inheritance is made only to make the type checker happy, and the places
# that use AsyncEtcd really should not take the concrete implementation type AsyncEtcd, but rather
# the interface type AbstractKVStore. In the current codebase, manually modifying places that
# currently take in an AsyncEtcd instance to instead take in AbstractKVStore would be too invasive.
class AgentEtcdClientView(AsyncEtcd, AbstractKVStore):
    _etcd: AsyncEtcd
    _config: AgentUnifiedConfig

    def __init__(
        self,
        etcd: AsyncEtcd,
        config: AgentUnifiedConfig,
    ) -> None:
        self._etcd = etcd
        self._config = config

    def _augment_scope_prefix_map(
        self,
        scope_prefix_map: Optional[Mapping[ConfigScopes, str]],
    ) -> Mapping[ConfigScopes, str]:
        if scope_prefix_map is None:
            scope_prefix_map = {}

        agent_config = self._config.agent
        return {
            **scope_prefix_map,
            ConfigScopes.SGROUP: f"sgroup/{agent_config.scaling_group}",
            ConfigScopes.NODE: f"nodes/agents/{agent_config.id}",
        }

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
