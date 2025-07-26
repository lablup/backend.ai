"""
Usage example for the new stage-based setup system.

This demonstrates how to use the modular stage system instead of the monolithic
SetupProvisioner approach.
"""

from ai.backend.manager.setup.provisioners.message_queue import MessageQueueSpecGenerator
from ai.backend.manager.setup.provisioners.redis import RedisSpecGenerator
from ai.backend.manager.setup.stage.stage_group import create_setup_stages, setup_all_stages


async def example_setup_usage(config, db, config_provider, etcd, pidx=0):
    """
    Example of how to use the new stage-based setup system.
    """

    # Create stage group with all dependencies configured
    stage_group = create_setup_stages(
        config=config, db=db, config_provider=config_provider, etcd=etcd, pidx=pidx
    )

    # Setup all stages with proper dependency handling
    resources = await setup_all_stages(stage_group, config, db, config_provider, etcd, pidx)

    # Use the provisioned resources
    event_hub = resources["event_hub"]
    redis_clients = resources["redis"]
    message_queue = resources["message_queue"]
    event_producer = resources["event_producer"]
    repositories = resources["repositories"]

    # ... use resources in your application

    # When done, teardown in reverse order
    # await teardown_all_stages(stage_group)

    return {
        "event_hub": event_hub,
        "redis": redis_clients,
        "message_queue": message_queue,
        "event_producer": event_producer,
        "repositories": repositories,
        # ... other resources
    }


# For selective setup (only specific components needed)
async def example_selective_setup(config, db, config_provider, etcd):
    """
    Example of setting up only specific stages for lightweight deployments.
    """

    stage_group = create_setup_stages(
        config=config, db=db, config_provider=config_provider, etcd=etcd
    )

    # Setup only what you need
    await stage_group.redis.setup(RedisSpecGenerator(config))
    await stage_group.message_queue.setup(
        MessageQueueSpecGenerator(stage_group.redis, config)
    )  # depends on redis

    redis_clients = await stage_group.redis.wait_for_resource()
    message_queue = await stage_group.message_queue.wait_for_resource()

    return {"redis": redis_clients, "message_queue": message_queue}
