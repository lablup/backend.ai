from unittest.mock import AsyncMock

import pytest

from ai.backend.common import redis_helper
from ai.backend.common.bgtask import BackgroundTaskManager
from ai.backend.common.config import redis_config_iv
from ai.backend.common.defs import REDIS_STREAM_DB, RedisRole
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.events import EventDispatcher, EventProducer
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.types import AGENTID_MANAGER, EtcdRedisConfig
from ai.backend.manager.idle import init_idle_checkers
from ai.backend.manager.plugin.monitor import ManagerErrorPluginContext
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs


@pytest.fixture
async def processors(
    etcd_fixture,
    extra_fixtures,
    database_fixture,
    database_engine,
    registry_ctx,
    shared_config,
    local_config,
):
    etcd = AsyncEtcd(
        local_config["etcd"]["addr"],
        local_config["etcd"]["namespace"],
        {
            ConfigScopes.GLOBAL: "",
        },
        credentials=None,
    )

    agent_registry, _, _, _, _, _, _ = registry_ctx
    ectx = ManagerErrorPluginContext(etcd, local_config)

    node_id = local_config["manager"]["id"]

    raw_redis_config = await etcd.get_prefix("config/redis")
    local_config["redis"] = redis_config_iv.check(raw_redis_config)
    etcd_redis_config = EtcdRedisConfig.from_dict(local_config["redis"])

    redis_stream = redis_helper.get_redis_object(
        etcd_redis_config.get_override_config(RedisRole.STREAM),
        name="stream",
        db=REDIS_STREAM_DB,
    )

    mq = RedisQueue(
        redis_stream,
        RedisMQArgs(
            stream_key="events",
            group_name="manager",
            node_id=node_id,
        ),
    )

    distributed_lock_factory = AsyncMock()

    event_producer = EventProducer(
        mq,
        source=AGENTID_MANAGER,
        log_events=False,
    )
    event_dispatcher = EventDispatcher(
        mq,
        log_events=False,
    )

    background_task_manager = BackgroundTaskManager(
        redis_stream,
        event_producer,
    )

    idle_checker_host = await init_idle_checkers(
        database_engine,
        shared_config,
        event_dispatcher,
        event_producer,
        distributed_lock_factory,
    )

    session_service = SessionService(
        SessionServiceArgs(
            db=database_engine,
            agent_registry=agent_registry,
            background_task_manager=background_task_manager,
            error_monitor=ectx,
            idle_checker_host=idle_checker_host,
        )
    )
    return SessionProcessors(session_service, [])
