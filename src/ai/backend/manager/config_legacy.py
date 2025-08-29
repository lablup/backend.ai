from __future__ import annotations

import logging
import os
import secrets
import socket
import sys
from abc import abstractmethod
from collections import UserDict
from collections.abc import Mapping
from pathlib import Path
from pprint import pformat
from typing import (
    Any,
    Awaitable,
    Callable,
    Final,
    List,
    Optional,
    Sequence,
    TypeAlias,
)

import click
import trafaret as t

from ai.backend.common import config
from ai.backend.common import validators as tx
from ai.backend.common.defs import DEFAULT_FILE_IO_TIMEOUT
from ai.backend.common.lock import EtcdLock, FileLock, RedisLock
from ai.backend.logging import BraceStyleAdapter, LogLevel
from ai.backend.manager.data.session.types import SessionStatus

from .defs import DEFAULT_METRIC_RANGE_VECTOR_TIMEWINDOW
from .pglock import PgAdvisoryLock

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_max_cpu_count = os.cpu_count()
_file_perm = (Path(__file__).parent / "server.py").stat()

DEFAULT_CHUNK_SIZE: Final = 256 * 1024  # 256 KiB
DEFAULT_INFLIGHT_CHUNKS: Final = 8

NestedStrKeyedDict: TypeAlias = "dict[str, Any | NestedStrKeyedDict]"

_default_pyroscope_config: dict[str, Any] = {
    "enabled": False,
    "app-name": None,
    "server-addr": None,
    "sample-rate": None,
}

_default_global_lock_lifetime: dict[str, float | int] = {
    "schedule": 30,
    "check_precondition": 30,
    "start": 30,
}

_default_reporter: dict[str, Any] = {
    "smtp": [],
    "audit-log": [],
    "action-monitors": [],
}

_default_smtp_template = """
Action type: {{ action_type }}
Entity ID: {{ entity_id }}
Status: {{ status }}
Description: {{ description }}
Started at: {{ created_at }}
Finished at: {{ ended_at }}
Duration: {{ duration }} seconds

This email is sent from Backend.AI SMTP Reporter.
"""

