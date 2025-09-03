from __future__ import annotations

import asyncio
import csv
import json
import logging
import sys
from typing import TYPE_CHECKING, Literal

import click
import redis
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from tabulate import tabulate

from ai.backend.common import redis_helper
from ai.backend.common.types import RedisConnectionInfo
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.cli.context import redis_ctx

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@click.group()
def cli() -> None:
    pass


async def _ping(redis_conn: RedisConnectionInfo) -> None:
    try:
        await redis_helper.execute(redis_conn, lambda r: r.execute_command("PING"))
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
        log.exception("ping(): Redis ping failed")


@cli.command()
@click.option("--manager-id", help="ID of manager to check status.")
@click.option(
    "-f",
    "--format",
    type=click.Choice(["plain", "csv", "json"]),
    help="Output format type.",
    default="plain",
)
@click.argument("scheduler_name", required=False)
@click.pass_obj
def last_execution_time(
    cli_ctx: CLIContext,
    scheduler_name: str | None,
    *,
    format: Literal["plain"] | Literal["csv"] | Literal["json"] = "plain",
    manager_id: str | None = None,
) -> None:
    """Queries manager's scheduler execution footprint from Redis. When scheduler name is not specified, this command will return informations of all schedulers in store."""

    async def _impl():
        bootstrap_config = await cli_ctx.get_bootstrap_config()
        _manager_id = manager_id or bootstrap_config.manager.id
        async with redis_ctx(cli_ctx) as redis_conn_set:
            if not scheduler_name:
                keys = []

                async def _scan_keys(r: Redis) -> list[bytes]:
                    result = []
                    async for key in r.scan_iter(match=f"manager.{_manager_id}.*"):
                        result.append(key)
                    return result

                keys = await redis_helper.execute(redis_conn_set.live, _scan_keys)
                if len(keys) == 0:
                    log.warn(
                        "Failed to fetch scheduler information manager {}. Please check if you have mentioned manager ID correctly and the specified manager is up and running.",
                        manager_id,
                    )
                    return

                def _pipeline(r: Redis) -> Pipeline:
                    pipe = r.pipeline(transaction=True)
                    for k in keys:
                        pipe.hgetall(k)
                    return pipe

                schedulers = [key.decode().split(".")[-1] for key in keys]
                encoded_results = await redis_helper.execute(redis_conn_set.live, _pipeline)
            else:
                redis_key = f"manager.{_manager_id}.{scheduler_name}"
                exists = await redis_helper.execute(
                    redis_conn_set.live, lambda r: r.exists(redis_key)
                )
                if exists == 0:
                    log.warn(
                        "Failed to fetch scheduler information of {} on manager {}. Please check if you have mentioned both manager ID and scheduler name correctly.",
                        scheduler_name,
                        manager_id,
                    )
                    return
                schedulers = [scheduler_name]
                encoded_results = [
                    await redis_helper.execute(redis_conn_set.live, lambda r: r.hgetall(redis_key))
                ]
            results = [
                {k.decode(): v.decode() for k, v in resp.items()} for resp in encoded_results
            ]
            match format:
                case "plain":
                    for scheduler, resp in zip(schedulers, results):
                        print(
                            tabulate([("scheduler", scheduler)] + [(k, v) for k, v in resp.items()])
                        )
                case "csv":
                    writer = csv.DictWriter(
                        sys.stdout,
                        fieldnames=[
                            "scheduler",
                            "trigger_event",
                            "execution_time",
                            "finish_time",
                            "extras",
                        ],
                    )
                    for scheduler, resp in zip(schedulers, results):
                        row = {
                            "scheduler": scheduler,
                            "trigger_event": resp["trigger_event"],
                            "execution_time": resp["execution_time"],
                            "finish_time": resp["finish_time"],
                        }
                        extras = [f"{k}={v}" for k, v in resp.items() if k not in row]
                        row["extras"] = ";".join(extras)
                        writer.writerow(row)
                case "json":
                    print(
                        json.dumps(
                            [
                                {"scheduler": scheduler, **resp}
                                for scheduler, resp in zip(schedulers, results)
                            ],
                            ensure_ascii=False,
                            indent=2,
                        )
                    )

    asyncio.run(_impl())
