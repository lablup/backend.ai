import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Mapping

import msgpack
import sqlalchemy as sa
from dateutil.tz import tzutc
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline as RedisPipeline

from ai.backend.common import redis_helper
from ai.backend.common.types import (
    RedisConnectionInfo,
)
from ai.backend.common.utils import nmget
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.kernel import (
    RESOURCE_USAGE_KERNEL_STATUSES,
    kernels,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.user.actions.admin_month_stats import (
    AdminMonthStatsAction,
    AdminMonthStatsActionResult,
)
from ai.backend.manager.services.user.actions.user_month_stats import (
    UserMonthStatsAction,
    UserMonthStatsActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UserService:
    _db: ExtendedAsyncSAEngine
    _redis_stat: RedisConnectionInfo

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        redis_stat: RedisConnectionInfo,
    ) -> None:
        self._db = db
        self._redis_stat = redis_stat

    async def _get_time_binned_monthly_stats(self, user_uuid=None):
        """
        Generate time-binned (15 min) stats for the last one month (2880 points).
        The structure of the result would be:

            [
            # [
            #     timestamp, num_sessions,
            #     cpu_allocated, mem_allocated, gpu_allocated,
            #     io_read, io_write, scratch_used,
            # ]
                [1562083808.657106, 1, 1.2, 1073741824, ...],
                [1562084708.657106, 2, 4.0, 1073741824, ...],
            ]

        Note that the timestamp is in UNIX-timestamp.
        """
        # Get all or user kernels for the last month from DB.
        time_window = 900  # 15 min
        stat_length = 2880  # 15 * 4 * 24 * 30
        now = datetime.now(tzutc())
        start_date = now - timedelta(days=30)

        async with self._db.begin_readonly() as conn:
            query = (
                sa.select([
                    kernels.c.id,
                    kernels.c.created_at,
                    kernels.c.terminated_at,
                    kernels.c.occupied_slots,
                ])
                .select_from(kernels)
                .where(
                    (kernels.c.terminated_at >= start_date)
                    & (kernels.c.status.in_(RESOURCE_USAGE_KERNEL_STATUSES)),
                )
                .order_by(sa.asc(kernels.c.created_at))
            )
            if user_uuid is not None:
                query = query.where(kernels.c.user_uuid == user_uuid)
            result = await conn.execute(query)
            rows = result.fetchall()

        # Build time-series of time-binned stats.
        start_date_ts = start_date.timestamp()
        time_series_list: list[dict[str, Any]] = [
            {
                "date": start_date_ts + (idx * time_window),
                "num_sessions": {
                    "value": 0,
                    "unit_hint": "count",
                },
                "cpu_allocated": {
                    "value": 0,
                    "unit_hint": "count",
                },
                "mem_allocated": {
                    "value": 0,
                    "unit_hint": "bytes",
                },
                "gpu_allocated": {
                    "value": 0,
                    "unit_hint": "count",
                },
                "io_read_bytes": {
                    "value": 0,
                    "unit_hint": "bytes",
                },
                "io_write_bytes": {
                    "value": 0,
                    "unit_hint": "bytes",
                },
                "disk_used": {
                    "value": 0,
                    "unit_hint": "bytes",
                },
            }
            for idx in range(stat_length)
        ]

        async def _pipe_builder(r: Redis) -> RedisPipeline:
            pipe = r.pipeline()
            for row in rows:
                await pipe.get(str(row["id"]))
            return pipe

        raw_stats = await redis_helper.execute(self._redis_stat, _pipe_builder)

        for row, raw_stat in zip(rows, raw_stats):
            if raw_stat is not None:
                last_stat = msgpack.unpackb(raw_stat)
                io_read_byte = int(nmget(last_stat, "io_read.current", 0))
                io_write_byte = int(nmget(last_stat, "io_write.current", 0))
                disk_used = int(nmget(last_stat, "io_scratch_size.stats.max", 0, "/"))
            else:
                io_read_byte = 0
                io_write_byte = 0
                disk_used = 0

            occupied_slots: Mapping[str, Any] = row.occupied_slots
            kernel_created_at: float = row.created_at.timestamp()
            kernel_terminated_at: float = row.terminated_at.timestamp()
            cpu_value = int(occupied_slots.get("cpu", 0))
            mem_value = int(occupied_slots.get("mem", 0))
            cuda_device_value = int(occupied_slots.get("cuda.devices", 0))
            cuda_share_value = Decimal(occupied_slots.get("cuda.shares", 0))

            start_index = int((kernel_created_at - start_date_ts) // time_window)
            end_index = int((kernel_terminated_at - start_date_ts) // time_window) + 1
            if start_index < 0:
                start_index = 0
            for time_series in time_series_list[start_index:end_index]:
                time_series["num_sessions"]["value"] += 1
                time_series["cpu_allocated"]["value"] += cpu_value
                time_series["mem_allocated"]["value"] += mem_value
                time_series["gpu_allocated"]["value"] += cuda_device_value
                time_series["gpu_allocated"]["value"] += cuda_share_value
                time_series["io_read_bytes"]["value"] += io_read_byte
                time_series["io_write_bytes"]["value"] += io_write_byte
                time_series["disk_used"]["value"] += disk_used

        # Change Decimal type to float to serialize to JSON
        for time_series in time_series_list:
            time_series["gpu_allocated"]["value"] = float(time_series["gpu_allocated"]["value"])
        return time_series_list

    async def user_month_stats(self, action: UserMonthStatsAction) -> UserMonthStatsActionResult:
        stats = await self._get_time_binned_monthly_stats(user_uuid=action.user_id)
        return UserMonthStatsActionResult(stats=stats)

    # TODO: user (전체)
    async def admin_month_stats(self, action: AdminMonthStatsAction) -> AdminMonthStatsActionResult:
        stats = await self._get_time_binned_monthly_stats(user_uuid=None)
        return AdminMonthStatsActionResult(stats=stats)
