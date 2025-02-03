"""
Configuration Schema on etcd
----------------------------

The etcd (v3) itself is a flat key-value storage, but we use its prefix-based filtering
by using a directory-like configuration structure.
At the root, it contains "/sorna/{namespace}" as the common prefix.

In most cases, a single global configurations are sufficient, but cluster administrators
may want to apply different settings (e.g., resource slot types, vGPU sizes, etc.)
to different scaling groups or even each node.

To support such requirements, we add another level of prefix named "configuration scope".
There are three types of configuration scopes:

 * Global
 * Scaling group
 * Node

When reading configurations, the underlying `ai.backend.common.etcd.AsyncEtcd` class
returns a `collections.ChainMap` instance that merges three configuration scopes
in the order of node, scaling group, and global, so that node-level configs override
scaling-group configs, and scaling-group configs override global configs if they exist.

Note that the global scope prefix may be an empty string; this allows use of legacy
etcd databases without explicit migration.  When the global scope prefix is an empty string,
it does not make a new depth in the directory structure, so "{namespace}/config/x" (not
"{namespace}//config/x"!) is recognized as the global config.

Notes on Docker registry configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A registry name contains the host, port (only for non-standards), and the path.
So, they must be URL-quoted (including slashes) to avoid parsing
errors due to intermediate slashes and colons.
Alias keys are also URL-quoted in the same way.

{namespace}
 + ''  # ConfigScoeps.GLOBAL
   + config
     + system
       - timezone: "UTC"  # pytz-compatible timezone names (e.g., "Asia/Seoul")
     + api
       - allow-origins: "*"
       - allow-openapi-schema-introspection: "yes" | "no"  # (default: no)
       - allow-graphql-schema-introspection: "yes" | "no"  # (default: no)
       + resources
         - group_resource_visibility: "true"  # return group resource status in check-presets
                                              # (default: false)
     + docker
       + image
         - auto_pull: "digest" (default) | "tag" | "none"
     + redis
       - addr: "{redis-host}:{redis-port}"
       - password: {password}
     + idle
       - enabled: "timeout,utilization"      # comma-separated list of checker names
       - app-streaming-packet-timeout: "5m"  # in seconds; idleness of app-streaming TCP connections
         # NOTE: idle checkers get activated AFTER the app-streaming packet timeout has passed.
       - checkers
         + "timeout"
           - threshold: "10m"
         + "utilization"
           + resource-thresholds
             + "cpu_util"
               - average: 30  # in percent
             + "mem"
               - average: 30  # in percent
             + "cuda_util"
               - average: 30  # in percent  # CUDA core utilization
             + "cuda_mem"
               - average: 30  # in percent
               # NOTE: To use "cuda.mem" criteria, user programs must use
               #       an incremental allocation strategy for CUDA memory.
           - thresholds-check-operator: "and"
             # "and" (default, so any other words except the "or"):
             #     garbage collect a session only when ALL of the resources are
             #     under-utilized not exceeding their thresholds.
             #     ex) (cpu < threshold) AND (mem < threshold) AND ...
             # "or":
             #     garbage collect a session when ANY of the resources is
             #     under-utilized not exceeding their thresholds.
             #     ex) (cpu < threshold) OR (mem < threshold) OR ...
           - time-window: "12h"  # time window to average utilization
                                 # a session will not be terminated until this time
           - initial-grace-period: "5m" # time to allow to be idle for first
         # "session_lifetime" does not have etcd config but it is configured via
         # the keypair_resource_polices table.
     + resource_slots
       - {"cuda.device"}: {"count"}
       - {"cuda.mem"}: {"bytes"}
       - {"cuda.smp"}: {"count"}
       ...
     + plugins
       + accelerator
         + "cuda"
           - allocation_mode: "discrete"
           ...
       + network
         + "overlay"
           - mtu: 1500  # Maximum Transmission Unit
       + scheduler
         + "fifo"
         + "lifo"
         + "drf"
         ...
     + network
       + inter-container:
         - default-driver: "overlay"
       + subnet
         - agent: "0.0.0.0/0"
         - container: "0.0.0.0/0"
       + rpc
         - keepalive-timeout: 60  # seconds
     + watcher
       - token: {some-secret}
   + volumes
     - _types     # allowed vfolder types
       + "user"   # enabled if present
       + "group"  # enabled if present
     # 20.09 and later
     - default_host: "{default-proxy}:{default-volume}"
     + proxies:   # each proxy may provide multiple volumes
       + "local"  # proxy name
         - client_api: "http://localhost:6021"
         - manager_api: "http://localhost:6022"
         - secret: "xxxxxx..."       # for manager API
         - ssl_verify: true | false  # for manager API
         - sftp_scaling_groups: "group-1,group-2,..."
       + "mynas1"
         - client_api: "https://proxy1.example.com:6021"
         - manager_api: "https://proxy1.example.com:6022"
         - secret: "xxxxxx..."       # for manager API
         - ssl_verify: true | false  # for manager API
         - sftp_scaling_groups: "group-3,group-4,..."
     # 23.03 and later
       + exposed_volume_info: "percentage"
       ...
     ...
   ...
 + nodes
   + manager
     - {instance-id}: "up"
     ...
   # etcd.get("config/redis/addr") is not None => single redis node
   # etcd.get("config/redis/sentinel") is not None => redis sentinel
   + redis:
     - addr: "tcp://redis:6379"
     - sentinel: {comma-seperated list of sentinel addresses}
     - service_name: "mymanager"
     - password: {redis-auth-password}
   + agents
     + {instance-id}: {"starting","running"}  # ConfigScopes.NODE
       - ip: {"127.0.0.1"}
       - watcher_port: {"6009"}
     ...
 + sgroup
   + {name}  # ConfigScopes.SGROUP
     - swarm-manager/token
     - swarm-manager/host
     - swarm-worker/token
     - iprange          # to choose ethernet iface when creating containers
     - resource_policy  # the name of scaling-group resource-policy in database
     + nodes
       - {instance-id}: 1  # just a membership set
"""

