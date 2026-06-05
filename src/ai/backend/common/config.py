from __future__ import annotations

import os
import sys
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any, override

import humps
import tomli
import trafaret as t
from pydantic import (
    AliasChoices,
    ConfigDict,
    Field,
    model_validator,
)

from . import validators as tx
from .etcd import AsyncEtcd, ConfigScopes
from .exception import BackendAIError, ConfigurationError, ModelDefinitionValidationError
from .types import BackendAISchema, RedisHelperConfig, SchemaValidationFailureInfo

__all__ = (
    "ConfigurationError",
    "check",
    "etcd_config_iv",
    "merge",
    "override_key",
    "override_with_env",
    "read_from_etcd",
    "read_from_file",
    "redis_config_iv",
    "redis_helper_config_iv",
    "redis_helper_default_config",
    "vfolder_config_iv",
)


class BaseConfigSchema(BackendAISchema):
    @staticmethod
    def snake_to_kebab_case(string: str) -> str:
        return string.replace("_", "-")

    model_config = ConfigDict(
        validate_by_name=True,
        from_attributes=True,
        alias_generator=snake_to_kebab_case,
        validate_default=True,
    )


class BaseConfigModel(BackendAISchema):
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


DEFAULT_SHELL = "/bin/bash"


def _wrap_str_start_command_into_argv(service: Any) -> Any:
    if not isinstance(service, dict):
        return service
    sc = service.get("start_command")
    if not isinstance(sc, str):
        return service
    shell = service.get("shell")
    if shell:
        return {**service, "start_command": [shell, "-c", sc]}
    return {**service, "start_command": [sc]}


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
    enable: bool = Field(
        default=False,
        description=(
            "Whether the route should be health-checked. When false the route "
            "becomes active immediately and the remaining fields are ignored."
        ),
        examples=[False],
    )
    interval: float = Field(
        default=10.0,
        description="Interval in seconds between health checks.",
        examples=[10.0],
    )
    path: str = Field(
        default="/health",
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
    start_command: list[str] | None = Field(
        default=None,
        description=(
            "Argv list to start the model service. ``{model_path}`` in any "
            "token is replaced per-token with the resolved ``model_path`` "
            "before launch. ``None`` falls back to the image's default CMD."
        ),
        examples=[["python", "service.py"], ["vllm", "serve", "{model_path}"]],
    )
    shell: str = Field(
        default=DEFAULT_SHELL,
        description="Shell configured for the model service.",
        examples=[DEFAULT_SHELL],
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

    @model_validator(mode="before")
    @classmethod
    def _wrap_str_start_command(cls, data: Any) -> Any:
        return _wrap_str_start_command_into_argv(data)


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
            enable=_pick(hb.enable, ho.enable, "enable" in hs),
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

    @override
    @classmethod
    def build_validation_error(cls, info: SchemaValidationFailureInfo) -> BackendAIError:
        return ModelDefinitionValidationError(
            extra_msg=info.summary,
            extra_data={"errors": info.errors},
        )

    def merge(self, override: ModelDefinition) -> ModelDefinition:
        """Merge the given override into this definition, returning a new instance."""
        return _merge_definition(self, override)

    def health_check_config(self) -> ModelHealthCheck | None:
        for model in self.models:
            if model.service and model.service.health_check and model.service.health_check.enable:
                return model.service.health_check
        return None

    def with_args_appended(self, args: list[str]) -> ModelDefinition:
        """Return a copy with ``args`` appended to each model's
        ``service.start_command`` as separate argv tokens.

        Models with ``service is None`` are passed through unchanged;
        a model whose ``start_command`` is ``None`` receives ``args``
        as its initial ``start_command`` (the agent's image-CMD fallback
        is responsible for prepending a launcher when this happens).
        """
        if not args:
            return self
        new_models: list[ModelConfig] = []
        for model in self.models:
            if model.service is None:
                new_models.append(model)
                continue
            existing = model.service.start_command or []
            new_service = model.service.model_copy(
                update={"start_command": existing + args},
            )
            new_models.append(model.model_copy(update={"service": new_service}))
        return self.model_copy(update={"models": new_models})


# ============================================================================
# ModelDefinition draft types — partial-input variants used by source layers
# (preset storage, vfolder yaml, request DTO). Every field defaults to
# ``None`` so any subset can flow through ``merge`` without strict
# validation. ``to_resolved`` converts the draft back to the strict
# :class:`ModelDefinition` at the persistence boundary; required-field
# validation is delegated to Pydantic via the strict type's constructor.
# ============================================================================


class ModelHealthCheckDraft(BaseConfigModel):
    enable: bool | None = None
    interval: float | None = None
    path: str | None = None
    max_retries: int | None = None
    max_wait_time: float | None = None
    expected_status_code: int | None = None
    initial_delay: float | None = None

    def to_resolved(self) -> ModelHealthCheck:
        # Drop unset (None) fields so the strict type's ``Field(default=...)``
        # declarations remain the single source of truth for default values.
        return ModelHealthCheck.model_validate(self.model_dump(exclude_none=True))


class ModelServiceConfigDraft(BaseConfigModel):
    pre_start_actions: list[PreStartAction] | None = None
    start_command: list[str] | None = None
    shell: str | None = None
    port: int | None = None
    health_check: ModelHealthCheckDraft | None = None

    @model_validator(mode="before")
    @classmethod
    def _wrap_str_start_command(cls, data: Any) -> Any:
        return _wrap_str_start_command_into_argv(data)

    def to_resolved(self) -> ModelServiceConfig:
        # Drop unset (None) scalars so the strict type's ``Field(default=...)``
        # declarations remain the single source of truth for default values;
        # resolve the nested ``health_check`` draft explicitly. Missing
        # required fields (e.g. ``port``) surface as
        # ``BackendAISchemaValidationFailed``.
        payload = self.model_dump(exclude_none=True, exclude={"health_check"})
        payload["health_check"] = self.health_check.to_resolved() if self.health_check else None
        return ModelServiceConfig.model_validate(payload)


class ModelConfigDraft(BaseConfigModel):
    name: str | None = None
    model_path: str | None = None
    service: ModelServiceConfigDraft | None = None
    metadata: ModelMetadata | None = None  # ModelMetadata is already all-Optional.

    def to_resolved(self) -> ModelConfig:
        service = self.service.to_resolved() if self.service else None
        if service is not None and service.start_command and self.model_path is not None:
            # ``{model_path}`` placeholders in the variant baseline's
            # ``start_command`` are resolved here, at the same moment the
            # draft becomes a strict ``ModelConfig`` and ``model_path`` is
            # finalized. Placeholders therefore never propagate downstream.
            service.start_command = [
                token.replace("{model_path}", self.model_path) for token in service.start_command
            ]
        payload = self.model_dump(exclude_none=True, exclude={"service"})
        payload["service"] = service
        return ModelConfig.model_validate(payload)


def _merge_health_check_draft(
    base: ModelHealthCheckDraft,
    override: ModelHealthCheckDraft,
) -> ModelHealthCheckDraft:
    s = override.model_fields_set
    return ModelHealthCheckDraft.model_construct(
        enable=_pick(base.enable, override.enable, "enable" in s),
        interval=_pick(base.interval, override.interval, "interval" in s),
        path=_pick(base.path, override.path, "path" in s),
        max_retries=_pick(base.max_retries, override.max_retries, "max_retries" in s),
        max_wait_time=_pick(base.max_wait_time, override.max_wait_time, "max_wait_time" in s),
        expected_status_code=_pick(
            base.expected_status_code, override.expected_status_code, "expected_status_code" in s
        ),
        initial_delay=_pick(base.initial_delay, override.initial_delay, "initial_delay" in s),
    )


def _merge_service_config_draft(
    base: ModelServiceConfigDraft,
    override: ModelServiceConfigDraft,
) -> ModelServiceConfigDraft:
    s = override.model_fields_set
    health_check: ModelHealthCheckDraft | None
    if "health_check" in s and base.health_check is not None and override.health_check is not None:
        health_check = _merge_health_check_draft(base.health_check, override.health_check)
    else:
        health_check = _pick(base.health_check, override.health_check, "health_check" in s)
    return ModelServiceConfigDraft.model_construct(
        pre_start_actions=_pick(
            base.pre_start_actions, override.pre_start_actions, "pre_start_actions" in s
        ),
        start_command=_pick(base.start_command, override.start_command, "start_command" in s),
        shell=_pick(base.shell, override.shell, "shell" in s),
        port=_pick(base.port, override.port, "port" in s),
        health_check=health_check,
    )


def _merge_config_draft(
    base: ModelConfigDraft,
    override: ModelConfigDraft,
) -> ModelConfigDraft:
    s = override.model_fields_set
    service: ModelServiceConfigDraft | None
    if "service" in s and base.service is not None and override.service is not None:
        service = _merge_service_config_draft(base.service, override.service)
    else:
        service = _pick(base.service, override.service, "service" in s)
    metadata: ModelMetadata | None
    if "metadata" in s and base.metadata is not None and override.metadata is not None:
        metadata = _merge_metadata(base.metadata, override.metadata)
    else:
        metadata = _pick(base.metadata, override.metadata, "metadata" in s)
    return ModelConfigDraft.model_construct(
        name=_pick(base.name, override.name, "name" in s),
        model_path=override.model_path if override.model_path is not None else base.model_path,
        service=service,
        metadata=metadata,
    )


class ModelDefinitionDraft(BaseConfigModel):
    """Partial ModelDefinition; every field is optional.

    Drafts are produced by source layers (preset storage, vfolder yaml,
    request DTO) and merged together. Convert to a strict
    :class:`ModelDefinition` via :meth:`to_resolved` at the persistence
    boundary; required-field validation is delegated to Pydantic via the
    strict type's constructor.
    """

    models: list[ModelConfigDraft] | None = None

    @override
    @classmethod
    def build_validation_error(cls, info: SchemaValidationFailureInfo) -> BackendAIError:
        return ModelDefinitionValidationError(
            extra_msg=info.summary,
            extra_data={"errors": info.errors},
        )

    def merge(self, override: ModelDefinitionDraft) -> ModelDefinitionDraft:
        """Merge ``override`` over ``self`` and return a new draft.

        ``models`` is merged element-wise by index. Within each element,
        nested sub-models are merged recursively when both sides provide
        them; otherwise the override's value (when explicitly set) wins.
        """
        if "models" not in override.model_fields_set or override.models is None:
            return ModelDefinitionDraft.model_construct(models=self.models)
        if self.models is None or not self.models:
            return ModelDefinitionDraft.model_construct(models=override.models)
        if not override.models:
            return ModelDefinitionDraft.model_construct(models=self.models)
        merged: list[ModelConfigDraft] = []
        for i in range(max(len(self.models), len(override.models))):
            if i >= len(self.models):
                merged.append(override.models[i])
            elif i >= len(override.models):
                merged.append(self.models[i])
            else:
                merged.append(_merge_config_draft(self.models[i], override.models[i]))
        return ModelDefinitionDraft.model_construct(models=merged)

    def to_resolved(self) -> ModelDefinition:
        return ModelDefinition.model_validate({
            "models": [m.to_resolved() for m in (self.models or [])],
        })

    @classmethod
    def from_file_payload(cls, payload: Mapping[str, Any]) -> ModelDefinitionDraft:
        """Parse a model-definition file into a draft, normalizing the ``health_check`` block."""
        # Dump by field name so the keys below match regardless of snake/kebab input.
        data = cls.model_validate(dict(payload)).model_dump(exclude_unset=True, by_alias=False)
        for model in data.get("models") or []:
            service = model.get("service")
            if service is None:
                continue
            if "health_check" not in service:
                continue
            health_check = service["health_check"]
            # An empty health_check (null or {}) is an explicit opt-out; disable it so it
            # overrides any enabled baseline instead of inheriting one.
            if not health_check:
                service["health_check"] = {"enable": False}
                continue
            # A non-empty block opts in; default enable to True when unset.
            if health_check.get("enable") is None:
                health_check["enable"] = True
        return cls.model_validate(data)


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
