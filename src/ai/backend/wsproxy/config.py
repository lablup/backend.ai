import os
import pwd
import socket
import sys
import types
import typing
from dataclasses import dataclass
from pathlib import Path
from pprint import pformat
from typing import Annotated, Any

import click
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    ValidationError,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import PydanticUndefined, core_schema

from ai.backend.common import config
from ai.backend.logging import LogLevel
from ai.backend.logging.config_pydantic import LoggingConfig

from .types import EventLoopType, ProxyProtocol

_file_perm = (Path(__file__).parent / "server.py").stat()


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
    )


@dataclass
class UserID:
    default_uid: int | None = None

    @classmethod
    def uid_validator(
        cls,
        value: int | str | None,
    ) -> int:
        if value is None:
            assert cls.default_uid, "value is None but default_uid not provided"
            return cls.default_uid
        assert isinstance(value, (int, str)), "value must be an integer"
        match value:
            case int():
                if value == -1:
                    return os.getuid()
                else:
                    return value
            case str():
                try:
                    _value = int(value)
                    if _value == -1:
                        return os.getuid()
                    else:
                        return _value
                except ValueError:
                    try:
                        return pwd.getpwnam(value).pw_uid
                    except KeyError:
                        assert False, f"no such user {value} in system"

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        schema = core_schema.chain_schema([
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.str_schema(),
            ]),
            core_schema.no_info_plain_validator_function(cls.uid_validator),
        ])

        return core_schema.json_or_python_schema(
            json_schema=schema,
            python_schema=core_schema.union_schema([
                # check if it's an instance first before doing any further work
                core_schema.union_schema([
                    core_schema.is_instance_schema(int),
                    core_schema.is_instance_schema(str),
                ]),
                schema,
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(int),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `int`
        return handler(
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.str_schema(),
            ])
        )


@dataclass
class GroupID:
    default_gid: int | None = None

    @classmethod
    def uid_validator(
        cls,
        value: int | str | None,
    ) -> int:
        if value is None:
            assert cls.default_gid, "value is None but default_gid not provided"
        assert isinstance(value, (int, str)), "value must be an integer"
        match value:
            case int():
                if value == -1:
                    return os.getgid()
                else:
                    return value
            case str():
                try:
                    _value = int(value)
                    if _value == -1:
                        return os.getgid()
                    else:
                        return _value
                except ValueError:
                    try:
                        return pwd.getpwnam(value).pw_gid
                    except KeyError:
                        assert False, f"no such user {value} in system"

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        schema = core_schema.chain_schema([
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.str_schema(),
            ]),
            core_schema.no_info_plain_validator_function(cls.uid_validator),
        ])

        return core_schema.json_or_python_schema(
            json_schema=schema,
            python_schema=core_schema.union_schema([
                # check if it's an instance first before doing any further work
                core_schema.union_schema([
                    core_schema.is_instance_schema(int),
                    core_schema.is_instance_schema(str),
                ]),
                schema,
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(int),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `int`
        return handler(
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.str_schema(),
            ])
        )


class DebugConfig(BaseSchema):
    enabled: Annotated[bool, Field(default=False)]
    asyncio: Annotated[bool, Field(default=False)]
    enhanced_aiomonitor_task_info: Annotated[bool, Field(default=False)]
    log_events: Annotated[bool, Field(default=False)]


class WSProxyConfig(BaseSchema):
    ipc_base_path: Annotated[
        Path,
        Field(
            default=Path("/tmp/backend.ai/ipc"),
            description="Directory to store temporary UNIX sockets.",
        ),
    ]
    event_loop: Annotated[
        EventLoopType,
        Field(default=EventLoopType.ASYNCIO, description="Type of event loop to use."),
    ]
    pid_file: Annotated[
        Path,
        Field(
            default=Path(os.devnull),
            description="Place to store process PID.",
            examples=["/run/backend.ai/wsproxy/wsproxy.pid"],
        ),
    ]

    id: Annotated[
        str,
        Field(default=f"i-{socket.gethostname()}", examples=["i-node01"], description="Node id."),
    ]
    user: Annotated[
        int,
        UserID(default_uid=_file_perm.st_uid),
        Field(default=_file_perm.st_uid, description="Process owner."),
    ]
    group: Annotated[
        int,
        GroupID(default_gid=_file_perm.st_gid),
        Field(default=_file_perm.st_uid, description="Process group."),
    ]

    bind_host: Annotated[
        str,
        Field(
            default="0.0.0.0",
            description="Bind address of the port opened on behalf of wsproxy worker",
        ),
    ]
    advertised_host: Annotated[
        str, Field(examples=["example.com"], description="Hostname to be advertised to client")
    ]

    bind_api_port: Annotated[
        int, Field(default=5050, description="Port number to bind for API server")
    ]
    advertised_api_port: Annotated[
        int | None,
        Field(default=None, examples=[15050], description="API port number reachable from client"),
    ]

    bind_proxy_port_range: Annotated[
        tuple[int, int],
        Field(default=[10200, 10300], description="Port number to bind for actual traffic"),
    ]
    advertised_proxy_port_range: Annotated[
        tuple[int, int] | None,
        Field(
            default=None,
            examples=[[20200, 20300]],
            description="Traffic port range reachable from client",
        ),
    ]

    protocol: Annotated[
        ProxyProtocol, Field(default=ProxyProtocol.HTTP, description="Proxy protocol")
    ]

    jwt_encrypt_key: Annotated[
        str, Field(examples=["50M3G00DL00KING53CR3T"], description="JWT encryption key")
    ]
    permit_hash_key: Annotated[
        str, Field(examples=["50M3G00DL00KING53CR3T"], description="Permit hash key")
    ]

    api_secret: Annotated[str, Field(examples=["50M3G00DL00KING53CR3T"], description="API secret")]

    aiomonitor_termui_port: Annotated[
        int,
        Field(
            gt=0, lt=65536, description="Port number for aiomonitor termui server.", default=48500
        ),
    ]
    aiomonitor_webui_port: Annotated[
        int,
        Field(
            gt=0, lt=65536, description="Port number for aiomonitor webui server.", default=49500
        ),
    ]


class ServerConfig(BaseSchema):
    wsproxy: WSProxyConfig
    logging: LoggingConfig
    debug: DebugConfig


def load(config_path: Path | None = None, log_level: LogLevel = LogLevel.NOTSET) -> ServerConfig:
    # Determine where to read configuration.
    raw_cfg, _ = config.read_from_file(config_path, "wsproxy")

    config.override_key(raw_cfg, ("debug", "enabled"), log_level == LogLevel.DEBUG)
    if log_level != LogLevel.NOTSET:
        config.override_key(raw_cfg, ("logging", "level"), log_level)
        config.override_key(raw_cfg, ("logging", "pkg-ns", "ai.backend"), log_level)
        config.override_key(raw_cfg, ("logging", "pkg-ns", "aiohttp"), log_level)

    # Validate and fill configurations
    # (allow_extra will make configs to be forward-copmatible)
    try:
        cfg = ServerConfig(**raw_cfg)
        if cfg.debug.enabled:
            print("== WSProxy configuration ==", file=sys.stderr)
            print(pformat(cfg.model_dump()), file=sys.stderr)
    except ValidationError as e:
        print(
            "ConfigurationError: Could not read or validate the manager local config:",
            file=sys.stderr,
        )
        print(pformat(e), file=sys.stderr)
        raise click.Abort()
    else:
        return cfg


class Undefined:
    pass


class UnsupportedTypeError(RuntimeError):
    pass


def generate_example_json(
    schema: type[BaseSchema] | types.GenericAlias | types.UnionType, parent: list[str] = []
) -> dict | list:
    if isinstance(schema, types.UnionType):
        return generate_example_json(typing.get_args(schema)[0], parent=[*parent])
    elif isinstance(schema, types.GenericAlias):
        if typing.get_origin(schema) is not list:
            raise RuntimeError("GenericAlias other than list not supported!")
        return [generate_example_json(typing.get_args(schema)[0], parent=[*parent])]
    elif issubclass(schema, BaseSchema):
        res = {}
        for name, info in schema.model_fields.items():
            config_key = [*parent, name]
            assert info.annotation
            alternative_example = Undefined
            if info.examples:
                res[name] = info.examples[0]
            elif info.default != PydanticUndefined:
                alternative_example = info.default
            if name not in res:
                try:
                    res[name] = generate_example_json(info.annotation, parent=config_key)
                except RuntimeError:
                    if alternative_example != Undefined:
                        res[name] = alternative_example
                    else:
                        raise
        return res
    else:
        raise UnsupportedTypeError(str(schema))
