from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Mapping, Type, cast
from uuid import uuid4

import pytest

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.types import KernelId, SessionId, SessionTypes
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.idle import (
    BaseIdleChecker,
    IdleCheckerHost,
    NetworkTimeoutIdleChecker,
    SessionLifetimeChecker,
    UtilizationIdleChecker,
    calculate_remaining_time,
    init_idle_checkers,
)
from ai.backend.manager.server import (
    background_task_ctx,
    database_ctx,
    distributed_lock_ctx,
    event_dispatcher_ctx,
    redis_ctx,
    shared_config_ctx,
)


def get_checker_from_host(
    checker_host: IdleCheckerHost, checker_type: Type[BaseIdleChecker]
) -> BaseIdleChecker:
    for checker in checker_host._checkers:
        if isinstance(checker, checker_type):
            return checker
    else:
        raise ValueError(
            f"{checker_type} not found in the checker_host. {checker_host._checkers = }"
        )


def remaining_time_calculation() -> None:
    # test 1
    # now + 10.0 == idle_baseline + timeout_period
    now = datetime(2020, 3, 1, 12, 30, second=20)
    idle_baseline = datetime(2020, 3, 1, 12, 30, second=0)
    timeout_period = timedelta(seconds=30)
    grace_period_end = None
    remaining = calculate_remaining_time(now, idle_baseline, timeout_period, grace_period_end)
    expect = 10.0
    assert expect == remaining

    # test 2
    # now + 40.0 == max(grace_period_end, idle_baseline) + timeout_period
    now = datetime(2020, 3, 1, 12, 30, second=20)
    idle_baseline = datetime(2020, 3, 1, 12, 30, second=0)
    timeout_period = timedelta(seconds=30)
    grace_period_end = datetime(2020, 3, 1, 12, 30, second=30)
    remaining = calculate_remaining_time(now, idle_baseline, timeout_period, grace_period_end)
    expect = 40.0
    assert expect == remaining

    now = datetime(2020, 3, 1, 12, 30, second=20)
    idle_baseline = datetime(2020, 3, 1, 12, 30, second=30)
    timeout_period = timedelta(seconds=30)
    grace_period_end = datetime(2020, 3, 1, 12, 30, second=20)
    remaining = calculate_remaining_time(now, idle_baseline, timeout_period, grace_period_end)
    expect = 40.0
    assert expect == remaining

    # test 3
    # now - 30.0 == max(grace_period_end, idle_baseline) + timeout_period
    now = datetime(2020, 3, 1, 12, 30, second=50)
    idle_baseline = datetime(2020, 3, 1, 12, 30, second=0)
    timeout_period = timedelta(seconds=10)
    grace_period_end = datetime(2020, 3, 1, 12, 30, second=10)
    remaining = calculate_remaining_time(now, idle_baseline, timeout_period, grace_period_end)
    expect = -30.0
    assert expect == remaining


@pytest.mark.asyncio
async def new_user_grace_period_checker(
    etcd_fixture,
    database_fixture,
    create_app_and_client,
) -> None:
    test_app, _ = await create_app_and_client(
        [
            shared_config_ctx,
            redis_ctx,
            event_dispatcher_ctx,
            background_task_ctx,
            database_ctx,
            distributed_lock_ctx,
        ],
        [".etcd"],
    )
    root_ctx: RootContext = test_app["_root.context"]

    # test config
    grace_period = 30
    user_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    expected = datetime(2020, 3, 1, 12, 30, second=30)
    idle_value: Mapping[str, Any] = {
        "checkers": {
            "user_grace_period": {"user_initial_grace_period": str(grace_period)},
        },
        "enabled": "",
    }
    kernel = {"user_created_at": user_created_at}

    await root_ctx.shared_config.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    try:
        await checker_host.start()
        grace_period_end = await checker_host._grace_period_checker.get_grace_period_end(kernel)
    finally:
        await checker_host.shutdown()

    assert grace_period_end == expected


