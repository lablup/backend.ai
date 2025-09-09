import os
from dataclasses import dataclass
from pathlib import Path
from typing import override

from ai.backend.common.msgpack import DEFAULT_PACK_OPTS, DEFAULT_UNPACK_OPTS
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.logging.config import LoggingConfig
from ai.backend.logging.logger import Logger


@dataclass
class LoggerSpec:
    is_master: bool
    ipc_base_path: Path
    config: LoggingConfig


class LoggerSpecGenerator(ArgsSpecGenerator[LoggerSpec]):
    pass


@dataclass
class LoggerResult:
    logger: Logger
    log_endpoint: str


class LoggerProvisioner(Provisioner[LoggerSpec, LoggerResult]):
    @property
    @override
    def name(self) -> str:
        return "storage-worker-logger"

    @override
    async def setup(self, spec: LoggerSpec) -> LoggerResult:
        log_sockpath = Path(
            spec.ipc_base_path / f"storage-proxy-logger-{os.getpid()}.sock",
        )
        log_sockpath.parent.mkdir(parents=True, exist_ok=True)
        log_endpoint = f"ipc://{log_sockpath}"
        logger = Logger(
            spec.config,
            is_master=spec.is_master,
            log_endpoint=log_endpoint,
            msgpack_options={
                "pack_opts": DEFAULT_PACK_OPTS,
                "unpack_opts": DEFAULT_UNPACK_OPTS,
            },
        )
        logger.__enter__()
        return LoggerResult(logger, log_endpoint)

    @override
    async def teardown(self, resource: LoggerResult) -> None:
        resource.logger.__exit__()


class LoggerStage(ProvisionStage[LoggerSpec, LoggerResult]):
    pass
