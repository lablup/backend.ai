from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path
from pprint import pformat
from typing import AsyncIterator, Self

import attrs
import click

from ai.backend.common import redis_helper
from ai.backend.common.config import redis_config_iv
from ai.backend.common.defs import (
    REDIS_IMAGE_DB,
    REDIS_LIVE_DB,
    REDIS_STATISTICS_DB,
    REDIS_STREAM_DB,
    RedisRole,
)
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.exception import ConfigurationError
from ai.backend.common.types import RedisConnectionInfo
from ai.backend.logging import AbstractLogger, LocalLogger, LogLevel

from ..config import LocalConfig, SharedConfig
from ..config import load as load_config


class CLIContext:
    _local_config: LocalConfig | None
    _logger: AbstractLogger

    def __init__(self, config_path: Path, log_level: LogLevel) -> None:
        self.config_path = config_path
        self.log_level = log_level
        self._local_config = None

    @property
    def local_config(self) -> LocalConfig:
        # Lazy-load the configuration only when requested.
        try:
            if self._local_config is None:
                self._local_config = load_config(self.config_path, self.log_level)
        except ConfigurationError as e:
            print(
                "ConfigurationError: Could not read or validate the manager local config:",
                file=sys.stderr,
            )
            print(pformat(e.invalid_data), file=sys.stderr)
            raise click.Abort()
        return self._local_config

    def __enter__(self) -> Self:
        # The "start-server" command is injected by ai.backend.cli from the entrypoint
        # and it has its own multi-process-aware logging initialization.
        # If we duplicate the local logging with it, the process termination may hang.
        click_ctx = click.get_current_context()
        if click_ctx.invoked_subcommand != "start-server":
            logging_config = {
                "level": self.log_level,
                "pkg-ns": {
                    "": LogLevel.WARNING,
                    "ai.backend": self.log_level,
                },
            }
            try:
                # Try getting the logging config but silently fallback to the default if not
                # present (e.g., when `mgr gql show` command used in CI without installation as
                # addressed in #1686).
                with open(os.devnull, "w") as sink, contextlib.redirect_stderr(sink):
                    logging_config = self.local_config["logging"]
            except click.Abort:
                pass
            self._logger = LocalLogger(logging_config)
            self._logger.__enter__()
        return self

    def __exit__(self, *exc_info) -> None:
        click_ctx = click.get_current_context()
        if click_ctx.invoked_subcommand != "start-server":
            self._logger.__exit__()


@contextlib.asynccontextmanager
async def etcd_ctx(cli_ctx: CLIContext) -> AsyncIterator[AsyncEtcd]:
    local_config = cli_ctx.local_config
    creds = None
    if local_config["etcd"]["user"]:
        creds = {
            "user": local_config["etcd"]["user"],
            "password": local_config["etcd"]["password"],
        }
    scope_prefix_map = {
        ConfigScopes.GLOBAL: "",
        # TODO: provide a way to specify other scope prefixes
    }
    etcd = AsyncEtcd(
        local_config["etcd"]["addr"],
        local_config["etcd"]["namespace"],
        scope_prefix_map,
        credentials=creds,
    )
    try:
        yield etcd
    finally:
        await etcd.close()


@contextlib.asynccontextmanager
async def config_ctx(cli_ctx: CLIContext) -> AsyncIterator[SharedConfig]:
    local_config = cli_ctx.local_config
    # scope_prefix_map is created inside ConfigServer
    shared_config = SharedConfig(
        local_config["etcd"]["addr"],
        local_config["etcd"]["user"],
        local_config["etcd"]["password"],
        local_config["etcd"]["namespace"],
    )
    await shared_config.reload()
    raw_redis_config = await shared_config.etcd.get_prefix("config/redis")
    local_config["redis"] = redis_config_iv.check(raw_redis_config)
    try:
        yield shared_config
    finally:
        await shared_config.close()


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
    redis_live = redis_helper.get_redis_object(
        local_config["redis"].get_override_config(RedisRole.LIVE),
        name="mgr_cli.live",
        db=REDIS_LIVE_DB,
    )
    redis_stat = redis_helper.get_redis_object(
        local_config["redis"].get_override_config(RedisRole.STATISTICS),
        name="mgr_cli.stat",
        db=REDIS_STATISTICS_DB,
    )
    redis_image = redis_helper.get_redis_object(
        local_config["redis"].get_override_config(RedisRole.IMAGE),
        name="mgr_cli.image",
        db=REDIS_IMAGE_DB,
    )
    redis_stream = redis_helper.get_redis_object(
        local_config["redis"].get_override_config(RedisRole.STREAM),
        name="mgr_cli.stream",
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
