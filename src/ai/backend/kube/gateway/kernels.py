"""Kernel-level operations of the Agent RPC contract, carried out on session Pods."""

from __future__ import annotations

import asyncio
import logging
import textwrap
import time
from collections.abc import Mapping, Sequence
from typing import Any, Final, Literal, override
from uuid import UUID

from kubernetes_asyncio import client

from ai.backend.agent.errors.agent import KernelNotFoundError
from ai.backend.agent.kernel import RUN_ID_FOR_BATCH_JOB, AbstractCodeRunner, NextResult
from ai.backend.common.dto.agent.response import CodeCompletionResp
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.image.anycast import ImagePullFinishedEvent
from ai.backend.common.events.event_types.kernel.anycast import KernelTerminatedAnycastEvent
from ai.backend.common.events.event_types.kernel.broadcast import KernelTerminatedBroadcastEvent
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.events.event_types.session.anycast import (
    ExecutionFinishedAnycastEvent,
    ExecutionStartedAnycastEvent,
    ExecutionTimeoutAnycastEvent,
    SessionFailureAnycastEvent,
    SessionSuccessAnycastEvent,
)
from ai.backend.common.events.event_types.session.broadcast import (
    SessionFailureBroadcastEvent,
    SessionSuccessBroadcastEvent,
)
from ai.backend.common.types import AgentId, KernelId, SessionId
from ai.backend.kube.controller.manifests import kernel_service_ports
from ai.backend.kube.controller.naming import KERNEL_CONTAINER
from ai.backend.kube.crd.base import CRD_VERSION
from ai.backend.kube.crd.session import ServicePortSpec, SessionWorkload
from ai.backend.kube.gateway.kernel_index import KernelEndpoint, KernelIndex
from ai.backend.kube.gateway.pod_exec import exec_in_pod
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

KERNEL_HOME: Final = "/home/work"
KERNEL_PYTHON: Final = "/opt/backend.ai/bin/python"
SU_EXEC: Final = "/opt/kernel/su-exec"
MAX_DOWNLOAD_BYTES: Final = 1024 * 1024

# Each script confines the path to the kernel home and prints a JSON result or the payload.
_UPLOAD_SCRIPT: Final = textwrap.dedent("""
    import os, sys
    home = os.path.realpath(sys.argv[1])
    target = os.path.realpath(os.path.join(home, sys.argv[2]))
    if os.path.commonpath([home, target]) != home:
        sys.exit("not allowed to upload files outside " + home)
    data = sys.stdin.buffer.read(int(sys.argv[3]))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as f:
        f.write(data)
""")
_DOWNLOAD_SCRIPT: Final = textwrap.dedent("""
    import io, os, sys, tarfile
    home = os.path.realpath(sys.argv[1])
    target = os.path.realpath(os.path.join(home, sys.argv[2]))
    if os.path.commonpath([home, target]) != home:
        sys.exit("not allowed to download files outside " + home)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        tar.add(target, arcname=os.path.basename(target))
    if buf.tell() > int(sys.argv[3]):
        sys.exit("too large archive file exceeding the limit")
    if sys.argv[4] == "single":
        buf.seek(0)
        with tarfile.open(fileobj=buf) as tar:
            names = tar.getnames()
            if len(names) != 1:
                sys.exit("expected a single file")
            sys.stdout.buffer.write(tar.extractfile(names[0]).read())
    else:
        sys.stdout.buffer.write(buf.getvalue())
""")
_LIST_SCRIPT: Final = textwrap.dedent("""
    import json, os, stat, sys
    home = os.path.realpath(sys.argv[1])
    target = os.path.realpath(os.path.join(home, sys.argv[2]))
    if os.path.commonpath([home, target]) != home:
        sys.exit("not allowed to list files outside " + home)
    files = []
    for f in os.scandir(target):
        st = f.stat(follow_symlinks=False)
        files.append({
            "mode": stat.filemode(st.st_mode), "size": st.st_size,
            "ctime": st.st_ctime, "mtime": st.st_mtime, "atime": st.st_atime,
            "filename": f.name,
        })
    print(json.dumps(files))
""")