manager_local_config_iv = (
    t.Dict({
        t.Key("db"): t.Dict({
            t.Key("type", default="postgresql"): t.Enum("postgresql"),
            t.Key("addr"): tx.HostPortPair,
            t.Key("name"): tx.Slug[2:64],
            t.Key("user"): t.String,
            t.Key("password"): t.String,
            t.Key("pool-size", default=8): t.ToInt[1:],  # type: ignore
            t.Key("pool-recycle", default=-1): t.ToFloat[-1:],  # -1 is infinite
            t.Key("pool-pre-ping", default=False): t.ToBool,
            t.Key("max-overflow", default=64): t.ToInt[-1:],  # -1 is infinite  # type: ignore
            t.Key("lock-conn-timeout", default=0): t.ToFloat[0:],  # 0 is infinite
        }),
        t.Key("manager"): t.Dict({
            t.Key("ipc-base-path", default="/tmp/backend.ai/ipc"): tx.Path(
                type="dir", auto_create=True
            ),
            t.Key("num-proc", default=_max_cpu_count): t.Int[1:_max_cpu_count],
            t.Key("id", default=f"i-{socket.gethostname()}"): t.String,
            t.Key("user", default=None): tx.UserID(default_uid=_file_perm.st_uid),
            t.Key("user", default=None): tx.UserID(default_uid=_file_perm.st_uid),
            t.Key("group", default=None): tx.GroupID(default_gid=_file_perm.st_gid),
            t.Key("service-addr", default=("0.0.0.0", 8080)): tx.HostPortPair,
            t.Key("internal-addr", default=("0.0.0.0", 18080)): tx.HostPortPair,
            t.Key(
                "rpc-auth-manager-keypair", default="fixtures/manager/manager.key_secret"
            ): tx.Path(type="file"),
            t.Key("heartbeat-timeout", default=40.0): t.Float[1.0:],  # type: ignore
            t.Key("secret", default=None): t.Null | t.String,
            t.Key("ssl-enabled", default=False): t.ToBool,
            t.Key("ssl-cert", default=None): t.Null | tx.Path(type="file"),
            t.Key("ssl-privkey", default=None): t.Null | tx.Path(type="file"),
            t.Key("event-loop", default="asyncio"): t.Enum("asyncio", "uvloop"),
            t.Key("distributed-lock", default="pg_advisory"): t.Enum(
                "filelock", "pg_advisory", "redlock", "etcd"
            ),
            t.Key(
                "pg-advisory-config", default=PgAdvisoryLock.default_config
            ): PgAdvisoryLock.config_iv,
            t.Key("filelock-config", default=FileLock.default_config): FileLock.config_iv,
            t.Key("redlock-config", default=RedisLock.default_config): RedisLock.config_iv,
            t.Key("etcdlock-config", default=EtcdLock.default_config): EtcdLock.config_iv,
            t.Key(
                "session_schedule_lock_lifetime", default=_default_global_lock_lifetime["schedule"]
            ): t.ToFloat(),
            t.Key(
                "session_check_precondition_lock_lifetime",
                default=_default_global_lock_lifetime["check_precondition"],
            ): t.ToFloat(),
            t.Key(
                "session_start_lock_lifetime", default=_default_global_lock_lifetime["start"]
            ): t.ToFloat(),
            t.Key("pid-file", default=os.devnull): tx.Path(
                type="file",
                allow_nonexisting=True,
                allow_devnull=True,
            ),
            t.Key("allowed-plugins", default=None): t.Null | tx.ToSet,
            t.Key("disabled-plugins", default=None): t.Null | tx.ToSet,
            t.Key("hide-agents", default=False): t.Bool,
            t.Key(
                "agent-selection-resource-priority",
                default=["cuda", "rocm", "tpu", "cpu", "mem"],
            ): t.List(t.String),
            t.Key("importer-image", default="lablup/importer:manylinux2010"): t.String,
            t.Key("max-wsmsg-size", default=16 * (2**20)): t.ToInt,  # default: 16 MiB
            tx.AliasedKey(["aiomonitor-termui-port", "aiomonitor-port"], default=38100): t.ToInt[
                1:65535
            ],
            t.Key("aiomonitor-webui-port", default=39100): t.ToInt[1:65535],
            t.Key("use-experimental-redis-event-dispatcher", default=False): t.ToBool,
            t.Key("status-update-interval", default=None): t.Null | t.ToFloat[0:],  # second
            t.Key("status-lifetime", default=None): t.Null | t.ToInt[0:],  # second
            t.Key("public-metrics-port", default=None): t.Null | t.ToInt[1:65535],
        }).allow_extra("*"),
        t.Key("docker-registry"): t.Dict({  # deprecated in v20.09
            t.Key("ssl-verify", default=True): t.ToBool,
        }).allow_extra("*"),
        t.Key("logging"): t.Any,  # checked in ai.backend.logging
        t.Key("pyroscope", default=_default_pyroscope_config): t.Dict({
            t.Key("enabled", default=_default_pyroscope_config["enabled"]): t.ToBool,
            t.Key("app-name", default=_default_pyroscope_config["app-name"]): t.Null | t.String,
            t.Key("server-addr", default=_default_pyroscope_config["server-addr"]): t.Null
            | t.String,
            t.Key("sample-rate", default=_default_pyroscope_config["sample-rate"]): t.Null
            | t.ToInt[1:],
        }).allow_extra("*"),
        t.Key("reporter", default=_default_reporter): t.Dict({
            t.Key("smtp", default=[]): t.List(
                t.Dict({
                    t.Key("name"): t.String,
                    t.Key("host"): t.String,
                    t.Key("port"): t.Int[1:65535],
                    t.Key("username"): t.String,
                    t.Key("password"): t.String,
                    t.Key("sender"): t.String,
                    t.Key("recipients"): t.List(t.String),
                    t.Key("use-tls"): t.ToBool,
                    t.Key("max-workers", default=5): t.Int,
                    t.Key("template", default=_default_smtp_template): t.String,
                    t.Key("trigger-policy"): t.Enum("ALL", "ON_ERROR"),
                })
            ),
            t.Key("audit-log", default=[]): t.List(
                t.Dict({
                    t.Key("name"): t.String,
                }).allow_extra("*")
            ),
            t.Key("action-monitors", default=[]): t.List(
                t.Dict({
                    t.Key("subscribed-actions"): t.List(t.String),
                    t.Key("reporter"): t.String,
                }).allow_extra("*")
            ),
        }).allow_extra("*"),
        t.Key("debug"): t.Dict({
            t.Key("enabled", default=False): t.ToBool,
            t.Key("asyncio", default=False): t.Bool,
            t.Key("enhanced-aiomonitor-task-info", default=False): t.Bool,
            t.Key("log-events", default=False): t.ToBool,
            t.Key("log-scheduler-ticks", default=False): t.ToBool,
            t.Key("periodic-sync-stats", default=False): t.ToBool,
        }).allow_extra("*"),
    })
    .merge(config.etcd_config_iv)
    .allow_extra("*")
)

