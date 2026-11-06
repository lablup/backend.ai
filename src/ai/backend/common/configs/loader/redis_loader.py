from __future__ import annotations

from ai.backend.common.configs.loader.etcd_loader import EtcdConfigLoader
from ai.backend.common.configs.loader.loader_chain import merge_configs
from ai.backend.common.configs.loader.local_only_filter import LocalOnlyFieldFilter
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.etcd import AsyncEtcd


async def load_redis_config(etcd: AsyncEtcd, local_redis: RedisConfig | None) -> RedisConfig:
    """Merge etcd `config/redis` over `local_redis`; the local-only fields come only from `local_redis`."""
    etcd_loader = LocalOnlyFieldFilter(EtcdConfigLoader(etcd, prefix="config/redis"), RedisConfig)
    # Validate each source first so that both use the same key spellings before merging.
    etcd_redis = RedisConfig.model_validate(await etcd_loader.load()).model_dump(exclude_unset=True)
    local = local_redis.model_dump(exclude_unset=True) if local_redis is not None else {}
    return RedisConfig.model_validate(merge_configs(local, etcd_redis))
