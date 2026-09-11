"""Valkey clients for one test: the real server the container pool runs.

The manager decides which role and which database each client talks to; this asks the
config the same way, so a scenario reaches the keys the product reaches.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.defs import REDIS_LIVE_DB, REDIS_STATISTICS_DB, RedisRole
from ai.backend.manager.config.provider import ManagerConfigProvider


@dataclass(frozen=True)
class ScenarioValkey:
    """The clients an adapter under test is handed."""

    stat: ValkeyStatClient
    schedule: ValkeyScheduleClient

    @classmethod
    async def create(cls, config: ManagerConfigProvider) -> Self:
        target = config.config.redis.to_valkey_profile_target()
        return cls(
            stat=await ValkeyStatClient.create(
                target.profile_target(RedisRole.STATISTICS),
                db_id=REDIS_STATISTICS_DB,
                human_readable_name="scenario-stat",
            ),
            schedule=await ValkeyScheduleClient.create(
                target.profile_target(RedisRole.STREAM),
                db_id=REDIS_LIVE_DB,
                human_readable_name="scenario-schedule",
            ),
        )

    async def close(self) -> None:
        await self.stat.close()
        await self.schedule.close()
