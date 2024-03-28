from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping, Optional, Tuple, Union, cast

import tomli
import trafaret as t

from . import validators as tx
from .etcd import AsyncEtcd, ConfigScopes
from .exception import ConfigurationError
from .types import RedisHelperConfig

__all__ = (
    "ConfigurationError",
    "etcd_config_iv",
    "redis_config_iv",
    "redis_helper_config_iv",
    "redis_helper_default_config",
    "vfolder_config_iv",
    "model_definition_iv",
    "read_from_file",
    "read_from_etcd",
    "override_key",
    "override_with_env",
    "check",
    "merge",
)

etcd_config_iv = t.Dict({
    t.Key("etcd"): t.Dict({
        t.Key("namespace"): t.String,
        t.Key("addr", ("127.0.0.1", 2379)): tx.HostPortPair,
        t.Key("user", default=""): t.Null | t.String(allow_blank=True),
        t.Key("password", default=""): t.Null | t.String(allow_blank=True),
    }).allow_extra("*"),
}).allow_extra("*")

redis_helper_default_config: RedisHelperConfig = {
    "socket_timeout": 5.0,
    "socket_connect_timeout": 2.0,
    "reconnect_poll_timeout": 0.3,
}

redis_helper_config_iv = t.Dict({
    t.Key("socket_timeout", default=5.0): t.ToFloat,
    t.Key("socket_connect_timeout", default=2.0): t.ToFloat,
    t.Key("reconnect_poll_timeout", default=0.3): t.ToFloat,
}).allow_extra("*")

redis_default_config = {
    "addr": None,
    "sentinel": None,
    "service_name": None,
    "password": None,
    "redis_helper_config": redis_helper_default_config,
}

redis_config_iv = t.Dict({
    t.Key("addr", default=redis_default_config["addr"]): t.Null | tx.HostPortPair,
    t.Key(  # if present, addr is ignored and service_name becomes mandatory.
        "sentinel", default=redis_default_config["sentinel"]
    ): t.Null | tx.DelimiterSeperatedList(tx.HostPortPair),
    t.Key("service_name", default=redis_default_config["service_name"]): t.Null | t.String,
    t.Key("password", default=redis_default_config["password"]): t.Null | t.String,
    t.Key(
        "redis_helper_config",
        default=redis_helper_default_config,
    ): redis_helper_config_iv,
}).allow_extra("*")

vfolder_config_iv = t.Dict({
    tx.AliasedKey(["mount", "_mount"], default=None): t.Null | tx.Path(type="dir"),
    tx.AliasedKey(["fsprefix", "_fsprefix"], default=""): tx.Path(
        type="dir", resolve=False, relative_only=True, allow_nonexisting=True
    ),
}).allow_extra("*")

model_definition_iv = t.Dict({
    t.Key("models"): t.List(
        t.Dict({
            t.Key("name"): t.String,
            t.Key("model_path"): t.String,
            t.Key("service", default=None): t.Null
            | t.Dict({
                # ai.backend.kernel.service.ServiceParser.start_service()
                # ai.backend.kernel.service_actions
                t.Key("pre_start_actions", default=[]): t.Null
                | t.List(
                    t.Dict({
                        t.Key("action"): t.String,
                        t.Key("args"): t.Dict().allow_extra("*"),
                    })
                ),
                t.Key("start_command"): t.List(t.String),
                t.Key("port"): t.ToInt[1:],
                t.Key("health_check", default=None): t.Null
                | t.Dict({
                    t.Key("path"): t.String,
                    t.Key("max_retries", default=10): t.Null | t.ToInt[1:],
                    t.Key("max_wait_time", default=5): t.Null | t.ToFloat[0:],
                    t.Key("expected_status_code", default=200): t.Null | t.ToInt[100:],
                }),
            }),
            t.Key("metadata", default=None): t.Null
            | t.Dict({
                t.Key("author", default=None): t.Null | t.String(allow_blank=True),
                t.Key("title", default=None): t.Null | t.String(allow_blank=True),
                t.Key("version", default=None): t.Null | t.Int | t.String,
                tx.AliasedKey(["created", "created_at"], default=None): t.Null
                | t.String(allow_blank=True),
                tx.AliasedKey(["last_modified", "modified_at"], default=None): t.Null
                | t.String(allow_blank=True),
                t.Key("description", default=None): t.Null | t.String(allow_blank=True),
                t.Key("task", default=None): t.Null | t.String(allow_blank=True),
                t.Key("category", default=None): t.Null | t.String(allow_blank=True),
                t.Key("architecture", default=None): t.Null | t.String(allow_blank=True),
                t.Key("framework", default=None): t.Null | t.List(t.String),
                t.Key("label", default=None): t.Null | t.List(t.String),
                t.Key("license", default=None): t.Null | t.String(allow_blank=True),
                t.Key("min_resource", default=None): t.Null | t.Dict().allow_extra("*"),
            }).allow_extra("*"),
        })
    )
})


