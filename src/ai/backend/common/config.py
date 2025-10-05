from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping, Optional, Tuple, Union, cast

import humps
import tomli
import trafaret as t
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
)

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


class BaseConfigSchema(BaseModel):
    @staticmethod
    def snake_to_kebab_case(string: str) -> str:
        return string.replace("_", "-")

    model_config = ConfigDict(
        validate_by_name=True,
        from_attributes=True,
        alias_generator=snake_to_kebab_case,
        validate_default=True,
    )


class BaseConfigModel(BaseModel):
    @staticmethod
    def snake_to_kebab_case(string: str) -> str:
        return string.replace("_", "-")

    model_config = ConfigDict(
        validate_by_name=True,
        from_attributes=True,
        extra="allow",
        alias_generator=snake_to_kebab_case,
    )


etcd_config_iv = t.Dict({
    t.Key("etcd"): t.Dict({
        t.Key("namespace"): t.String,
        t.Key("addr", default=("127.0.0.1", 2379)): tx.HostPortPair | t.List(tx.HostPortPair),
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
    "use_tls": False,
    "tls_skip_verify": False,
}

redis_config_iv = t.Dict({
    t.Key("addr", default=redis_default_config["addr"]): t.Null | tx.HostPortPair,
    t.Key(  # if present, addr is ignored and service_name becomes mandatory.
        "sentinel", default=redis_default_config["sentinel"]
    ): t.Null | tx.DelimiterSeperatedList(tx.HostPortPair),
    t.Key("service_name", default=redis_default_config["service_name"]): t.Null | t.String,
    t.Key("password", default=redis_default_config["password"]): t.Null | t.String,
    t.Key("use_tls", default=redis_default_config["use_tls"]): t.Bool,
    t.Key("tls_skip_verify", default=redis_default_config["tls_skip_verify"]): t.Bool,
    t.Key(
        "redis_helper_config",
        default=redis_helper_default_config,
    ): redis_helper_config_iv,
    t.Key("override_configs", default=None): t.Null
    | t.Mapping(
        t.String,
        t.Dict({
            t.Key("addr", default=redis_default_config["addr"]): t.Null | tx.HostPortPair,
            t.Key(  # if present, addr is ignored and service_name becomes mandatory.
                "sentinel", default=redis_default_config["sentinel"]
            ): t.Null | tx.DelimiterSeperatedList(tx.HostPortPair),
            t.Key("service_name", default=redis_default_config["service_name"]): t.Null | t.String,
            t.Key("password", default=redis_default_config["password"]): t.Null | t.String,
            t.Key("use_tls", default=redis_default_config["use_tls"]): t.Bool,
            t.Key("tls_skip_verify", default=redis_default_config["tls_skip_verify"]): t.Bool,
            t.Key(
                "redis_helper_config",
                default=redis_helper_default_config,
            ): redis_helper_config_iv,
        }).allow_extra("*"),
    ),
}).allow_extra("*")

vfolder_config_iv = t.Dict({
    tx.AliasedKey(["mount", "_mount"], default=None): t.Null | tx.Path(type="dir"),
    tx.AliasedKey(["fsprefix", "_fsprefix"], default=""): tx.Path(
        type="dir", resolve=False, relative_only=True, allow_nonexisting=True
    ),
}).allow_extra("*")

# Used in Etcd as a global config.
# If `scalingGroup.scheduler_opts` contains an `agent_selector_config`, it will override this.
agent_selector_globalconfig_iv = t.Dict({}).allow_extra("*")

# Used in `scalingGroup.scheduler_opts` as a per scaling_group config.
agent_selector_config_iv = t.Dict({}) | agent_selector_globalconfig_iv


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
                t.Key("start_command"): t.String | t.List(t.String),
                t.Key("shell", default="/bin/bash"): t.String,  # used if start_command is a string
                t.Key("port"): t.ToInt[1:],
                t.Key("health_check", default=None): t.Null
                | t.Dict({
                    t.Key("interval", default=10): t.Null | t.ToFloat[0:],
                    t.Key("path"): t.String,
                    t.Key("max_retries", default=10): t.Null | t.ToInt[1:],
                    t.Key("max_wait_time", default=15): t.Null | t.ToFloat[0:],
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


class PreStartAction(BaseConfigModel):
    action: str = Field(
        description="The name of the pre-start action to execute.",
        examples=["action_name"],
    )
    args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments for the pre-start action.",
        examples=[{"arg1": "value1", "arg2": "value2"}],
    )


class ModelHealthCheck(BaseConfigModel):
    interval: Optional[float] = Field(
        default=10.0,
        description="Interval in seconds between health checks.",
        examples=[10.0],
    )
    path: str = Field(
        description="Path to check for health status.",
        examples=["/health"],
    )
    max_retries: Optional[int] = Field(
        default=10,
        description="Maximum number of retries for health check.",
        examples=[10],
    )
    max_wait_time: Optional[float] = Field(
        default=15.0,
        description="Maximum time in seconds to wait for a health check response.",
        examples=[15.0],
    )
    expected_status_code: Optional[int] = Field(
        default=200,
        description="Expected HTTP status code for a healthy response.",
        examples=[200],
        gt=100,
    )


class ModelServiceConfig(BaseConfigModel):
    pre_start_actions: list[PreStartAction] = Field(
        default_factory=list,
        description="List of pre-start actions to execute before starting the model service.",
    )
    start_command: str | list[str] = Field(
        description="Command to start the model service.",
        examples=["python service.py", ["python", "service.py"]],
    )
    shell: str = Field(
        default="/bin/bash",
        description="Shell to use if start_command is a string.",
        examples=["/bin/bash"],
    )
    port: int = Field(
        description="Port number for the model service. Must be greater than 1.",
        examples=[8080],
        gt=1,
    )
    health_check: Optional[ModelHealthCheck] = Field(
        default=None,
        description="Health check configuration for the model service.",
    )


class ModelMetadata(BaseConfigModel):
    author: Optional[str] = Field(
        default=None,
        examples=["John Doe"],
    )
    title: Optional[str] = Field(
        default=None,
    )
    version: Optional[int | str] = Field(
        default=None,
    )
    created: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("created", "created_at"),
        serialization_alias="created",
    )
    last_modified: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("last_modified", "modified_at"),
        serialization_alias="last_modified",
    )
    description: Optional[str] = Field(
        default=None,
    )
    task: Optional[str] = Field(
        default=None,
    )
    category: Optional[str] = Field(
        default=None,
    )
    architecture: Optional[str] = Field(
        default=None,
    )
    framework: Optional[list[str]] = Field(
        default=None,
    )
    label: Optional[list[str]] = Field(
        default=None,
    )
    license: Optional[str] = Field(
        default=None,
    )
    min_resource: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Minimum resource requirements for the model.",
    )


class ModelConfig(BaseConfigModel):
    name: str = Field(
        description="Name of the model.",
        examples=["my_model"],
    )
    model_path: str = Field(
        description="Path to the model file.",
        examples=["/models/my_model"],
    )
    service: Optional[ModelServiceConfig] = Field(
        default=None,
        description="Configuration for the model service.",
    )
    metadata: Optional[ModelMetadata] = Field(
        default=None,
        description="Metadata about the model.",
    )


class ModelDefinition(BaseConfigModel):
    models: list[ModelConfig] = Field(
        default_factory=list,
        description="List of models in the model definition.",
    )

    def health_check_config(self) -> Optional[ModelHealthCheck]:
        for model in self.models:
            if model.service and model.service.health_check:
                if model.service.health_check is not None:
                    return model.service.health_check
        return None


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


def config_key_to_snake_case(o: Any) -> Any:
    match o:
        case dict():
            return {humps.dekebabize(k): config_key_to_snake_case(v) for k, v in o.items()}
        case list() | tuple() | set():
            return [config_key_to_snake_case(i) for i in o]
        case _:
            return o
