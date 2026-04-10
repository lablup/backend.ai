from __future__ import annotations

import os
import sys
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any

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
    "check",
    "etcd_config_iv",
    "merge",
    "model_definition_iv",
    "override_key",
    "override_with_env",
    "read_from_etcd",
    "read_from_file",
    "redis_config_iv",
    "redis_helper_config_iv",
    "redis_helper_default_config",
    "vfolder_config_iv",
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
                    t.Key("initial_delay", default=60): t.Null | t.ToFloat[0:],
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
    args: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments for the pre-start action.",
        examples=[{"arg1": "value1", "arg2": "value2"}],
    )


class ModelHealthCheck(BaseConfigModel):
    interval: float = Field(
        default=10.0,
        description="Interval in seconds between health checks.",
        examples=[10.0],
    )
    path: str = Field(
        description="Path to check for health status.",
        examples=["/health"],
    )
    max_retries: int = Field(
        default=10,
        description="Maximum number of retries for health check.",
        examples=[10],
    )
    max_wait_time: float = Field(
        default=15.0,
        description="Maximum time in seconds to wait for a health check response.",
        examples=[15.0],
    )
    expected_status_code: int = Field(
        default=200,
        description="Expected HTTP status code for a healthy response.",
        examples=[200],
        gt=100,
    )
    initial_delay: float = Field(
        default=60.0,
        description="Initial delay in seconds before the first health check.",
        examples=[60.0],
        ge=0,
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
    health_check: ModelHealthCheck | None = Field(
        default=None,
        description="Health check configuration for the model service.",
    )


class ModelMetadata(BaseConfigModel):
    author: str | None = Field(
        default=None,
        examples=["John Doe"],
    )
    title: str | None = Field(
        default=None,
    )
    version: int | str | None = Field(
        default=None,
    )
    created: str | None = Field(
        default=None,
        validation_alias=AliasChoices("created", "created_at"),
        serialization_alias="created",
    )
    last_modified: str | None = Field(
        default=None,
        validation_alias=AliasChoices("last_modified", "modified_at"),
        serialization_alias="last_modified",
    )
    description: str | None = Field(
        default=None,
    )
    task: str | None = Field(
        default=None,
    )
    category: str | None = Field(
        default=None,
    )
    architecture: str | None = Field(
        default=None,
    )
    framework: list[str] | None = Field(
        default=None,
    )
    label: list[str] | None = Field(
        default=None,
    )
    license: str | None = Field(
        default=None,
    )
    min_resource: dict[str, Any] | None = Field(
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
    service: ModelServiceConfig | None = Field(
        default=None,
        description="Configuration for the model service.",
    )
    metadata: ModelMetadata | None = Field(
        default=None,
        description="Metadata about the model.",
    )


def _pick(base_val: Any, override_val: Any, override_set: bool) -> Any:
    """Return the override value if explicitly set, otherwise the base.

    Distinguishes between unset (not in model_fields_set → keep base)
    and explicitly set to None (in model_fields_set → replace with None).
    """
    if not override_set:
        return base_val
    return override_val


def _merge_metadata(base: ModelMetadata, override: ModelMetadata) -> ModelMetadata:
    """Merge two ModelMetadata instances. All fields are atomic."""
    s = override.model_fields_set
    return ModelMetadata.model_construct(
        author=_pick(base.author, override.author, "author" in s),
        title=_pick(base.title, override.title, "title" in s),
        version=_pick(base.version, override.version, "version" in s),
        created=_pick(base.created, override.created, "created" in s),
        last_modified=_pick(base.last_modified, override.last_modified, "last_modified" in s),
        description=_pick(base.description, override.description, "description" in s),
        task=_pick(base.task, override.task, "task" in s),
        category=_pick(base.category, override.category, "category" in s),
        architecture=_pick(base.architecture, override.architecture, "architecture" in s),
        framework=_pick(base.framework, override.framework, "framework" in s),
        label=_pick(base.label, override.label, "label" in s),
        license=_pick(base.license, override.license, "license" in s),
        min_resource=_pick(base.min_resource, override.min_resource, "min_resource" in s),
    )


def _merge_service_config(
    base: ModelServiceConfig,
    override: ModelServiceConfig,
) -> ModelServiceConfig:
    """Merge two ModelServiceConfig instances.

    ``health_check`` is merged field-by-field; all other fields
    (``start_command``, ``pre_start_actions``, etc.) are replaced atomically.
    """
    s = override.model_fields_set
    health_check: ModelHealthCheck | None
    if "health_check" in s and base.health_check is not None and override.health_check is not None:
        hb, ho = base.health_check, override.health_check
        hs = ho.model_fields_set
        health_check = ModelHealthCheck.model_construct(
            interval=_pick(hb.interval, ho.interval, "interval" in hs),
            path=_pick(hb.path, ho.path, "path" in hs),
            max_retries=_pick(hb.max_retries, ho.max_retries, "max_retries" in hs),
            max_wait_time=_pick(hb.max_wait_time, ho.max_wait_time, "max_wait_time" in hs),
            expected_status_code=_pick(
                hb.expected_status_code, ho.expected_status_code, "expected_status_code" in hs
            ),
            initial_delay=_pick(hb.initial_delay, ho.initial_delay, "initial_delay" in hs),
        )
    else:
        health_check = _pick(base.health_check, override.health_check, "health_check" in s)
    return ModelServiceConfig.model_construct(
        pre_start_actions=_pick(
            base.pre_start_actions, override.pre_start_actions, "pre_start_actions" in s
        ),
        start_command=_pick(base.start_command, override.start_command, "start_command" in s),
        shell=_pick(base.shell, override.shell, "shell" in s),
        port=_pick(base.port, override.port, "port" in s),
        health_check=health_check,
    )


def _merge_config(base: ModelConfig, override: ModelConfig) -> ModelConfig:
    """Merge two ModelConfig instances.

    ``service`` and ``metadata`` sub-models are merged recursively;
    all other fields are replaced atomically.
    """
    s = override.model_fields_set
    service: ModelServiceConfig | None
    if "service" in s and base.service is not None and override.service is not None:
        service = _merge_service_config(base.service, override.service)
    else:
        service = _pick(base.service, override.service, "service" in s)
    metadata: ModelMetadata | None
    if "metadata" in s and base.metadata is not None and override.metadata is not None:
        metadata = _merge_metadata(base.metadata, override.metadata)
    else:
        metadata = _pick(base.metadata, override.metadata, "metadata" in s)
    return ModelConfig.model_construct(
        name=_pick(base.name, override.name, "name" in s),
        model_path=_pick(base.model_path, override.model_path, "model_path" in s),
        service=service,
        metadata=metadata,
    )


def _merge_definition(base: ModelDefinition, override: ModelDefinition) -> ModelDefinition:
    """Merge two ModelDefinition instances.

    The ``models`` list is merged by index — each element pair is merged
    via :func:`_merge_config`.  All other fields are replaced atomically.
    """
    models: list[ModelConfig]
    if "models" not in override.model_fields_set:
        models = base.models
    elif not base.models or not override.models:
        models = override.models
    else:
        models = []
        for i in range(max(len(base.models), len(override.models))):
            if i >= len(base.models):
                models.append(override.models[i])
            elif i >= len(override.models):
                models.append(base.models[i])
            else:
                models.append(_merge_config(base.models[i], override.models[i]))
    return ModelDefinition.model_construct(models=models)


class ModelDefinition(BaseConfigModel):
    models: list[ModelConfig] = Field(
        default_factory=list,
        description="List of models in the model definition.",
    )

    def merge(self, override: ModelDefinition) -> ModelDefinition:
        """Merge the given override into this definition, returning a new instance."""
        return _merge_definition(self, override)

    def health_check_config(self) -> ModelHealthCheck | None:
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


def read_from_file(toml_path: Path | str | None, daemon_name: str) -> tuple[dict[str, Any], Path]:
    config: dict[str, Any]
    discovered_path: Path
    if toml_path is None:
        discovered_path = find_config_file(daemon_name)
    else:
        discovered_path = Path(toml_path)
    try:
        config = tomli.loads(discovered_path.read_text())
    except OSError as e:
        raise ConfigurationError({
            "read_from_file()": f"Could not read config from: {discovered_path}",
        }) from e
    else:
        return config, discovered_path


async def read_from_etcd(
    etcd_config: Mapping[str, Any], scope_prefix_map: Mapping[ConfigScopes, str]
) -> dict[str, Any] | None:
    async with AsyncEtcd(etcd_config["addr"], etcd_config["namespace"], scope_prefix_map) as etcd:
        raw_value = await etcd.get("daemon/config")
    if raw_value is None:
        return None
    config: dict[str, Any]
    config = tomli.loads(raw_value)
    return config


def override_key(table: MutableMapping[str, Any], key_path: tuple[str, ...], value: Any) -> None:
    for k in key_path[:-1]:
        if k not in table:
            table[k] = {}
        table = table[k]
    table[key_path[-1]] = value


def override_with_env(
    table: MutableMapping[str, Any], key_path: tuple[str, ...], env_key: str
) -> None:
    val = os.environ.get(env_key, None)
    if val is None:
        return
    override_key(table, key_path, val)


def check(table: Any, iv: t.Trafaret) -> Any:
    try:
        config = iv.check(table)
    except t.DataError as e:
        err_data = e.as_dict()
        if isinstance(err_data, str):
            raise ConfigurationError({"error": err_data}) from e
        raise ConfigurationError(err_data) from e
    else:
        return config


def merge(table: Mapping[str, Any], updates: Mapping[str, Any]) -> Mapping[str, Any]:
    result = {**table}
    for k, v in updates.items():
        if isinstance(v, Mapping):
            orig = result.get(k, {})
            if not isinstance(orig, Mapping):
                raise TypeError(f"Cannot merge non-mapping value at key {k!r}")
            result[k] = merge(orig, v)
        else:
            result[k] = v
    return result


def set_if_not_set(table: MutableMapping[str, Any], key_path: tuple[str, ...], value: Any) -> None:
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