_config_defaults: Mapping[str, Any] = {
    "system": {
        "timezone": "UTC",
    },
    "api": {
        "allow-origins": "*",
        "allow-openapi-schema-introspection": False,
        "allow-graphql-schema-introspection": False,
        "max-gql-query-depth": None,
        "max-gql-connection-page-size": None,
    },
    "redis": config.redis_default_config,
    "docker": {
        "registry": {},
        "image": {
            "auto_pull": "digest",
        },
    },
    "network": {
        "inter-container": {
            "default-driver": "overlay",
        },
        "subnet": {
            "agent": "0.0.0.0/0",
            "container": "0.0.0.0/0",
        },
    },
    "plugins": {
        "accelerator": {},
        "network": {},
        "scheduler": {},
        "agent-selector": {},
    },
    "watcher": {
        "token": None,
        "file-io-timeout": DEFAULT_FILE_IO_TIMEOUT,
    },
    "session": {
        "hang-tolerance": {
            "threshold": {},
        },
    },
    "metric": {
        "address": {
            "host": "127.0.0.1",
            "port": 9090,
        },
        "timewindow": DEFAULT_METRIC_RANGE_VECTOR_TIMEWINDOW,
    },
}


session_hang_tolerance_iv = t.Dict(
    {
        t.Key(
            "threshold", default=_config_defaults["session"]["hang-tolerance"]["threshold"]
        ): t.Dict({
            t.Key(SessionStatus.PREPARING.name, optional=True): tx.TimeDuration(),
            t.Key(SessionStatus.TERMINATING.name, optional=True): tx.TimeDuration(),
        }).ignore_extra("*"),
    },
)