from __future__ import annotations

import logging
import os
import secrets
import socket
import sys
import urllib.parse
from abc import abstractmethod
from collections import UserDict
from collections.abc import Mapping
from contextvars import ContextVar
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

import aiotools
import click
import trafaret as t
import yarl

from ai.backend.common import config
from ai.backend.common import validators as tx
from ai.backend.common.defs import DEFAULT_FILE_IO_TIMEOUT
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.etcd_etcetra import AsyncEtcd as EtcetraAsyncEtcd
from ai.backend.common.identity import get_instance_id
from ai.backend.common.lock import EtcdLock, FileLock, RedisLock
from ai.backend.common.types import (
    HostPortPair,
    SlotName,
    SlotTypes,
    current_resource_slots,
)
from ai.backend.logging import BraceStyleAdapter, LogLevel

from ..manager.defs import INTRINSIC_SLOTS
from .api import ManagerStatus
from .api.exceptions import ServerMisconfiguredError
from .models.session import SessionStatus
from .pglock import PgAdvisoryLock

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_max_cpu_count = os.cpu_count()
_file_perm = (Path(__file__).parent / "server.py").stat()

DEFAULT_CHUNK_SIZE: Final = 256 * 1024  # 256 KiB
DEFAULT_INFLIGHT_CHUNKS: Final = 8

NestedStrKeyedDict: TypeAlias = "dict[str, Any | NestedStrKeyedDict]"

current_vfolder_types: ContextVar[List[str]] = ContextVar("current_vfolder_types")

_default_pyroscope_config: dict[str, Any] = {
    "enabled": False,
    "app-name": None,
    "server-addr": None,
    "sample-rate": None,
}

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
                "filelock",
                "pg_advisory",
                "redlock",
                "etcd",
                "etcetra",
            ),
            t.Key(
                "pg-advisory-config", default=PgAdvisoryLock.default_config
            ): PgAdvisoryLock.config_iv,
            t.Key("filelock-config", default=FileLock.default_config): FileLock.config_iv,
            t.Key("redlock-config", default=RedisLock.default_config): RedisLock.config_iv,
            t.Key("etcdlock-config", default=EtcdLock.default_config): EtcdLock.config_iv,
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
            tx.AliasedKey(["aiomonitor-termui-port", "aiomonitor-port"], default=48100): t.ToInt[
                1:65535
            ],
            t.Key("aiomonitor-webui-port", default=49100): t.ToInt[1:65535],
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
        config.override_key(raw_cfg, ("logging", "pkg-ns", "aiohttp"), log_level)

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


