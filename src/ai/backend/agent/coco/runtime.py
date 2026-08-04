import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.json import load_json
from ai.backend.logging import BraceStyleAdapter

from .errors import ImageDigestUnresolved, RuntimeInvocationFailed
from .spec import ContainerSpec

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class RuntimeConfig:
    binary: str
    address: str
    namespace: str


class AbstractRuntimeClient(ABC):
    @abstractmethod
    async def resolve_image(self, canonical: str, supplied_digest: str) -> str: ...

    @abstractmethod
    async def create(self, spec: ContainerSpec) -> str: ...

    @abstractmethod
    async def start(self, container_id: str) -> None: ...

    @abstractmethod
    async def wait_running(self, container_id: str, limit_seconds: float) -> None: ...

    @abstractmethod
    async def kill(self, container_id: str, signal: str) -> None: ...

    @abstractmethod
    async def delete(self, container_id: str, force: bool) -> None: ...

    @abstractmethod
    async def inspect(self, container_ids: Sequence[str]) -> Sequence[Mapping[str, Any]]: ...

    @abstractmethod
    async def list_ids(self, labels: Mapping[str, str]) -> Sequence[str]: ...


class NerdctlClient(AbstractRuntimeClient):
    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config

    async def _run(self, *args: str, check: bool = True) -> str:
        argv = (
            self._config.binary,
            "--address",
            self._config.address,
            "--namespace",
            self._config.namespace,
            *args,
        )
        proc = await asyncio.create_subprocess_exec(
            *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if check and proc.returncode != 0:
            raise RuntimeInvocationFailed(
                extra_msg=f"{' '.join(argv)} exited {proc.returncode}: {stderr.decode().strip()}"
            )
        return stdout.decode()

    @override
    async def resolve_image(self, canonical: str, supplied_digest: str) -> str:
        if not supplied_digest:
            raise ImageDigestUnresolved(extra_msg=canonical)
        return supplied_digest

    @override
    async def create(self, spec: ContainerSpec) -> str:
        out = await self._run("create", *spec.to_args())
        container_id = out.strip().splitlines()[-1].strip()
        if not container_id:
            raise RuntimeInvocationFailed(extra_msg=f"create returned no id for {spec.name}")
        return container_id

    @override
    async def start(self, container_id: str) -> None:
        await self._run("start", container_id)

    @override
    async def wait_running(self, container_id: str, limit_seconds: float) -> None:
        deadline = asyncio.get_running_loop().time() + limit_seconds
        while True:
            entries = await self.inspect([container_id])
            status = ""
            if entries:
                status = str(entries[0].get("State", {}).get("Status", ""))
            if status == "running":
                return
            if status in ("exited", "dead"):
                raise RuntimeInvocationFailed(
                    extra_msg=f"container {container_id[:12]} reached status {status}"
                )
            if asyncio.get_running_loop().time() >= deadline:
                raise RuntimeInvocationFailed(
                    extra_msg=(
                        f"container {container_id[:12]} did not reach running within"
                        f" {limit_seconds} seconds (last status {status or 'unknown'})"
                    )
                )
            await asyncio.sleep(0.5)

    @override
    async def kill(self, container_id: str, signal: str) -> None:
        await self._run("kill", "--signal", signal, container_id, check=False)

    @override
    async def delete(self, container_id: str, force: bool) -> None:
        args = ["rm", "--volumes"]
        if force:
            args.append("--force")
        await self._run(*args, container_id, check=False)

    @override
    async def inspect(self, container_ids: Sequence[str]) -> Sequence[Mapping[str, Any]]:
        if not container_ids:
            return []
        out = await self._run("inspect", "--mode", "dockercompat", *container_ids, check=False)
        if not out.strip():
            return []
        try:
            parsed = load_json(out)
        except ValueError:
            return []
        return parsed if isinstance(parsed, list) else [parsed]

    @override
    async def list_ids(self, labels: Mapping[str, str]) -> Sequence[str]:
        args = ["ps", "--all", "--quiet", "--no-trunc"]
        for key, value in labels.items():
            args += ["--filter", f"label={key}={value}"]
        out = await self._run(*args, check=False)
        return [line.strip() for line in out.splitlines() if line.strip()]
