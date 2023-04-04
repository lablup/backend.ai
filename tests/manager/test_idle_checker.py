from datetime import datetime, timedelta
from typing import Any, Mapping

import pytest

# from ai.backend.common import redis_helper
# from ai.backend.common.types import SessionTypes
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.idle import (  # IdleCheckerHost,; NetworkTimeoutIdleChecker,; NewUserGracePeriodChecker,; SessionLifetimeChecker,; UtilizationIdleChecker,
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


def test_remaining_time_calculation() -> None:
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
async def test_new_user_grace_period_checker(
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

    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.shared_config,
        root_ctx.event_dispatcher,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    try:
        await checker_host._shared_config.etcd.put_prefix("config/idle", idle_value)
        await checker_host.start()
        grace_period_end = await checker_host._grace_period_checker.get_grace_period_end(kernel)
    finally:
        await checker_host.shutdown()

    assert grace_period_end == expected


# @pytest.mark.asyncio
# async def test_network_timeout_idle_checker(
#     etcd_fixture,
#     database_fixture,
#     create_app_and_client,
#     mocker,
# ) -> None:
#     test_app, _ = await create_app_and_client(
#         [
#             shared_config_ctx,
#             redis_ctx,
#             event_dispatcher_ctx,
#             background_task_ctx,
#             database_ctx,
#             distributed_lock_ctx,
#         ],
#         [".etcd"],
#     )
#     root_ctx: RootContext = test_app["_root.context"]

#     # test config
#     session_id = "network-check-session"
#     threshold = 10
#     last_access = datetime(2020, 3, 1, 12, 30, second=0).timestamp()
#     now = datetime(2020, 3, 1, 12, 30, second=5).timestamp()
#     mocker.patch("ai.backend.manager.idle.get_redis_now", return_value=now)
#     # expected = datetime(2020, 3, 1, 12, 30, second=30)
#     idle_value = {
#         "checkers": {
#             "network_timeout": {
#                 "threshold": str(threshold),
#             }
#         },
#         "enabled": "network_timeout",
#     }
#     kernel = {
#         "session_id": session_id,
#         "session_type": SessionTypes.INTERACTIVE,
#     }
#     policy = {
#         "idle_timeout": 0,
#     }

#     checker_host = await init_idle_checkers(
#         root_ctx.db,
#         root_ctx.shared_config,
#         root_ctx.event_dispatcher,
#         root_ctx.event_producer,
#         root_ctx.distributed_lock_factory,
#     )
#     try:
#         await checker_host._shared_config.etcd.put_prefix("config/idle", idle_value)
#         await checker_host.start()
#         for checker in checker_host._checkers:
#             if isinstance(checker, NetworkTimeoutIdleChecker):
#                 network_idle_checker = checker
#                 break
#         else:
#             raise ValueError(f"NetworkTimeoutIdleChecker not found in the checker_host {checker_host._checkers = }")

#         await redis_helper.execute(
#             checker_host._redis_live,
#             lambda r: r.set(f"session.{session_id}.last_access", last_access),
#         )

#         result = await network_idle_checker.check_idleness(
#             kernel, checker_host._db, policy, checker_host._redis_live
#         )
#         remaining = await network_idle_checker.get_checker_result(
#             checker_host._redis_live, session_id
#         )
#     finally:
#         await checker_host.shutdown()

#     assert result == True