shared_config_iv = t.Dict({
    t.Key("system", default=_config_defaults["system"]): t.Dict({
        t.Key("timezone", default=_config_defaults["system"]["timezone"]): tx.TimeZone,
    }).allow_extra("*"),
    t.Key("api", default=_config_defaults["api"]): t.Dict({
        t.Key("allow-origins", default=_config_defaults["api"]["allow-origins"]): t.String,
        t.Key(
            "allow-graphql-schema-introspection",
            default=_config_defaults["api"]["allow-graphql-schema-introspection"],
        ): t.ToBool,
        t.Key(
            "allow-openapi-schema-introspection",
            default=_config_defaults["api"]["allow-openapi-schema-introspection"],
        ): t.ToBool,
        t.Key("max-gql-query-depth", default=_config_defaults["api"]["max-gql-query-depth"]): t.Null
        | t.ToInt[1:],
        t.Key(
            "max-gql-connection-page-size",
            default=_config_defaults["api"]["max-gql-connection-page-size"],
        ): t.Null | t.ToInt[1:],
    }).allow_extra("*"),
    t.Key("redis", default=_config_defaults["redis"]): config.redis_config_iv,
    t.Key("docker", default=_config_defaults["docker"]): t.Dict({
        t.Key("image", default=_config_defaults["docker"]["image"]): t.Dict({
            t.Key("auto_pull", default=_config_defaults["docker"]["image"]["auto_pull"]): t.Enum(
                "digest", "tag", "none"
            ),
        }).allow_extra("*"),
    }).allow_extra("*"),
    t.Key("plugins", default=_config_defaults["plugins"]): t.Dict({
        t.Key("accelerator", default=_config_defaults["plugins"]["accelerator"]): t.Mapping(
            t.String, t.Mapping(t.String, t.Any)
        ),
        t.Key("scheduler", default=_config_defaults["plugins"]["scheduler"]): t.Mapping(
            t.String, t.Mapping(t.String, t.Any)
        ),
        t.Key("agent-selector", default=_config_defaults["plugins"]["agent-selector"]): t.Mapping(
            t.String, config.agent_selector_globalconfig_iv
        ),
    }).allow_extra("*"),
    t.Key("network", default=_config_defaults["network"]): t.Dict({
        t.Key("inter-container", default=_config_defaults["network"]["inter-container"]): t.Dict({
            t.Key(
                "default-driver",
                default=_config_defaults["network"]["inter-container"]["default-driver"],
            ): t.Null | t.String,
        }).allow_extra("*"),
        t.Key("subnet", default=_config_defaults["network"]["subnet"]): t.Dict({
            t.Key("agent", default=_config_defaults["network"]["subnet"]["agent"]): tx.IPNetwork,
            t.Key(
                "container", default=_config_defaults["network"]["subnet"]["container"]
            ): tx.IPNetwork,
        }).allow_extra("*"),
    }).allow_extra("*"),
    t.Key("watcher", default=_config_defaults["watcher"]): t.Dict({
        t.Key("token", default=_config_defaults["watcher"]["token"]): t.Null | t.String,
        t.Key(
            "file-io-timeout", default=_config_defaults["watcher"]["file-io-timeout"]
        ): t.ToFloat(),
    }).allow_extra("*"),
    t.Key("auth", default=None): (
        t.Dict({
            t.Key("max_password_age", default=None): t.Null | tx.TimeDuration(),
        }).allow_extra("*")
        | t.Null
    ),
    t.Key("session", default=_config_defaults["session"]): t.Dict(
        {
            t.Key(
                "hang-tolerance", default=_config_defaults["session"]["hang-tolerance"]
            ): session_hang_tolerance_iv,
        },
    ).allow_extra("*"),
    t.Key("metric", default=_config_defaults["metric"]): t.Dict({
        tx.AliasedKey(
            ["address", "addr"], default=_config_defaults["metric"]["address"]
        ): tx.HostPortPair,
        tx.AliasedKey(
            # time window for range vector queries
            ["timewindow", "time-window", "time_window"],
            default=_config_defaults["metric"]["timewindow"],
        ): t.String,
    }).allow_extra("*"),
}).allow_extra("*")

_volume_defaults: dict[str, Any] = {
    "_types": {
        "user": {},
    },
}

volume_config_iv = t.Dict({
    t.Key("_types", default=_volume_defaults["_types"]): t.Dict({
        t.Key("user", optional=True): t.String(allow_blank=True) | t.Dict({}).allow_extra("*"),
        t.Key("group", optional=True): t.String(allow_blank=True) | t.Dict({}).allow_extra("*"),
    }).allow_extra("*"),
    t.Key("default_host"): t.String,
    t.Key("exposed_volume_info", default="percentage"): tx.StringList(delimiter=","),
    t.Key("proxies"): t.Mapping(
        tx.Slug,
        t.Dict({
            t.Key("client_api"): t.String,
            t.Key("manager_api"): t.String,
            t.Key("secret"): t.String,
            t.Key("ssl_verify"): t.ToBool,
            t.Key("sftp_scaling_groups", default=None): t.Null | tx.StringList(delimiter=","),
        }),
    ),
}).allow_extra("*")


ConfigWatchCallback = Callable[[Sequence[str]], Awaitable[None]]


