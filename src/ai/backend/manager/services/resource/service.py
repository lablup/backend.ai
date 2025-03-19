from ai.backend.common.types import RedisConnectionInfo
from ai.backend.manager.config import SharedConfig
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry


class ResourceService:
    _db: ExtendedAsyncSAEngine
    _shared_config: SharedConfig
    _agent_registry: AgentRegistry
    _redis_stat: RedisConnectionInfo

    # TODO: 인자들 한 타입으로 묶을 것.
    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        agent_registry: AgentRegistry,
        redis_stat: RedisConnectionInfo,
        shared_config: SharedConfig,
    ) -> None:
        self._db = db
        self._agent_registry = agent_registry
        self._redis_stat = redis_stat
        self._shared_config = shared_config