class PodCodeRunner(AbstractCodeRunner):
    """Talks to the kernel runner's REPL sockets on the Pod IP."""

    pod_ip: str

    def __init__(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        event_producer: EventProducer,
        *,
        pod_ip: str,
        client_features: frozenset[str] | None = None,
    ) -> None:
        super().__init__(
            kernel_id, session_id, event_producer, exec_timeout=0, client_features=client_features
        )
        self.pod_ip = pod_ip

    @override
    async def get_repl_in_addr(self) -> str:
        return f"tcp://{self.pod_ip}:2000"

    @override
    async def get_repl_out_addr(self) -> str:
        return f"tcp://{self.pod_ip}:2001"


class GatewayKernels:
    _index: KernelIndex
    _core: client.CoreV1Api
    _exec_core: client.CoreV1Api
    _custom: client.CustomObjectsApi
    _event_producer: EventProducer
    _runners: dict[str, tuple[str, PodCodeRunner]]  # kernel id → (pod uid, runner)
    _runner_lock: asyncio.Lock
    _batch_tasks: set[asyncio.Task[None]]

    def __init__(
        self,
        index: KernelIndex,
        api: client.ApiClient,
        ws_api: client.ApiClient,
        event_producer: EventProducer,
    ) -> None:
        self._index = index
        self._core = client.CoreV1Api(api)
        self._exec_core = client.CoreV1Api(ws_api)
        self._custom = client.CustomObjectsApi(api)
        self._event_producer = event_producer
        self._runners = {}
        self._runner_lock = asyncio.Lock()
        self._batch_tasks = set()

    async def close(self) -> None:
        for task in self._batch_tasks:
            task.cancel()
        for _, runner in self._runners.values():
            await runner.close()

    def _endpoint(self, kernel_id: str) -> KernelEndpoint:
        endpoint = self._index.get(kernel_id)
        if endpoint is None or endpoint.pod_ip is None:
            raise KernelNotFoundError(
                f"The Pod of kernel {kernel_id} is not found (it might be terminated)."
            )
        return endpoint

    async def _runner(self, kernel_id: str) -> PodCodeRunner:
        endpoint = self._endpoint(kernel_id)
        async with self._runner_lock:
            cached = self._runners.get(kernel_id)
            if cached is not None and cached[0] == endpoint.pod_uid:
                return cached[1]
            if cached is not None:
                await cached[1].close()
            runner = await PodCodeRunner.new(
                KernelId(UUID(kernel_id)),
                SessionId(UUID(endpoint.session_id)),
                self._event_producer,
                pod_ip=endpoint.pod_ip,
            )
            self._runners[kernel_id] = (endpoint.pod_uid, runner)
            return runner

    async def forget(self, kernel_id: str) -> None:
        async with self._runner_lock:
            cached = self._runners.pop(kernel_id, None)
        if cached is not None:
            await cached[1].close()

    async def execute(
        self,
        session_id: SessionId,
        kernel_id: str,
        run_id: str | None,
        mode: Literal["query", "batch", "input", "continue"],
        text: str,
        *,
        opts: Mapping[str, Any],
        api_version: int,
        flush_timeout: float,
    ) -> dict[str, Any]:
        await self._event_producer.anycast_event(
            ExecutionStartedAnycastEvent(session_id=session_id)
        )
        runner = await self._runner(kernel_id)
        await runner.attach_output_queue(run_id)
        try:
            match mode:
                case "batch":
                    await runner.feed_batch(opts)
                case "query":
                    await runner.feed_code(text)
                case "input":
                    await runner.feed_input(text)
                case "continue":
                    pass
            result: NextResult = await runner.get_next_result(
                api_ver=api_version, flush_timeout=flush_timeout
            )
        except asyncio.CancelledError:
            await self.forget(kernel_id)
            raise
        if result["status"] == "finished":
            await self._event_producer.anycast_event(
                ExecutionFinishedAnycastEvent(session_id=session_id)
            )
        elif result["status"] == "exec-timeout":
            await self._event_producer.anycast_event(
                ExecutionTimeoutAnycastEvent(session_id=session_id)
            )
        return {**result, "files": []}

    def start_batch(
        self, session_id: SessionId, kernel_id: str, command: str, timeout_seconds: float | None
    ) -> None:
        task = asyncio.create_task(self._run_batch(session_id, kernel_id, command, timeout_seconds))
        self._batch_tasks.add(task)
        task.add_done_callback(self._batch_tasks.discard)

    async def _run_batch(
        self, session_id: SessionId, kernel_id: str, command: str, timeout_seconds: float | None
    ) -> None:
        mode: Literal["batch", "continue"] = "batch"
        opts: dict[str, Any] = {"exec": command}
        try:
            async with asyncio.timeout(timeout_seconds):
                while True:
                    try:
                        result = await self.execute(
                            session_id,
                            kernel_id,
                            RUN_ID_FOR_BATCH_JOB,
                            mode,
                            "",
                            opts=opts,
                            flush_timeout=1.0,
                            api_version=3,
                        )
                    except KernelNotFoundError:
                        await self._kernel_self_terminated(session_id, kernel_id)
                        return
                    if result["status"] == "finished":
                        await self._batch_ended(session_id, result["exitCode"])
                        return
                    if result["status"] == "exec-timeout":
                        await self._batch_ended(session_id, -2, timed_out=True)
                        return
                    mode, opts = "continue", {"exec": ""}
        except TimeoutError:
            await self._batch_ended(session_id, -2, timed_out=True)

    async def _batch_ended(
        self, session_id: SessionId, exit_code: int, *, timed_out: bool = False
    ) -> None:
        if exit_code == 0:
            reason = KernelLifecycleEventReason.TASK_FINISHED
            await self._event_producer.anycast_and_broadcast_event(
                SessionSuccessAnycastEvent(session_id=session_id, reason=reason, exit_code=0),
                SessionSuccessBroadcastEvent(session_id=session_id, reason=reason, exit_code=0),
            )
            return
        reason = (
            KernelLifecycleEventReason.TASK_TIMEOUT
            if timed_out
            else KernelLifecycleEventReason.TASK_FAILED
        )
        await self._event_producer.anycast_and_broadcast_event(
            SessionFailureAnycastEvent(session_id=session_id, reason=reason, exit_code=exit_code),
            SessionFailureBroadcastEvent(session_id=session_id, reason=reason, exit_code=exit_code),
        )

    async def _kernel_self_terminated(self, session_id: SessionId, kernel_id: str) -> None:
        reason = KernelLifecycleEventReason.SELF_TERMINATED
        kid = KernelId(UUID(kernel_id))
        await self._event_producer.anycast_and_broadcast_event(
            KernelTerminatedAnycastEvent(kernel_id=kid, session_id=session_id, reason=reason),
            KernelTerminatedBroadcastEvent(kernel_id=kid, session_id=session_id, reason=reason),
        )

    async def interrupt(self, kernel_id: str) -> dict[str, Any]:
        await (await self._runner(kernel_id)).feed_interrupt()
        return {"status": "finished"}

    async def get_completions(
        self, kernel_id: str, text: str, opts: Mapping[str, Any]
    ) -> CodeCompletionResp:
        result = await (await self._runner(kernel_id)).feed_and_get_completion(text, opts)
        return CodeCompletionResp(result=result)

    async def _service_ports(self, endpoint: KernelEndpoint) -> list[ServicePortSpec]:
        if endpoint.workload_name is None:
            return []
        raw = await self._custom.get_namespaced_custom_object(
            SessionWorkload.crd.group,
            CRD_VERSION,
            endpoint.namespace,
            SessionWorkload.crd.plural,
            endpoint.workload_name,
        )
        workload = SessionWorkload.model_validate(raw)
        for kernel in workload.spec.kernels:
            if kernel.kernel_id == endpoint.kernel_id:
                return kernel_service_ports(kernel)
        return []

    async def start_service(
        self, kernel_id: str, service: str, opts: Mapping[str, Any]
    ) -> dict[str, Any]:
        endpoint = self._endpoint(kernel_id)
        sport = next((p for p in await self._service_ports(endpoint) if p.name == service), None)
        if sport is None:
            return {"status": "failed", "error": "invalid service name"}
        return await (await self._runner(kernel_id)).feed_start_service({
            "name": service,
            "port": sport.container_ports[0],
            "ports": sport.container_ports,
            "protocol": sport.protocol,
            "options": opts,
        })

    async def shutdown_service(self, kernel_id: str, service: str) -> None:
        if self._index.get(kernel_id) is None:
            log.trace("service app shutdown skipped, kernel not found", service_name=service)
            return
        await (await self._runner(kernel_id)).feed_shutdown_service(service)

    def _as_kernel_user(self, endpoint: KernelEndpoint, command: list[str]) -> list[str]:
        if endpoint.uid is None:
            return command
        return [SU_EXEC, f"{endpoint.uid}:{endpoint.gid or endpoint.uid}", *command]

    async def _run_script(
        self, endpoint: KernelEndpoint, script: str, args: list[str], stdin: bytes | None = None
    ) -> bytes:
        command = self._as_kernel_user(
            endpoint, [KERNEL_PYTHON, "-s", "-c", script, KERNEL_HOME, *args]
        )
        result = await exec_in_pod(
            self._exec_core,
            endpoint.namespace,
            endpoint.pod_name,
            KERNEL_CONTAINER,
            command,
            stdin,
        )
        if result.exit_code != 0:
            raise PermissionError(result.stderr.decode("utf-8", "replace").strip())
        return result.stdout

    async def upload_file(self, kernel_id: str, filename: str, payload: bytes) -> None:
        endpoint = self._endpoint(kernel_id)
        await self._run_script(endpoint, _UPLOAD_SCRIPT, [filename, str(len(payload))], payload)

    async def download_file(self, kernel_id: str, filepath: str) -> bytes:
        endpoint = self._endpoint(kernel_id)
        return await self._run_script(
            endpoint, _DOWNLOAD_SCRIPT, [filepath, str(MAX_DOWNLOAD_BYTES), "archive"]
        )

    async def download_single(self, kernel_id: str, filepath: str) -> bytes:
        endpoint = self._endpoint(kernel_id)
        return await self._run_script(
            endpoint, _DOWNLOAD_SCRIPT, [filepath, str(MAX_DOWNLOAD_BYTES), "single"]
        )

    async def list_files(self, kernel_id: str, path: str) -> dict[str, Any]:
        endpoint = self._endpoint(kernel_id)
        out = await self._run_script(endpoint, _LIST_SCRIPT, [path])
        return {"files": out.decode("utf-8"), "errors": "", "abspath": path}

    async def images_ready(self, gateway_id: str, canonicals: Sequence[str]) -> None:
        """The kubelet pulls a session's image when its Pod starts, so each one is ready now.

        A failed pull ends the kernel later with `FAILED_TO_START`.
        """
        for canonical in canonicals:
            await self._event_producer.anycast_event(
                ImagePullFinishedEvent(
                    image=canonical,
                    agent_id=AgentId(gateway_id),
                    timestamp=time.time(),
                    msg="pulled by the kubelet when the Pod starts",
                )
            )

    def is_running(self, kernel_id: str) -> bool:
        endpoint = self._index.get(kernel_id)
        return endpoint is not None and endpoint.pod_phase == "Running"

    async def get_logs(self, kernel_id: str) -> dict[str, Any]:
        endpoint = self._endpoint(kernel_id)
        logs = await self._core.read_namespaced_pod_log(
            endpoint.pod_name, endpoint.namespace, container=KERNEL_CONTAINER
        )
        return {"logs": logs}
