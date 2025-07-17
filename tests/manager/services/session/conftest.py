from unittest.mock import AsyncMock

import pytest

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.config import redis_config_iv
from ai.backend.common.defs import REDIS_STREAM_DB, RedisRole
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.types import AGENTID_MANAGER, RedisProfileTarget
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
    local_config,
) -> SessionProcessors:
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
    etcd_redis_config = RedisProfileTarget.from_dict(local_config["redis"])

    redis_target = etcd_redis_config.profile_target(RedisRole.STREAM)
    redis_stream = await ValkeyStreamClient.create(
        redis_target,
        human_readable_name="stream",
        db_id=REDIS_STREAM_DB,
    )

    mq = RedisQueue(
        redis_stream,
        redis_target,
        RedisMQArgs(
            anycast_stream_key="events",
            broadcast_channel="manager_broadcast",
            consume_stream_keys={"events"},
            subscribe_channels=None,
            group_name="manager",
            node_id=node_id,
            db=REDIS_STREAM_DB,
        ),
    )

    event_producer = EventProducer(
        mq,
        source=AGENTID_MANAGER,
        log_events=False,
    )

    background_task_manager = BackgroundTaskManager(
        event_producer,
    )

    # Mock idle_checker_host for testing
    idle_checker_host = AsyncMock()

    # Mock the complex dependencies for testing
    session_service = SessionService(
        SessionServiceArgs(
            agent_registry=agent_registry,
            event_fetcher=AsyncMock(),
            background_task_manager=background_task_manager,
            event_hub=AsyncMock(),
            error_monitor=ectx,
            idle_checker_host=idle_checker_host,
            session_repository=AsyncMock(),
            admin_session_repository=AsyncMock(),
        )
    )
    return SessionProcessors(session_service, [])
