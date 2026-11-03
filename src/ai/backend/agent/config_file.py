import functools
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, override

from ai.backend.agent.resources import ComputerContext, KernelResourceSpec
from ai.backend.common.asyncio import run_in_executor_with_context
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import DeviceName


@dataclass(frozen=True)
class BaseKernelConfigFile(ABC):
    """A file a kernel reads from its config directory."""

    path: Path
    encoding: str | None = field(default=None, kw_only=True)

    @abstractmethod
    async def render(self) -> str:
        raise NotImplementedError

    async def write(self) -> None:
        content = await self.render()
        await run_in_executor_with_context(
            None, functools.partial(self.path.write_text, content, encoding=self.encoding)
        )


@dataclass(frozen=True)
class EnvironFile(BaseKernelConfigFile):
    environ: Mapping[str, str]
    extra_lines: Sequence[str] = ()

    @override
    async def render(self) -> str:
        lines = [f"{k}={v}\n" for k, v in self.environ.items()]
        lines += [f"{line}\n" for line in self.extra_lines]
        return "".join(lines)


@dataclass(frozen=True)
class SessionNameFile(BaseKernelConfigFile):
    session_name: str

    @override
    async def render(self) -> str:
        return self.session_name


@dataclass(frozen=True)
class DockerCredsFile(BaseKernelConfigFile):
    docker_creds: Mapping[str, Any]

    @override
    async def render(self) -> str:
        return dump_json_str(self.docker_creds)


@dataclass(frozen=True)
class ResourceFile(BaseKernelConfigFile):
    resource_spec: KernelResourceSpec
    computers: Mapping[DeviceName, ComputerContext]

    @override
    async def render(self) -> str:
        lines = [self.resource_spec.write_to_string()]
        for dev_type, device_alloc in self.resource_spec.allocations.items():
            device_plugin = self.computers[dev_type].instance
            kvpairs = await device_plugin.generate_resource_data(device_alloc)
            lines += [f"{k}={v}\n" for k, v in kvpairs.items()]
        return "".join(lines)