def find_config_file(daemon_name: str) -> Path:
    toml_path_from_env = os.environ.get("BACKEND_CONFIG_FILE", None)
    if not toml_path_from_env:
        toml_paths = [
            Path.cwd() / f"{daemon_name}.toml",
        ]
        if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
            parent_path = Path.cwd().parent
            while parent_path.is_relative_to(Path.home()):
                if (parent_path / "BUILD_ROOT").exists():
                    toml_paths.append(parent_path / f"{daemon_name}.toml")
                parent_path = parent_path.parent
            toml_paths += [
                Path.home() / ".config" / "backend.ai" / f"{daemon_name}.toml",
                Path(f"/etc/backend.ai/{daemon_name}.toml"),
            ]
        else:
            raise ConfigurationError({
                "read_from_file()": (
                    f"Unsupported platform for config path auto-discovery: {sys.platform}"
                ),
            })
    else:
        toml_paths = [Path(toml_path_from_env)]
    for _path in toml_paths:
        if _path.is_file():
            return _path
    else:
        searched_paths = ",".join(map(str, toml_paths))
        raise ConfigurationError({
            "find_config_file()": f"Could not read config from: {searched_paths}",
        })


def read_from_file(
    toml_path: Optional[Union[Path, str]], daemon_name: str
) -> Tuple[Dict[str, Any], Path]:
    config: Dict[str, Any]
    discovered_path: Path
    if toml_path is None:
        discovered_path = find_config_file(daemon_name)
    else:
        discovered_path = Path(toml_path)
    try:
        config = cast(Dict[str, Any], tomli.loads(discovered_path.read_text()))
    except IOError:
        raise ConfigurationError({
            "read_from_file()": f"Could not read config from: {discovered_path}",
        })
    else:
        return config, discovered_path


async def read_from_etcd(
    etcd_config: Mapping[str, Any], scope_prefix_map: Mapping[ConfigScopes, str]
) -> Optional[Dict[str, Any]]:
    etcd = AsyncEtcd(etcd_config["addr"], etcd_config["namespace"], scope_prefix_map)
    raw_value = await etcd.get("daemon/config")
    if raw_value is None:
        return None
    config: Dict[str, Any]
    config = cast(Dict[str, Any], tomli.loads(raw_value))
    return config


def override_key(table: MutableMapping[str, Any], key_path: Tuple[str, ...], value: Any):
    for k in key_path[:-1]:
        if k not in table:
            table[k] = {}
        table = table[k]
    table[key_path[-1]] = value


def override_with_env(table: MutableMapping[str, Any], key_path: Tuple[str, ...], env_key: str):
    val = os.environ.get(env_key, None)
    if val is None:
        return
    override_key(table, key_path, val)


def check(table: Any, iv: t.Trafaret):
    try:
        config = iv.check(table)
    except t.DataError as e:
        raise ConfigurationError(e.as_dict())
    else:
        return config


def merge(table: Mapping[str, Any], updates: Mapping[str, Any]) -> Mapping[str, Any]:
    result = {**table}
    for k, v in updates.items():
        if isinstance(v, Mapping):
            orig = result.get(k, {})
            assert isinstance(orig, Mapping)
            result[k] = merge(orig, v)
        else:
            result[k] = v
    return result


def set_if_not_set(table: MutableMapping[str, Any], key_path: Tuple[str, ...], value: Any) -> None:
    for k in key_path[:-1]:
        if k not in table:
            return
        table = table[k]
    if table.get(key_path[-1]) is None:
        table[key_path[-1]] = value
