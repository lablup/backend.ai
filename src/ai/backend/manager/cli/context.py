from __future__ import annotations

import atexit
import contextlib
import os
from typing import TYPE_CHECKING, AsyncIterator

import attrs
import click

from ai.backend.common import redis_helper
from ai.backend.common.config import redis_config_iv
from ai.backend.common.defs import REDIS_IMAGE_DB, REDIS_LIVE_DB, REDIS_STAT_DB, REDIS_STREAM_DB
from ai.backend.common.logging import AbstractLogger, Logger
from ai.backend.common.types import RedisConnectionInfo
from ai.backend.manager.config import SharedConfig

if TYPE_CHECKING:
    from ..config import LocalConfig


class CLIContext:
    local_config: LocalConfig

    _logger: AbstractLogger

    def __init__(self, local_config: LocalConfig) -> None:
        self.local_config = local_config

    def __enter__(self) -> None:
        # The "start-server" command is injected by ai.backend.cli from the entrypoint
        # and it has its own multi-process-aware logging initialization.
        # If we duplicate the local logging with it, the process termination may hang.
        click_ctx = click.get_current_context()
        if click_ctx.invoked_subcommand != "start-server":
            if (
                "drivers" in self.local_config["logging"]
                and "file" in self.local_config["logging"]["drivers"]
            ):
                self.local_config["logging"]["drivers"].remove("file")
            # log_endpoint = f'tcp://127.0.0.1:{find_free_port()}'
            ipc_base_path = self.local_config["manager"]["ipc-base-path"]
            log_sockpath = ipc_base_path / f"manager-cli-{os.getpid()}.sock"
            log_endpoint = f"ipc://{log_sockpath}"

            def _clean_logger():
                try:
                    os.unlink(log_sockpath)
                except FileNotFoundError:
                    pass

            atexit.register(_clean_logger)
            self._logger = Logger(
                self.local_config["logging"],
                is_master=True,
                log_endpoint=log_endpoint,
            )
            self._logger.__enter__()

    def __exit__(self, *exc_info) -> None:
        click_ctx = click.get_current_context()
        if click_ctx.invoked_subcommand != "start-server":
            self._logger.__exit__()


@attrs.define(auto_attribs=True, frozen=True, slots=True)
class RedisConnectionSet:
    live: RedisConnectionInfo
    stat: RedisConnectionInfo
    image: RedisConnectionInfo
    stream: RedisConnectionInfo


@contextlib.asynccontextmanager
async def redis_ctx(cli_ctx: CLIContext) -> AsyncIterator[RedisConnectionSet]:
    local_config = cli_ctx.local_config
    shared_config = SharedConfig(
        local_config["etcd"]["addr"],
        local_config["etcd"]["user"],
        local_config["etcd"]["password"],
        local_config["etcd"]["namespace"],
    )
    await shared_config.reload()
    raw_redis_config = await shared_config.etcd.get_prefix("config/redis")
    local_config["redis"] = redis_config_iv.check(raw_redis_config)
    redis_live = redis_helper.get_redis_object(shared_config.data["redis"], db=REDIS_LIVE_DB)
    redis_stat = redis_helper.get_redis_object(shared_config.data["redis"], db=REDIS_STAT_DB)
    redis_image = redis_helper.get_redis_object(
        shared_config.data["redis"],
        db=REDIS_IMAGE_DB,
    )
    redis_stream = redis_helper.get_redis_object(
        shared_config.data["redis"],
        db=REDIS_STREAM_DB,
    )
    yield RedisConnectionSet(
        live=redis_live,
        stat=redis_stat,
        image=redis_image,
        stream=redis_stream,
    )
    await redis_stream.close()
    await redis_image.close()
    await redis_stat.close()
    await redis_live.close()