class AbstractConfig(UserDict):
    """
    Deprecated: Use ai.backend.manager.config.unified instead.
    """

    _watch_callbacks: List[ConfigWatchCallback]

    def __init__(self, initial_data: Optional[Mapping[str, Any]] = None) -> None:
        super().__init__(initial_data)
        self._watch_callbacks = []

    @abstractmethod
    async def reload(self) -> None:
        pass

    def add_watch_callback(self, cb: ConfigWatchCallback) -> None:
        self._watch_callbacks.append(cb)

    async def dispatch_watch_callbacks(self, updated_keys: Sequence[str]) -> None:
        for cb in self._watch_callbacks:
            await cb(updated_keys)


class LocalConfig(AbstractConfig):
    async def reload(self) -> None:
        raise NotImplementedError


def load(
    config_path: Optional[Path] = None,
    log_level: LogLevel = LogLevel.NOTSET,
) -> LocalConfig:
    """
    Deprecated: Use ai.backend.manager.config.unified instead.
    """
    # Determine where to read configuration.
    raw_cfg, cfg_src_path = config.read_from_file(config_path, "manager")

    # Override the read config with environment variables (for legacy).
    config.override_with_env(raw_cfg, ("etcd", "namespace"), "BACKEND_NAMESPACE")
    config.override_with_env(raw_cfg, ("etcd", "addr"), "BACKEND_ETCD_ADDR")
    config.override_with_env(raw_cfg, ("etcd", "user"), "BACKEND_ETCD_USER")
    config.override_with_env(raw_cfg, ("etcd", "password"), "BACKEND_ETCD_PASSWORD")
    config.override_with_env(raw_cfg, ("db", "addr"), "BACKEND_DB_ADDR")
    config.override_with_env(raw_cfg, ("db", "name"), "BACKEND_DB_NAME")
    config.override_with_env(raw_cfg, ("db", "user"), "BACKEND_DB_USER")
    config.override_with_env(raw_cfg, ("db", "password"), "BACKEND_DB_PASSWORD")
    config.override_with_env(raw_cfg, ("manager", "num-proc"), "BACKEND_MANAGER_NPROC")
    config.override_with_env(raw_cfg, ("manager", "ssl-cert"), "BACKEND_SSL_CERT")
    config.override_with_env(raw_cfg, ("manager", "ssl-privkey"), "BACKEND_SSL_KEY")
    config.override_with_env(raw_cfg, ("manager", "pid-file"), "BACKEND_PID_FILE")
    config.override_with_env(raw_cfg, ("manager", "api-listen-addr", "host"), "BACKEND_SERVICE_IP")
    config.override_with_env(
        raw_cfg, ("manager", "api-listen-addr", "port"), "BACKEND_SERVICE_PORT"
    )
    config.override_with_env(
        raw_cfg, ("manager", "event-listen-addr", "host"), "BACKEND_ADVERTISED_MANAGER_HOST"
    )
    config.override_with_env(
        raw_cfg, ("manager", "event-listen-addr", "port"), "BACKEND_EVENTS_PORT"
    )
    config.override_with_env(
        raw_cfg, ("docker-registry", "ssl-verify"), "BACKEND_SKIP_SSLCERT_VALIDATION"
    )

    config.override_key(raw_cfg, ("debug", "enabled"), log_level == LogLevel.DEBUG)
    if log_level != LogLevel.NOTSET:
        config.override_key(raw_cfg, ("logging", "level"), log_level)
        config.override_key(raw_cfg, ("logging", "pkg-ns", "ai.backend"), log_level)

    # Validate and fill configurations
    # (allow_extra will make configs to be forward-compatible)
    try:
        cfg = config.check(raw_cfg, manager_local_config_iv)
        if cfg["debug"]["enabled"]:
            print("== Manager configuration ==", file=sys.stderr)
            print(pformat(cfg), file=sys.stderr)
        cfg["_src"] = cfg_src_path
        if cfg["manager"]["secret"] is None:
            cfg["manager"]["secret"] = secrets.token_urlsafe(16)
    except config.ConfigurationError as e:
        print(
            "ConfigurationError: Could not read or validate the manager local config:",
            file=sys.stderr,
        )
        print(pformat(e.invalid_data), file=sys.stderr)
        raise click.Abort()
    else:
        return LocalConfig(cfg)
