from __future__ import annotations

import contextlib
import sys
from pathlib import Path
from pprint import pformat
from typing import AsyncIterator, Optional, Self

import attrs
import click

from ai.backend.common import redis_helper
from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.config import find_config_file
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
from ai.backend.manager.config.bootstrap import BootstrapConfig
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.config.unified import ManagerUnifiedConfig, RedisConfig


class CLIContext:
    _bootstrap_config: Optional[BootstrapConfig]
    _logger: AbstractLogger

    def __init__(self, log_level: LogLevel, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path
        self.log_level = log_level
        self._bootstrap_config = None

    async def get_bootstrap_config(self) -> BootstrapConfig:
        # Lazy-load the configuration only when requested.
        try:
            if self._bootstrap_config is None:
                if self.config_path is None:
                    self.config_path = find_config_file("manager")

                self._bootstrap_config = await BootstrapConfig.load_from_file(
                    self.config_path, self.log_level
                )
        except ConfigurationError as e:
            print(
                "ConfigurationError: Could not read or validate the manager local config:",
                file=sys.stderr,
            )
            print(pformat(e.invalid_data), file=sys.stderr)
            raise click.Abort()
        return self._bootstrap_config

    def __enter__(self) -> Self:
        # The "start-server" command is injected by ai.backend.cli from the entrypoint
        # and it has its own multi-process-aware logging initialization.
        # If we duplicate the local logging with it, the process termination may hang.
        click_ctx = click.get_current_context()
        if click_ctx.invoked_subcommand != "start-server":
            self._logger = LocalLogger(log_level=self.log_level)
            self._logger.__enter__()
        return self

    def __exit__(self, *exc_info) -> None:
        click_ctx = click.get_current_context()
        if click_ctx.invoked_subcommand != "start-server":
            self._logger.__exit__()


@contextlib.asynccontextmanager
async def etcd_ctx(cli_ctx: CLIContext) -> AsyncIterator[AsyncEtcd]:
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    etcd_config_data = bootstrap_config.etcd.to_dataclass()
    creds = None
    if etcd_config_data.user:
        if not etcd_config_data.password:
            raise ConfigurationError({
                "etcd": "password is required when user is set",
            })

        creds = {
            "user": etcd_config_data.user,
            "password": etcd_config_data.password,
        }
    scope_prefix_map = {
        ConfigScopes.GLOBAL: "",
        # TODO: provide a way to specify other scope prefixes
    }
    etcd = AsyncEtcd(
        [addr.to_legacy() for addr in etcd_config_data.addrs],
        etcd_config_data.namespace,
        scope_prefix_map,
        credentials=creds,
    )
    try:
        yield etcd
    finally:
        await etcd.close()


@contextlib.asynccontextmanager
async def config_ctx(cli_ctx: CLIContext) -> AsyncIterator[ManagerUnifiedConfig]:
    # scope_prefix_map is created inside ConfigServer

    bootstrap_config = await cli_ctx.get_bootstrap_config()
    etcd_config_data = bootstrap_config.etcd.to_dataclass()
    etcd = AsyncEtcd.initialize(etcd_config_data)
    etcd_loader = LegacyEtcdLoader(etcd)
    redis_config = await etcd_loader.load()
    unified_config = ManagerUnifiedConfig(**redis_config)

    try:
        yield unified_config
    finally:
        await etcd_loader.close()


@attrs.define(auto_attribs=True, frozen=True, slots=True)
class RedisConnectionSet:
    live: RedisConnectionInfo
    stat: ValkeyStatClient
    image: ValkeyImageClient
    stream: RedisConnectionInfo


@contextlib.asynccontextmanager
async def redis_ctx(cli_ctx: CLIContext) -> AsyncIterator[RedisConnectionSet]:
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    etcd_config_data = bootstrap_config.etcd.to_dataclass()
    etcd = AsyncEtcd.initialize(etcd_config_data)
    loader = LegacyEtcdLoader(etcd, config_prefix="config/redis")
    raw_redis_config = await loader.load()
    redis_config = RedisConfig(**raw_redis_config)
    redis_profile_target = redis_config.to_redis_profile_target()

    redis_live = redis_helper.get_redis_object(
        redis_profile_target.profile_target(RedisRole.LIVE),
        name="mgr_cli.live",
        db=REDIS_LIVE_DB,
    )
    valkey_stat_client = await ValkeyStatClient.create(
        redis_profile_target.profile_target(RedisRole.STATISTICS).to_valkey_target(),
        db_id=REDIS_STATISTICS_DB,
        human_readable_name="mgr_cli.stat",
    )
    redis_image = await ValkeyImageClient.create(
        redis_profile_target.profile_target(RedisRole.IMAGE).to_valkey_target(),
        db_id=REDIS_IMAGE_DB,
        human_readable_name="mgr_cli.image",
    )
    redis_stream = redis_helper.get_redis_object(
        redis_profile_target.profile_target(RedisRole.STREAM),
        name="mgr_cli.stream",
        db=REDIS_STREAM_DB,
    )
    yield RedisConnectionSet(
        live=redis_live,
        stat=valkey_stat_client,
        image=redis_image,
        stream=redis_stream,
    )
    await redis_stream.close()
    await redis_image.close()
    await valkey_stat_client.close()
    await redis_live.close()