class SharedConfig(AbstractConfig):
    def __init__(
        self,
        etcd_addr: HostPortPair,
        etcd_user: Optional[str],
        etcd_password: Optional[str],
        namespace: str,
    ) -> None:
        super().__init__()
        credentials = None
        if etcd_user:
            assert etcd_user is not None
            assert etcd_password is not None
            credentials = {
                "user": etcd_user,
                "password": etcd_password,
            }
        scope_prefix_map = {
            ConfigScopes.GLOBAL: "",
            # TODO: provide a way to specify other scope prefixes
        }
        self.etcd = AsyncEtcd(etcd_addr, namespace, scope_prefix_map, credentials=credentials)
        self.etcetra_etcd = EtcetraAsyncEtcd(
            etcd_addr, namespace, scope_prefix_map, credentials=credentials
        )

    async def close(self) -> None:
        await self.etcd.close()

    async def reload(self) -> None:
        raw_cfg = await self.etcd.get_prefix("config")
        try:
            cfg = shared_config_iv.check(raw_cfg)
        except config.ConfigurationError as e:
            print("Validation of shared etcd configuration has failed:", file=sys.stderr)
            print(pformat(e.invalid_data), file=sys.stderr)
            raise click.Abort()
        else:
            self.data = cfg

    def __hash__(self) -> int:
        # When used as a key in dicts, we don't care our contents.
        # Just treat it like an opaque object.
        return hash(id(self))

    @classmethod
    def flatten(cls, key_prefix: str, inner_dict: NestedStrKeyedDict) -> dict[str, str]:
        flattend_dict: dict[str, str] = {}
        for k, v in inner_dict.items():
            if k == "":
                flattened_key = key_prefix
            else:
                flattened_key = key_prefix + "/" + urllib.parse.quote(k, safe="")
            match v:
                case Mapping():
                    flattend_dict.update(cls.flatten(flattened_key, v))  # type: ignore
                case str():
                    flattend_dict[flattened_key] = v
                case int() | float() | yarl.URL():
                    flattend_dict[flattened_key] = str(v)
                case _:
                    raise ValueError(
                        f"The value {v!r} must be serialized before storing to the etcd"
                    )
        return flattend_dict

    async def get_raw(self, key: str, allow_null: bool = True) -> Optional[str]:
        value = await self.etcd.get(key)
        if not allow_null and value is None:
            raise ServerMisconfiguredError("A required etcd config is missing.", key)
        return value

    async def register_myself(self) -> None:
        instance_id = await get_instance_id()
        manager_info = {
            f"nodes/manager/{instance_id}": "up",
        }
        await self.etcd.put_dict(manager_info)

    async def deregister_myself(self) -> None:
        instance_id = await get_instance_id()
        await self.etcd.delete_prefix(f"nodes/manager/{instance_id}")

    async def update_resource_slots(
        self,
        slot_key_and_units: Mapping[SlotName, SlotTypes],
    ) -> None:
        updates = {}
        known_slots = await self.get_resource_slots()
        for k, v in slot_key_and_units.items():
            if k not in known_slots or v != known_slots[k]:
                updates[f"config/resource_slots/{k}"] = v.value
        if updates:
            await self.etcd.put_dict(updates)

    async def update_manager_status(self, status) -> None:
        await self.etcd.put("manager/status", status.value)
        self.get_manager_status.cache_clear()

    @aiotools.lru_cache(maxsize=1, expire_after=2.0)
    async def _get_resource_slots(self):
        raw_data = await self.etcd.get_prefix_dict("config/resource_slots")
        return {SlotName(k): SlotTypes(v) for k, v in raw_data.items()}

    async def get_resource_slots(self) -> Mapping[SlotName, SlotTypes]:
        """
        Returns the system-wide known resource slots and their units.
        """
        try:
            ret = current_resource_slots.get()
        except LookupError:
            configured_slots = await self._get_resource_slots()
            ret = {**INTRINSIC_SLOTS, **configured_slots}
            current_resource_slots.set(ret)
        return ret

    @aiotools.lru_cache(maxsize=1, expire_after=2.0)
    async def _get_vfolder_types(self):
        return await self.etcd.get_prefix("volumes/_types")

    async def get_vfolder_types(self) -> Sequence[str]:
        """
        Returns the vfolder types currently set. One of "user" and/or "group".
        If none is specified, "user" type is implicitly assumed.
        """
        try:
            ret = current_vfolder_types.get()
        except LookupError:
            vf_types = await self._get_vfolder_types()
            ret = list(vf_types.keys())
            current_vfolder_types.set(ret)
        return ret

    @aiotools.lru_cache(maxsize=1, expire_after=5.0)
    async def get_manager_nodes_info(self):
        return await self.etcd.get_prefix_dict("nodes/manager")

    @aiotools.lru_cache(maxsize=1, expire_after=2.0)
    async def get_manager_status(self) -> ManagerStatus:
        status = await self.etcd.get("manager/status")
        if status is None:
            return ManagerStatus.TERMINATED
        return ManagerStatus(status)

    async def watch_manager_status(self):
        async with aiotools.aclosing(self.etcd.watch("manager/status")) as agen:
            async for ev in agen:
                yield ev

    # TODO: refactor using contextvars in Python 3.7 so that the result is cached
    #       in a per-request basis.
    @aiotools.lru_cache(maxsize=1, expire_after=2.0)
    async def get_allowed_origins(self):
        return await self.etcd.get("config/api/allow-origins")

    def get_redis_url(self, db: int = 0) -> yarl.URL:
        """
        Returns a complete URL composed from the given Redis config.
        """
        url = yarl.URL("redis://host").with_host(str(self.data["redis"]["addr"][0])).with_port(
            self.data["redis"]["addr"][1]
        ).with_password(self.data["redis"]["password"]) / str(db)
        return url