@pytest.mark.asyncio
async def network_timeout_idle_checker(
    etcd_fixture,
    database_fixture,
    create_app_and_client,
    mocker,
) -> None:
    test_app, _ = await create_app_and_client(
        [
            shared_config_ctx,
            redis_ctx,
            event_dispatcher_ctx,
            background_task_ctx,
            database_ctx,
            distributed_lock_ctx,
        ],
        [".etcd"],
    )
    root_ctx: RootContext = test_app["_root.context"]

    # test 1
    # remaining time is positive and no grace period
    session_id = SessionId(uuid4())
    threshold = 10
    last_access = datetime(2020, 3, 1, 12, 30, second=0).timestamp()
    now = datetime(2020, 3, 1, 12, 30, second=5).timestamp()
    mocker.patch("ai.backend.manager.idle.get_redis_now", return_value=now)
    expected = timedelta(seconds=5).total_seconds()
    idle_value = {
        "checkers": {
            "network_timeout": {
                "threshold": str(threshold),
            }
        },
        "enabled": "network_timeout,",
    }
    kernel = {
        "session_id": session_id,
        "session_type": SessionTypes.INTERACTIVE,
    }
    policy = {
        "idle_timeout": threshold,
    }

    await root_ctx.shared_config.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    try:
        await checker_host.start()
        network_idle_checker = get_checker_from_host(checker_host, NetworkTimeoutIdleChecker)

        await redis_helper.execute(
            checker_host._redis_live,
            lambda r: r.set(f"session.{session_id}.last_access", last_access),
        )

        should_alive = await network_idle_checker.check_idleness(
            kernel, checker_host._db, policy, checker_host._redis_live
        )
        remaining = await network_idle_checker.get_checker_result(
            checker_host._redis_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert should_alive
    assert remaining == expected

    # test 2
    # remaining time is negative and no grace period
    session_id = SessionId(uuid4())
    threshold = 10
    last_access = datetime(2020, 3, 1, 12, 30, second=0).timestamp()
    now = datetime(2020, 3, 1, 12, 30, second=30).timestamp()
    mocker.patch("ai.backend.manager.idle.get_redis_now", return_value=now)
    expected = -1
    idle_value = {
        "checkers": {
            "network_timeout": {
                "threshold": str(threshold),
            }
        },
        "enabled": "network_timeout,",
    }
    kernel = {
        "session_id": session_id,
        "session_type": SessionTypes.INTERACTIVE,
    }
    policy = {
        "idle_timeout": threshold,
    }

    await root_ctx.shared_config.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    try:
        await checker_host.start()
        network_idle_checker = get_checker_from_host(checker_host, NetworkTimeoutIdleChecker)

        await redis_helper.execute(
            checker_host._redis_live,
            lambda r: r.set(f"session.{session_id}.last_access", last_access),
        )

        should_alive = await network_idle_checker.check_idleness(
            kernel, checker_host._db, policy, checker_host._redis_live
        )
        remaining = await network_idle_checker.get_checker_result(
            checker_host._redis_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert not should_alive
    assert remaining == expected

    # test 3
    # remaining time is positive with new user grace period
    session_id = SessionId(uuid4())
    threshold = 10
    last_access = datetime(2020, 3, 1, 12, 30, second=0).timestamp()
    now = datetime(2020, 3, 1, 12, 30, second=5).timestamp()
    user_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    grace_period = 30
    mocker.patch("ai.backend.manager.idle.get_redis_now", return_value=now)
    expected = timedelta(seconds=35).total_seconds()
    idle_value = {
        "checkers": {
            "user_grace_period": {"user_initial_grace_period": str(grace_period)},
            "network_timeout": {
                "threshold": str(threshold),
            },
        },
        "enabled": "network_timeout,",
    }
    kernel = {
        "session_id": session_id,
        "session_type": SessionTypes.INTERACTIVE,
        "user_created_at": user_created_at,
    }
    policy = {
        "idle_timeout": threshold,
    }

    await root_ctx.shared_config.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    try:
        await checker_host.start()
        network_idle_checker = get_checker_from_host(checker_host, NetworkTimeoutIdleChecker)

        await redis_helper.execute(
            checker_host._redis_live,
            lambda r: r.set(f"session.{session_id}.last_access", last_access),
        )

        grace_period_end = await checker_host._grace_period_checker.get_grace_period_end(kernel)
        should_alive = await network_idle_checker.check_idleness(
            kernel,
            checker_host._db,
            policy,
            checker_host._redis_live,
            grace_period_end=grace_period_end,
        )
        remaining = await network_idle_checker.get_checker_result(
            checker_host._redis_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert should_alive
    assert remaining == expected

    # test 4
    # remaining time is negative with new user grace period
    session_id = SessionId(uuid4())
    threshold = 10
    last_access = datetime(2020, 3, 1, 12, 30, second=0).timestamp()
    now = datetime(2020, 3, 1, 12, 30, second=50).timestamp()
    user_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    grace_period = 30
    mocker.patch("ai.backend.manager.idle.get_redis_now", return_value=now)
    expected = -1
    idle_value = {
        "checkers": {
            "user_grace_period": {"user_initial_grace_period": str(grace_period)},
            "network_timeout": {
                "threshold": str(threshold),
            },
        },
        "enabled": "network_timeout,",
    }
    kernel = {
        "session_id": session_id,
        "session_type": SessionTypes.INTERACTIVE,
        "user_created_at": user_created_at,
    }
    policy = {
        "idle_timeout": threshold,
    }

    await root_ctx.shared_config.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    try:
        await checker_host.start()
        network_idle_checker = get_checker_from_host(checker_host, NetworkTimeoutIdleChecker)

        await redis_helper.execute(
            checker_host._redis_live,
            lambda r: r.set(f"session.{session_id}.last_access", last_access),
        )

        grace_period_end = await checker_host._grace_period_checker.get_grace_period_end(kernel)
        should_alive = await network_idle_checker.check_idleness(
            kernel,
            checker_host._db,
            policy,
            checker_host._redis_live,
            grace_period_end=grace_period_end,
        )
        remaining = await network_idle_checker.get_checker_result(
            checker_host._redis_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert not should_alive
    assert remaining == expected


@pytest.mark.asyncio
async def session_lifetime_checker(
    etcd_fixture,
    database_fixture,
    create_app_and_client,
    mocker,
) -> None:
    test_app, _ = await create_app_and_client(
        [
            shared_config_ctx,
            redis_ctx,
            event_dispatcher_ctx,
            background_task_ctx,
            database_ctx,
            distributed_lock_ctx,
        ],
        [".etcd"],
    )
    root_ctx: RootContext = test_app["_root.context"]

    # test 1
    # remaining time is positive and no grace period
    session_id = SessionId(uuid4())
    kernel_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    max_session_lifetime = 30
    now = datetime(2020, 3, 1, 12, 30, second=10)
    mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)
    expected = timedelta(seconds=20).total_seconds()
    idle_value = {
        "checkers": {},
        "enabled": "",
    }
    kernel = {
        "session_id": session_id,
        "created_at": kernel_created_at,
    }
    policy = {
        "max_session_lifetime": max_session_lifetime,
    }

    await root_ctx.shared_config.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    try:
        await checker_host.start()
        session_lifetime_checker = get_checker_from_host(checker_host, SessionLifetimeChecker)

        should_alive = await session_lifetime_checker.check_idleness(
            kernel,
            checker_host._db,
            policy,
            checker_host._redis_live,
        )
        remaining = await session_lifetime_checker.get_checker_result(
            checker_host._redis_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert should_alive
    assert remaining == expected

    # test 2
    # remaining time is negative and no grace period
    session_id = SessionId(uuid4())
    kernel_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    max_session_lifetime = 30
    now = datetime(2020, 3, 1, 12, 30, second=50)
    mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)
    expected = -1
    idle_value = {
        "checkers": {},
        "enabled": "",
    }
    kernel = {
        "session_id": session_id,
        "created_at": kernel_created_at,
    }
    policy = {
        "max_session_lifetime": max_session_lifetime,
    }

    await root_ctx.shared_config.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    try:
        await checker_host.start()
        session_lifetime_checker = get_checker_from_host(checker_host, SessionLifetimeChecker)

        should_alive = await session_lifetime_checker.check_idleness(
            kernel,
            checker_host._db,
            policy,
            checker_host._redis_live,
        )
        remaining = await session_lifetime_checker.get_checker_result(
            checker_host._redis_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert not should_alive
    assert remaining == expected

    # test 3
    # remaining time is positive with new user grace period
    session_id = SessionId(uuid4())
    kernel_created_at = datetime(2020, 3, 1, 12, 30, second=10)
    user_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    max_session_lifetime = 10
    now = datetime(2020, 3, 1, 12, 30, second=25)
    mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)
    grace_period = 30
    expected = timedelta(seconds=15).total_seconds()
    idle_value = {
        "checkers": {
            "user_grace_period": {"user_initial_grace_period": str(grace_period)},
        },
        "enabled": "",
    }
    kernel = {
        "session_id": session_id,
        "created_at": kernel_created_at,
        "user_created_at": user_created_at,
    }
    policy = {
        "max_session_lifetime": max_session_lifetime,
    }

    await root_ctx.shared_config.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    try:
        await checker_host.start()
        session_lifetime_checker = get_checker_from_host(checker_host, SessionLifetimeChecker)
        grace_period_end = await checker_host._grace_period_checker.get_grace_period_end(kernel)

        should_alive = await session_lifetime_checker.check_idleness(
            kernel,
            checker_host._db,
            policy,
            checker_host._redis_live,
            grace_period_end=grace_period_end,
        )
        remaining = await session_lifetime_checker.get_checker_result(
            checker_host._redis_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert should_alive
    assert remaining == expected

    # test 4
    # remaining time is negative with new user grace period
    session_id = SessionId(uuid4())
    kernel_created_at = datetime(2020, 3, 1, 12, 30, second=40)
    user_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    max_session_lifetime = 10
    now = datetime(2020, 3, 1, 12, 30, second=55)
    mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)
    grace_period = 30
    expected = -1
    idle_value = {
        "checkers": {
            "user_grace_period": {"user_initial_grace_period": str(grace_period)},
        },
        "enabled": "",
    }
    kernel = {
        "session_id": session_id,
        "created_at": kernel_created_at,
        "user_created_at": user_created_at,
    }
    policy = {
        "max_session_lifetime": max_session_lifetime,
    }

    await root_ctx.shared_config.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    try:
        await checker_host.start()
        session_lifetime_checker = get_checker_from_host(checker_host, SessionLifetimeChecker)
        grace_period_end = await checker_host._grace_period_checker.get_grace_period_end(kernel)

        should_alive = await session_lifetime_checker.check_idleness(
            kernel,
            checker_host._db,
            policy,
            checker_host._redis_live,
            grace_period_end=grace_period_end,
        )
        remaining = await session_lifetime_checker.get_checker_result(
            checker_host._redis_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert not should_alive
    assert remaining == expected


@pytest.mark.asyncio
async def utilization_idle_checker__utilization(
    etcd_fixture,
    database_fixture,
    create_app_and_client,
    mocker,
) -> None:
    test_app, _ = await create_app_and_client(
        [
            shared_config_ctx,
            redis_ctx,
            event_dispatcher_ctx,
            background_task_ctx,
            database_ctx,
            distributed_lock_ctx,
        ],
        [".etcd"],
    )
    root_ctx: RootContext = test_app["_root.context"]

    kernel_id = KernelId(uuid4())
    expected = {
        "cpu_util": 10.0,
        "mem": 50.0,
        "cuda_mem": 0.0,
        "cuda_util": 0.0,
    }
    occupied_slots = {
        "mem": 10.0,
    }
    live_stat = {
        "mem": {
            "current": "5.0",
            "pct": "10.0",
        },
        "cpu_util": {
            "pct": "10.0",
        },
    }

    resource_thresholds = {
        "cpu_util": {"average": "0"},
        "mem": {"average": "0"},
        "cuda_util": {"average": "0"},
        "cuda_mem": {"average": "0"},
    }
    idle_value = {
        "checkers": {
            "utilization": {
                "initial-grace-period": "0",
                "resource-thresholds": resource_thresholds,
                "thresholds-check-operator": "or",
                "time-window": "100",
            }
        },
        "enabled": "utilization",
    }

    await root_ctx.shared_config.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    await redis_helper.execute(
        checker_host._redis_stat,
        lambda r: r.set(str(kernel_id), msgpack.packb(live_stat)),
    )
    try:
        await checker_host.start()
        utilization_idle_checker = get_checker_from_host(checker_host, UtilizationIdleChecker)
        utilization_idle_checker = cast(UtilizationIdleChecker, utilization_idle_checker)

        utilization = await utilization_idle_checker.get_current_utilization(
            [kernel_id], occupied_slots
        )
    finally:
        await checker_host.shutdown()

    assert utilization == expected


@pytest.mark.asyncio
async def utilization_idle_checker(
    etcd_fixture,
    database_fixture,
    create_app_and_client,
    mocker,
) -> None:
    test_app, _ = await create_app_and_client(
        [
            shared_config_ctx,
            redis_ctx,
            event_dispatcher_ctx,
            background_task_ctx,
            database_ctx,
            distributed_lock_ctx,
        ],
        [".etcd"],
    )
    root_ctx: RootContext = test_app["_root.context"]

    # test 1
    # remaining time is positive and no utilization.
    # - No utilization during initial grace period
    session_id = SessionId(uuid4())
    kernel_id = KernelId(uuid4())
    timewindow = 30
    initial_grace_period = 100
    kernel_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    now = datetime(2020, 3, 1, 12, 30, second=10)
    expected = timedelta(seconds=120).total_seconds()

    mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)

    occupied_slots: Mapping[str, Decimal] = {
        "mem": Decimal(10.0),
    }
    live_stat = {
        "mem": {
            "current": "5.0",
            "pct": "10.0",
        },
        "cpu_util": {
            "pct": "10.0",
        },
    }
    kernel = {
        "id": kernel_id,
        "session_id": session_id,
        "created_at": kernel_created_at,
        "cluster_size": 1,
        "occupied_slots": occupied_slots,
    }
    policy = {
        "idle_timeout": timewindow,
    }

    resource_thresholds = {
        "cpu_util": {"average": "0"},
        "mem": {"average": "0"},
        "cuda_util": {"average": "0"},
        "cuda_mem": {"average": "0"},
    }
    idle_value = {
        "checkers": {
            "utilization": {
                "initial-grace-period": str(initial_grace_period),
                "resource-thresholds": resource_thresholds,
                "thresholds-check-operator": "or",
                "time-window": str(timewindow),
            }
        },
        "enabled": "utilization",
    }
    await root_ctx.shared_config.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    await redis_helper.execute(
        checker_host._redis_stat,
        lambda r: r.set(str(kernel_id), msgpack.packb(live_stat)),
    )
    try:
        await checker_host.start()
        utilization_idle_checker = get_checker_from_host(checker_host, UtilizationIdleChecker)

        should_alive = await utilization_idle_checker.check_idleness(
            kernel, checker_host._db, policy, checker_host._redis_live
        )
        remaining = await utilization_idle_checker.get_checker_result(
            checker_host._redis_live, session_id
        )
        util_info = await utilization_idle_checker.get_extra_info(session_id)
    finally:
        await checker_host.shutdown()

    assert should_alive
    assert remaining == expected
    assert util_info is None

    # test 2
    # remaining time is positive with utilization.
    session_id = SessionId(uuid4())
    kernel_id = KernelId(uuid4())
    kernel_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    now = datetime(2020, 3, 1, 12, 30, second=10)
    initial_grace_period = 0
    timewindow = 15
    expected = timedelta(seconds=5).total_seconds()

    mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)

    occupied_slots = {
        "mem": Decimal(10.0),
    }
    live_stat = {
        "mem": {
            "current": "5.0",
            "pct": "10.0",
        },
        "cpu_util": {
            "pct": "10.0",
        },
    }
    kernel = {
        "id": kernel_id,
        "session_id": session_id,
        "created_at": kernel_created_at,
        "cluster_size": 1,
        "occupied_slots": occupied_slots,
    }
    policy = {
        "idle_timeout": timewindow,
    }

    resource_thresholds = {
        "cpu_util": {"average": "0"},
        "mem": {"average": "0"},
        "cuda_util": {"average": "0"},
        "cuda_mem": {"average": "0"},
    }
    idle_value = {
        "checkers": {
            "utilization": {
                "initial-grace-period": str(initial_grace_period),
                "resource-thresholds": resource_thresholds,
                "thresholds-check-operator": "or",
                "time-window": str(timewindow),
            }
        },
        "enabled": "utilization",
    }
    await root_ctx.shared_config.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    await redis_helper.execute(
        checker_host._redis_stat,
        lambda r: r.set(str(kernel_id), msgpack.packb(live_stat)),
    )
    try:
        await checker_host.start()
        utilization_idle_checker = get_checker_from_host(checker_host, UtilizationIdleChecker)

        should_alive = await utilization_idle_checker.check_idleness(
            kernel, checker_host._db, policy, checker_host._redis_live
        )
        remaining = await utilization_idle_checker.get_checker_result(
            checker_host._redis_live, session_id
        )
        util_info = await utilization_idle_checker.get_extra_info(session_id)
    finally:
        await checker_host.shutdown()

    assert should_alive
    assert remaining == expected
    assert util_info is not None

    # test 3
    # remaining time is negative with utilization.
    session_id = SessionId(uuid4())
    kernel_id = KernelId(uuid4())
    timewindow = 15
    initial_grace_period = 0
    kernel_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    now = datetime(2020, 3, 1, 12, 30, second=50)
    expected = -1

    mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)

    occupied_slots = {
        "mem": Decimal(10.0),
    }
    live_stat = {
        "mem": {
            "current": "5.0",
            "pct": "10.0",
        },
        "cpu_util": {
            "pct": "10.0",
        },
    }
    kernel = {
        "id": kernel_id,
        "session_id": session_id,
        "created_at": kernel_created_at,
        "cluster_size": 1,
        "occupied_slots": occupied_slots,
    }
    policy = {
        "idle_timeout": timewindow,
    }

    resource_thresholds = {
        "cpu_util": {"average": "0"},
        "mem": {"average": "0"},
        "cuda_util": {"average": "0"},
        "cuda_mem": {"average": "0"},
    }
    idle_value = {
        "checkers": {
            "utilization": {
                "initial-grace-period": str(initial_grace_period),
                "resource-thresholds": resource_thresholds,
                "thresholds-check-operator": "or",
                "time-window": str(timewindow),
            }
        },
        "enabled": "utilization",
    }
    await root_ctx.shared_config.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    await redis_helper.execute(
        checker_host._redis_stat,
        lambda r: r.set(str(kernel_id), msgpack.packb(live_stat)),
    )
    try:
        await checker_host.start()
        utilization_idle_checker = get_checker_from_host(checker_host, UtilizationIdleChecker)

        should_alive = await utilization_idle_checker.check_idleness(
            kernel, checker_host._db, policy, checker_host._redis_live
        )
        remaining = await utilization_idle_checker.get_checker_result(
            checker_host._redis_live, session_id
        )
        util_info = await utilization_idle_checker.get_extra_info(session_id)
    finally:
        await checker_host.shutdown()

    assert should_alive
    assert remaining == expected
    assert util_info is not None
