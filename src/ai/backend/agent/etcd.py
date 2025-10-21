from typing import Collection

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.common.data.config.types import EtcdConfigData
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.types import AgentId


class EtcdClientRegistry:
    _etcd_config: EtcdConfigData
    _etcd_clients: dict[AgentId, AsyncEtcd]
    _global_etcd: AsyncEtcd

    @property
    def global_etcd(self) -> AsyncEtcd:
        return self._global_etcd

    def __init__(self, etcd_config: EtcdConfigData) -> None:
        self._etcd_config = etcd_config
        self._etcd_clients = {}
        self._global_etcd = self._create_client(agent_id=None, scaling_group=None)

    async def close(self) -> None:
        for etcd in self._etcd_clients.values():
            await etcd.close()
        await self._global_etcd.close()

    def get_client(self, agent_id: AgentId) -> AsyncEtcd:
        return self._etcd_clients[agent_id]

    def prefill_clients(self, prefill_data: Collection[AgentUnifiedConfig]) -> None:
        for agent_config in prefill_data:
            agent_id = AgentId(agent_config.agent.id)
            self._etcd_clients[agent_id] = self._create_client(
                agent_id, agent_config.agent.scaling_group
            )

    def _create_client(self, agent_id: AgentId | None, scaling_group: str | None) -> AsyncEtcd:
        scope_prefix_map = {ConfigScopes.GLOBAL: ""}
        if scaling_group is not None:
            scope_prefix_map[ConfigScopes.SGROUP] = f"sgroup/{scaling_group}"
        if agent_id is not None:
            scope_prefix_map[ConfigScopes.NODE] = f"nodes/agents/{agent_id}"

        if self._etcd_config.user and self._etcd_config.password:
            etcd_credentials = {
                "user": self._etcd_config.user,
                "password": self._etcd_config.password,
            }
        else:
            etcd_credentials = None

        return AsyncEtcd(
            [addr.to_legacy() for addr in self._etcd_config.addrs],
            self._etcd_config.namespace,
            scope_prefix_map,
            credentials=etcd_credentials,
        )
