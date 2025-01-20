import enum
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

from .types import EventLoopType
from .utils import config_key_to_snake_case

_file_perm = (Path(__file__).parent / "server.py").stat()
_default_num_worker = 1
_default_db_pool_size = 8
_default_pool_recycle = -1
_default_max_overflow = 64


class DBType(enum.StrEnum):
    POSTGRESQL = "postgresql"


class TransactionIsolationLevel(enum.StrEnum):
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
        extra="allow",
    )


class HostPortPair(BaseSchema):
    host: Annotated[str, Field(examples=["127.0.0.1"])]
    port: Annotated[int, Field(gt=0, lt=65536, examples=[8201])]

    def __repr__(self) -> str:
        return f"{self.host}:{self.port}"

    def __str__(self) -> str:
        return self.__repr__()

    def __getitem__(self, *args) -> int | str:
        if args[0] == 0:
            return self.host
        elif args[0] == 1:
            return self.port
        else:
            raise KeyError(*args)


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


class EtcdConfig(BaseSchema):
    namespace: Annotated[str, Field(description="etcd namespace.")]
    addr: Annotated[
        HostPortPair,
        Field(
            description="Address to access the etcd.",
            examples=[HostPortPair(host="127.0.0.1", port=8121)],
        ),
    ]
    user: Annotated[str, Field(description="etcd user.")]
    password: Annotated[str, Field(description="etcd password.")]


class DBConfig(BaseSchema):
    type: Annotated[
        DBType,
        Field(
            description=f"DB type. One of {[_type.value for _type in DBType]}. Default is 'postgresql'.",
            default=DBType.POSTGRESQL,
        ),
    ]
    transaction_isolation: Annotated[
        TransactionIsolationLevel,
        Field(
            description=f"Transaction isolation level. One of {[val.value for val in TransactionIsolationLevel]}. Default is 'SERIALIZABLE'.",
            default=TransactionIsolationLevel.SERIALIZABLE,
        ),
    ]
    addr: Annotated[
        HostPortPair,
        Field(
            description="Address to access the database.",
            examples=[HostPortPair(host="127.0.0.1", port=8001)],
        ),
    ]
    name: Annotated[str, Field(description="Database name.")]

    user: Annotated[str, Field(description="Database account user.")]
    password: Annotated[str, Field(description="Database account password.")]

    pool_size: Annotated[
        int,
        Field(
            description=f"The connection pool's initial size. Default is {_default_db_pool_size}.",
            default=_default_db_pool_size,
        ),
    ]
    pool_recycle: Annotated[
        int,
        Field(
            description=f"This setting causes the pool to recycle connections after the given number of seconds has passed. Default is {_default_pool_recycle}, which means infinite.",
            default=_default_pool_recycle,
        ),
    ]
    pool_pre_ping: Annotated[
        bool,
        Field(
            description="This setting eliminates DB error due to stale pooled connections by ping at the start of each connection pool checkout. Default is 'false'.",
            default=False,
        ),
    ]
    max_overflow: Annotated[
        int,
        Field(
            description=f"The maximum allowed overflow of the connection pool. Default is {_default_max_overflow}.",
            default=_default_max_overflow,
        ),
    ]


class AccountManagerConfig(BaseSchema):
    service_addr: Annotated[
        HostPortPair,
        Field(
            description="Address of account-manager service.",
            examples=[HostPortPair(host="127.0.0.1", port=8099)],
        ),
    ]
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
            examples=["/tmp/backend.ai/account_manager.pid"],
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
    ssl_enabled: Annotated[
        bool, Field(description="Use TLS to communicate. Default is false.", default=False)
    ]
    ssl_cert: Annotated[
        Path | None, Field(description="SSL Certificate file path. Default is null.", default=None)
    ]
    ssl_privkey: Annotated[
        Path | None, Field(description="SSL Private key file path. Default is null.", default=False)
    ]
    num_workers: Annotated[
        int,
        Field(
            description=f"Number of forked workers. Default is {_default_num_worker}.",
            default=_default_num_worker,
        ),
    ]
    allowed_plugins: Annotated[
        list[str] | None,
        Field(description="Plugins to allow. Default is null, which skips allowing.", default=None),
    ]
    disabled_plugins: Annotated[
        list[str] | None,
        Field(description="Plugins to block. Default is null, which skips blocking.", default=None),
    ]

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


class PyroscopeConfig(BaseSchema):
    enabled: Annotated[bool, Field(default=False, description="Enable pyroscope profiler.")]
    app_name: Annotated[str, Field(default=None, description="Pyroscope app name.")]
    server_addr: Annotated[str, Field(default=None, description="Pyroscope server address.")]
    sample_rate: Annotated[int, Field(default=None, description="Pyroscope sample rate.")]


class DebugConfig(BaseSchema):
    enabled: Annotated[bool, Field(default=False)]
    asyncio: Annotated[bool, Field(default=False)]
    enhanced_aiomonitor_task_info: Annotated[bool, Field(default=False)]
    log_events: Annotated[bool, Field(default=False)]


class ServerConfig(BaseSchema):
    etcd: EtcdConfig
    db: DBConfig
    account_manager: AccountManagerConfig
    pyroscope: Annotated[PyroscopeConfig, Field(default_factory=PyroscopeConfig)]
    debug: DebugConfig
    # logging


def load(config_path: Path | None = None, log_level: str = "INFO") -> ServerConfig:
    # Determine where to read configuration.
    raw_cfg, _ = config.read_from_file(config_path, "account-manager")

    config.override_key(raw_cfg, ("debug", "enabled"), log_level == "DEBUG")
    config.override_key(raw_cfg, ("logging", "level"), log_level.upper())
    config.override_key(raw_cfg, ("logging", "pkg-ns", "ai.backend"), log_level.upper())
    config.override_key(raw_cfg, ("logging", "pkg-ns", "aiohttp"), log_level.upper())

    # Validate and fill configurations
    # (allow_extra will make configs to be forward-copmatible)
    try:
        raw_cfg = config_key_to_snake_case(raw_cfg)
        cfg = ServerConfig(**raw_cfg)
        if cfg.debug.enabled:
            print("== Account Manager configuration ==", file=sys.stderr)
            print(pformat(cfg.model_dump()), file=sys.stderr)
    except ValidationError as e:
        print(
            "ConfigurationError: Could not read or validate the account manager local config:",
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
