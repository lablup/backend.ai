from __future__ import annotations

import asyncio
import codecs
import io
import json
import logging
import math
import secrets
import time
from abc import ABCMeta
from collections import OrderedDict
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, Literal, NotRequired, TypedDict, cast, override

from async_timeout import timeout

from ai.backend.common import msgpack
from ai.backend.common.asyncio import cancel_task, current_loop
from ai.backend.common.dto.agent.response import CodeCompletionResult
from ai.backend.common.enum_extension import StringSetFlag
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.json import load_json
from ai.backend.common.types import KernelId, SessionId, aobject
from ai.backend.logging import BraceStyleAdapter

from .errors import (
    ChannelNotEstablished,
    InvalidSocket,
    OutputQueueMismatchError,
    OutputQueueNotInitializedError,
    RunIdNotSetError,
    StaleAnswerRefused,
)
from .transport import RunnerTransport, ZeroMQTransport
from .vocabulary import RunnerReply, RunnerVerb

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

REDIAL_STALL_LIMIT: Final = 30
REDIAL_BACKOFF: Final = 1.0


# msg types visible to the API client.
# (excluding control signals such as 'finished' and 'waiting-input'
# since they are passed as separate status field.)
ConsoleItemType = Literal[
    "stdout",
    "stderr",
    "media",
    "html",
    "log",
    "completion",
]
outgoing_msg_types: frozenset[ConsoleItemType] = frozenset([
    "stdout",
    "stderr",
    "media",
    "html",
    "log",
    "completion",
])
ResultType = (
    ConsoleItemType
    | Literal[
        "continued",
        "clean-finished",
        "build-finished",
        "finished",
        "exec-timeout",
        "waiting-input",
    ]
)


class ClientFeatures(StringSetFlag):
    INPUT = "input"
    CONTINUATION = "continuation"


# TODO: use Python 3.7 contextvars for per-client feature selection
default_client_features = frozenset({
    ClientFeatures.INPUT.value,
    ClientFeatures.CONTINUATION.value,
})
default_api_version = 4
RUN_ID_FOR_BATCH_JOB = "batch-job"  # TODO: Deprecate usage of run-id


def _dump_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj).encode("utf-8")


class RunEvent(Exception):
    data: Any

    def __init__(self, data: Any = None) -> None:
        super().__init__()
        self.data = data


class InputRequestPending(RunEvent):
    pass


class CleanFinished(RunEvent):
    pass


class BuildFinished(RunEvent):
    pass


class RunFinished(RunEvent):
    pass


class ExecTimeout(RunEvent):
    pass


@dataclass
class ResultRecord:
    msg_type: ResultType
    data: str | None = None


class NextResult(TypedDict):
    runId: str | None
    status: ResultType
    exitCode: int | None
    options: Mapping[str, Any] | None
    # v1
    stdout: NotRequired[str | None]
    stderr: NotRequired[str | None]
    media: NotRequired[Sequence[Any]]
    html: NotRequired[Sequence[Any]]
    # v2
    console: NotRequired[Sequence[Any]]


class AbstractCodeRunner(aobject, metaclass=ABCMeta):
    kernel_id: KernelId
    session_id: SessionId
    started_at: float
    finished_at: float | None
    exec_timeout: float
    max_record_size: int
    client_features: frozenset[str]

    event_producer: EventProducer

    _transport: RunnerTransport | None

    completion_queue: asyncio.Queue[bytes]
    service_queue: asyncio.Queue[bytes]
    model_service_queue: asyncio.Queue[bytes]
    service_apps_info_queue: asyncio.Queue[bytes]
    status_queue: asyncio.Queue[bytes]
    transfer_queue: asyncio.Queue[bytes]
    _is_socket_invalid: bool
    output_queue: asyncio.Queue[ResultRecord] | None
    current_run_id: str | None
    pending_queues: OrderedDict[str, tuple[asyncio.Event, asyncio.Queue[ResultRecord]]]

    read_task: asyncio.Task[Any] | None
    status_task: asyncio.Task[Any] | None
    watchdog_task: asyncio.Task[Any] | None

    _closed: bool

    def __init__(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        event_producer: EventProducer,
        *,
        exec_timeout: float = 0,
        client_features: frozenset[str] | None = None,
    ) -> None:
        self.kernel_id = kernel_id
        self.session_id = session_id
        self.event_producer = event_producer
        self.started_at = time.monotonic()
        self.finished_at = None
        if not math.isfinite(exec_timeout) or exec_timeout < 0:
            raise ValueError("execution timeout must be a zero or finite positive number.")
        self.exec_timeout = exec_timeout
        self.max_record_size = 10 * (2**20)  # 10 MBytes
        self.client_features = client_features or frozenset()
        self._transport = None
        self._is_socket_invalid = False
        self.completion_queue = asyncio.Queue(maxsize=128)
        self.service_queue = asyncio.Queue(maxsize=128)
        self.model_service_queue = asyncio.Queue(maxsize=128)
        self.service_apps_info_queue = asyncio.Queue(maxsize=128)
        self.status_queue = asyncio.Queue(maxsize=128)
        self.transfer_queue = asyncio.Queue(maxsize=128)
        self.output_queue = None
        self.pending_queues = OrderedDict()
        self.current_run_id = None
        self.read_task = None
        self.status_task = None
        self.watchdog_task = None
        self._closed = False

    @override
    async def __ainit__(self) -> None:
        await self._get_transport()
        await self._create_tasks()

    async def _create_transport(self) -> RunnerTransport:
        return ZeroMQTransport(await self.get_repl_in_addr(), await self.get_repl_out_addr())

    async def _get_transport(self) -> RunnerTransport:
        if self._transport is None:
            self._transport = await self._create_transport()
        return self._transport

    async def refresh_sockets(self) -> None:
        if self.read_task is not None:
            self.read_task.cancel()
        self._transport = await self._create_transport()
        loop = current_loop()
        self.read_task = loop.create_task(self.read_output())

    @override
    def __getstate__(self) -> Mapping[str, Any]:
        props = self.__dict__.copy()
        del props["_transport"]
        del props["_is_socket_invalid"]
        del props["completion_queue"]
        del props["service_queue"]
        del props["model_service_queue"]
        del props["service_apps_info_queue"]
        del props["status_queue"]
        del props["transfer_queue"]
        del props["output_queue"]
        del props["pending_queues"]
        del props["read_task"]
        del props["status_task"]
        del props["watchdog_task"]
        del props["_closed"]
        del props["event_producer"]
        return props

    def __setstate__(self, props: MutableMapping[str, Any]) -> None:
        self.__dict__.update(props)
        self._transport = None
        self._is_socket_invalid = False
        self.completion_queue = asyncio.Queue(maxsize=128)
        self.service_queue = asyncio.Queue(maxsize=128)
        self.model_service_queue = asyncio.Queue(maxsize=128)
        self.service_apps_info_queue = asyncio.Queue(maxsize=128)
        self.status_queue = asyncio.Queue(maxsize=128)
        self.output_queue = None
        self.pending_queues = OrderedDict()
        self.read_task = None
        self.status_task = None
        self.watchdog_task = None
        self._closed = False
        # __ainit__() is called by the caller.

    async def get_repl_in_addr(self) -> str:
        raise NotImplementedError

    async def get_repl_out_addr(self) -> str:
        raise NotImplementedError

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            await self._close_tasks()
            if self._transport is not None:
                self._transport.close()
        except Exception:
            log.exception("AbstractCodeRunner.close(): unexpected error")

    async def _create_tasks(self) -> None:
        # close the previous task if any
        await self._close_tasks()

        loop = asyncio.get_running_loop()
        self.status_task = loop.create_task(self.ping_status())
        self.read_task = loop.create_task(self.read_output())
        if self.exec_timeout > 0:
            self.watchdog_task = loop.create_task(self.watchdog())

    async def _close_tasks(self) -> None:
        concurrent_safe_tasks: tuple[asyncio.Task[Any] | None, ...] = (
            self.status_task,
            self.read_task,
            self.watchdog_task,
        )
        await asyncio.gather(
            *[cancel_task(task) for task in concurrent_safe_tasks if task is not None],
            return_exceptions=True,
        )

    async def ping(self) -> dict[str, float] | None:
        try:
            return await self.feed_and_get_status()
        except Exception:
            log.exception("AbstractCodeRunner.ping(): unexpected error")
            return None

    async def ping_status(self) -> None:
        """
        This is to keep the REPL in/out port mapping in the Linux
        kernel's NAT table alive.
        """
        try:
            while True:
                ret = await self.feed_and_get_status()
                if ret is None:
                    break
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("AbstractCodeRunner.ping_status(): unexpected error")

    async def feed_batch(self, opts: Mapping[str, Any]) -> None:
        transport = await self._get_transport()
        clean_cmd = opts.get("clean", "")
        if clean_cmd is None:
            clean_cmd = ""
        await transport.send_multipart([
            RunnerVerb.CLEAN.frame,
            clean_cmd.encode("utf8"),
        ])
        build_cmd = opts.get("build", "")
        if build_cmd is None:
            build_cmd = ""
        await transport.send_multipart([
            RunnerVerb.BUILD.frame,
            build_cmd.encode("utf8"),
        ])
        exec_cmd = opts.get("exec", "")
        if exec_cmd is None:
            exec_cmd = ""
        await transport.send_multipart([
            RunnerVerb.EXEC.frame,
            exec_cmd.encode("utf8"),
        ])

    async def feed_code(self, text: str) -> None:
        transport = await self._get_transport()
        await transport.send_multipart([RunnerVerb.CODE.frame, text.encode("utf8")])

    async def feed_input(self, text: str) -> None:
        transport = await self._get_transport()
        await transport.send_multipart([RunnerVerb.INPUT.frame, text.encode("utf8")])

    async def feed_event(self, evdata: Any) -> None:
        transport = await self._get_transport()
        data = {
            "type": evdata.type,
            "data": evdata.data,
        }
        await transport.send_multipart([RunnerVerb.EVENT.frame, _dump_json_bytes(data)])

    async def feed_interrupt(self) -> None:
        transport = await self._get_transport()
        await transport.send_multipart([RunnerVerb.INTERRUPT.frame, b""])

    async def feed_and_get_status(self) -> dict[str, float] | None:
        transport = await self._get_transport()
        await transport.send_multipart([RunnerVerb.STATUS.frame, b""])
        try:
            result = await self.status_queue.get()
            self.status_queue.task_done()
            return cast(dict[str, float] | None, msgpack.unpackb(result))
        except asyncio.CancelledError:
            return None

    async def feed_and_get_completion(
        self, code_text: str, opts: Mapping[str, Any]
    ) -> CodeCompletionResult:
        transport = await self._get_transport()
        payload = {
            "code": code_text,
        }
        payload.update(opts)
        await transport.send_multipart([
            RunnerVerb.COMPLETE.frame,
            _dump_json_bytes(payload),
        ])
        try:
            result = await self.completion_queue.get()
            self.completion_queue.task_done()
            return CodeCompletionResult.success(load_json(result))
        except asyncio.CancelledError:
            return CodeCompletionResult.failure()

    async def feed_start_model_service(self, model_info: Mapping[str, Any]) -> dict[str, Any]:
        transport = await self._get_transport()
        await transport.send_multipart([
            RunnerVerb.START_MODEL_SERVICE.frame,
            _dump_json_bytes(model_info),
        ])
        health_check_info = model_info.get("service", {}).get("health_check")
        if health_check_info and health_check_info.get("enable"):
            timeout_seconds = (
                health_check_info["max_retries"] * health_check_info["max_wait_time"] + 10
            )
        else:
            timeout_seconds = 10
        try:
            async with timeout(timeout_seconds):
                result = await self.model_service_queue.get()
            self.model_service_queue.task_done()
            return cast(dict[str, Any], load_json(result))
        except asyncio.CancelledError:
            return {"status": "failed", "error": "cancelled"}
        except TimeoutError:
            return {"status": "failed", "error": "timeout"}

    async def feed_start_service(self, service_info: Mapping[str, Any]) -> dict[str, Any]:
        transport = await self._get_transport()
        await transport.send_multipart([
            RunnerVerb.START_SERVICE.frame,
            _dump_json_bytes(service_info),
        ])
        try:
            with timeout(10):
                result = await self.service_queue.get()
            self.service_queue.task_done()
            return cast(dict[str, Any], load_json(result))
        except asyncio.CancelledError:
            return {"status": "failed", "error": "cancelled"}
        except TimeoutError:
            return {"status": "failed", "error": "timeout"}

    async def feed_shutdown_service(self, service_name: str) -> None:
        transport = await self._get_transport()
        await transport.send_multipart([
            RunnerVerb.SHUTDOWN_SERVICE.frame,
            _dump_json_bytes(service_name),
        ])

    async def feed_service_apps(self) -> dict[str, Any]:
        transport = await self._get_transport()
        await transport.send_multipart([
            RunnerVerb.GET_APPS.frame,
            b"",
        ])
        try:
            with timeout(10):
                result = await self.service_apps_info_queue.get()
            self.service_apps_info_queue.task_done()
            return cast(dict[str, Any], load_json(result))
        except asyncio.CancelledError:
            return {"status": "failed", "error": "cancelled"}
        except TimeoutError:
            return {"status": "failed", "error": "timeout"}

    async def _guest_request(
        self,
        verb: RunnerVerb,
        payload: Mapping[str, Any],
        *,
        body: bytes = b"",
        timeout_seconds: float = 60.0,
    ) -> tuple[Mapping[str, Any], bytes]:
        transport = await self._get_transport()
        request_id = secrets.token_hex(8)
        header = _dump_json_bytes({**payload, "req": request_id})
        await transport.send_multipart([verb.frame, header + b"\n" + body])
        try:
            async with asyncio.timeout(timeout_seconds):
                while True:
                    raw = await self.transfer_queue.get()
                    self.transfer_queue.task_done()
                    line, _, answer = raw.partition(b"\n")
                    reply = cast(Mapping[str, Any], load_json(line))
                    if reply.get("req") == request_id:
                        break
        except TimeoutError as e:
            raise StaleAnswerRefused(
                extra_msg=f"{verb.value} on kernel {self.kernel_id} went unanswered"
            ) from e
        if not reply.get("ok"):
            raise PermissionError(reply.get("error") or f"{verb.value} refused inside the guest")
        return reply, answer

    async def feed_list_files(self, container_path: str) -> dict[str, Any]:
        reply, _ = await self._guest_request(RunnerVerb.LIST_FILES, {"path": container_path})
        return {
            "files": json.dumps(reply["files"]),
            "errors": reply.get("errors", ""),
            "abspath": reply["abspath"],
        }

    async def feed_upload_file(self, container_path: str, filedata: bytes) -> None:
        await self._guest_request(
            RunnerVerb.UPLOAD_FILE, {"path": container_path}, body=filedata
        )

    async def feed_download_file(self, container_path: str) -> bytes:
        _, body = await self._guest_request(RunnerVerb.DOWNLOAD_FILE, {"path": container_path})
        if not body:
            raise StaleAnswerRefused(
                extra_msg=f"the guest returned an empty archive for {container_path}"
            )
        return body

    async def feed_download_single(self, container_path: str) -> bytes:
        _, body = await self._guest_request(RunnerVerb.DOWNLOAD_SINGLE, {"path": container_path})
        if not body:
            raise StaleAnswerRefused(
                extra_msg=f"the guest returned an empty file for {container_path}"
            )
        return body

    async def feed_get_logs(self) -> dict[str, Any]:
        reply, body = await self._guest_request(RunnerVerb.GET_LOGS, {})
        return {"logs": body.decode("utf-8", errors="replace"), "truncated": reply.get("truncated")}

    async def watchdog(self) -> None:
        try:
            await asyncio.sleep(self.exec_timeout)
            if self.output_queue is not None:
                # TODO: what to do if None?
                await self.output_queue.put(ResultRecord("exec-timeout", None))
        except asyncio.CancelledError:
            pass

    @staticmethod
    def aggregate_console(
        result: NextResult, records: Sequence[ResultRecord], api_ver: int
    ) -> None:
        if api_ver == 1:
            stdout_items = []
            stderr_items = []
            media_items = []
            html_items = []

            for rec in records:
                if rec.msg_type == "stdout":
                    stdout_items.append(rec.data or "")
                elif rec.msg_type == "stderr":
                    stderr_items.append(rec.data or "")
                elif rec.msg_type == "media" and rec.data is not None:
                    o = load_json(rec.data)
                    media_items.append((o["type"], o["data"]))
                elif rec.msg_type == "html":
                    html_items.append(rec.data)

            result["stdout"] = "".join(stdout_items)
            result["stderr"] = "".join(stderr_items)
            result["media"] = media_items
            result["html"] = html_items

        elif api_ver >= 2:
            console_items: list[tuple[ConsoleItemType, str | tuple[str, str]]] = []
            last_stdout = io.StringIO()
            last_stderr = io.StringIO()

            for rec in records:
                if last_stdout.tell() and rec.msg_type != "stdout":
                    console_items.append(("stdout", last_stdout.getvalue()))
                    last_stdout.seek(0)
                    last_stdout.truncate(0)
                if last_stderr.tell() and rec.msg_type != "stderr":
                    console_items.append(("stderr", last_stderr.getvalue()))
                    last_stderr.seek(0)
                    last_stderr.truncate(0)

                if rec.msg_type == "stdout":
                    last_stdout.write(rec.data or "")
                elif rec.msg_type == "stderr":
                    last_stderr.write(rec.data or "")
                elif rec.msg_type == "media" and rec.data is not None:
                    o = load_json(rec.data)
                    console_items.append(("media", (o["type"], o["data"])))
                elif rec.msg_type in outgoing_msg_types:
                    # FIXME: currently mypy cannot handle dynamic specialization of literals.
                    console_items.append((rec.msg_type, rec.data))  # type: ignore

            if last_stdout.tell():
                console_items.append(("stdout", last_stdout.getvalue()))
            if last_stderr.tell():
                console_items.append(("stderr", last_stderr.getvalue()))

            result["console"] = console_items
            last_stdout.close()
            last_stderr.close()

        else:
            raise AssertionError("Unrecognized API version")

    async def get_next_result(self, api_ver: int = 2, flush_timeout: float = 2.0) -> NextResult:
        # Context: per API request
        has_continuation = ClientFeatures.CONTINUATION in self.client_features
        records = []
        result: NextResult
        try:
            if self.output_queue is None:
                raise OutputQueueNotInitializedError
            with timeout(flush_timeout if has_continuation else None):
                while True:
                    rec = await self.output_queue.get()
                    if rec.msg_type in outgoing_msg_types:
                        records.append(rec)
                    self.output_queue.task_done()
                    if rec.msg_type == "finished":
                        data = load_json(rec.data) if rec.data else {}
                        raise RunFinished(data)
                    if rec.msg_type == "clean-finished":
                        data = load_json(rec.data) if rec.data else {}
                        raise CleanFinished(data)
                    if rec.msg_type == "build-finished":
                        data = load_json(rec.data) if rec.data else {}
                        raise BuildFinished(data)
                    if rec.msg_type == "waiting-input":
                        opts = load_json(rec.data) if rec.data else {}
                        raise InputRequestPending(opts)
                    if rec.msg_type == "exec-timeout":
                        raise ExecTimeout
        except asyncio.CancelledError:
            self.resume_output_queue()
            raise
        except TimeoutError:
            result = {
                "runId": self.current_run_id,
                "status": "continued",
                "exitCode": None,
                "options": None,
            }
            type(self).aggregate_console(result, records, api_ver)
            self.resume_output_queue()
            return result
        except CleanFinished as e:
            result = {
                "runId": self.current_run_id,
                "status": "clean-finished",
                "exitCode": e.data.get("exitCode"),
                "options": None,
            }
            type(self).aggregate_console(result, records, api_ver)
            self.next_output_queue()
            return result
        except BuildFinished as e:
            result = {
                "runId": self.current_run_id,
                "status": "build-finished",
                "exitCode": e.data.get("exitCode"),
                "options": None,
            }
            type(self).aggregate_console(result, records, api_ver)
            self.next_output_queue()
            return result
        except RunFinished as e:
            result = {
                "runId": self.current_run_id,
                "status": "finished",
                "exitCode": e.data.get("exitCode"),
                "options": None,
            }
            type(self).aggregate_console(result, records, api_ver)
            self.next_output_queue()
            return result
        except ExecTimeout:
            result = {
                "runId": self.current_run_id,
                "status": "exec-timeout",
                "exitCode": None,
                "options": None,
            }
            log.warning("Execution timeout detected on kernel {}", self.kernel_id)
            type(self).aggregate_console(result, records, api_ver)
            self.next_output_queue()
            return result
        except InputRequestPending as e:
            result = {
                "runId": self.current_run_id,
                "status": "waiting-input",
                "exitCode": None,
                "options": e.data,
            }
            type(self).aggregate_console(result, records, api_ver)
            self.resume_output_queue()
            return result
        except Exception:
            log.exception("unexpected error")
            raise

    async def attach_output_queue(self, run_id: str | None) -> None:
        # Context: per API request
        if run_id is None:
            run_id = secrets.token_hex(16)
        if run_id is None:
            raise ValueError("run_id cannot be None")
        if run_id not in self.pending_queues:
            q: asyncio.Queue[ResultRecord] = asyncio.Queue(maxsize=4096)
            activated = asyncio.Event()
            self.pending_queues[run_id] = (activated, q)
        else:
            activated, q = self.pending_queues[run_id]
        log.info(
            "CodeRunner.attach_output_queue(k:{0}, run_id:{1}, is running event set:{2})",
            self.kernel_id,
            run_id,
            activated.is_set(),
        )
        if self.output_queue is None:
            self.output_queue = q
        else:
            if self.current_run_id == run_id:
                # No need to wait if we are continuing.
                pass
            else:
                # If there is an outstanding ongoning execution,
                # wait until it has "finished".
                await activated.wait()
                activated.clear()
        self.current_run_id = run_id
        if self.output_queue is not q:
            raise OutputQueueMismatchError

    def resume_output_queue(self) -> None:
        """
        Use this to conclude get_next_result() when the execution should be
        continued from the client.

        At that time, we need to reuse the current run ID and its output queue.
        We don't change self.output_queue here so that we can continue to read
        outputs while the client sends the continuation request.
        """
        if self.current_run_id is None:
            return
        self.pending_queues.move_to_end(self.current_run_id, last=False)

    def next_output_queue(self) -> None:
        """
        Use this to conclude get_next_result() when we have finished a "run".
        """
        if self.current_run_id is None:
            raise RunIdNotSetError
        self.pending_queues.pop(self.current_run_id, None)
        self.current_run_id = None
        if len(self.pending_queues) > 0:
            # Make the next waiting API request handler to proceed.
            _, (activated, q) = self.pending_queues.popitem(last=False)
            self.output_queue = q
            activated.set()
        else:
            # If there is no pending request, just ignore all outputs
            # from the kernel.
            self.output_queue = None

    async def read_output(self) -> None:
        # We should use incremental decoder because some kernels may
        # send us incomplete UTF-8 byte sequences (e.g., Julia).
        decoders = (
            codecs.getincrementaldecoder("utf8")(errors="replace"),
            codecs.getincrementaldecoder("utf8")(errors="replace"),
        )
        transport = await self._get_transport()
        stalls = 0
        while True:
            try:
                data = await transport.recv_multipart()
                if len(data) != 2:
                    log.warning("Invalid data from output socket, skip. (data: {})", data)
                    continue
                msg_type, msg_data = data
                try:
                    match msg_type:
                        case RunnerReply.STATUS.frame:
                            await self.status_queue.put(msg_data)
                        case RunnerReply.COMPLETION.frame:
                            await self.completion_queue.put(msg_data)
                        case RunnerReply.SERVICE_RESULT.frame:
                            await self.service_queue.put(msg_data)
                        case RunnerReply.MODEL_SERVICE_RESULT.frame:
                            await self.model_service_queue.put(msg_data)
                        case RunnerReply.MODEL_SERVICE_STATUS.frame:
                            # no-op
                            pass
                        case (
                            RunnerReply.FILES_RESULT.frame
                            | RunnerReply.TRANSFER_RESULT.frame
                            | RunnerReply.LOGS_RESULT.frame
                        ):
                            self.transfer_queue.put_nowait(msg_data)
                        case RunnerReply.APPS_RESULT.frame:
                            await self.service_apps_info_queue.put(msg_data)
                        case RunnerReply.STDOUT.frame:
                            if self.output_queue is None:
                                continue
                            if len(msg_data) > self.max_record_size:
                                msg_data = msg_data[: self.max_record_size]
                            await self.output_queue.put(
                                ResultRecord(
                                    "stdout",
                                    decoders[0].decode(msg_data),
                                )
                            )
                        case RunnerReply.STDERR.frame:
                            if self.output_queue is None:
                                continue
                            if len(msg_data) > self.max_record_size:
                                msg_data = msg_data[: self.max_record_size]
                            await self.output_queue.put(
                                ResultRecord(
                                    "stderr",
                                    decoders[1].decode(msg_data),
                                )
                            )
                        case _:
                            # Normal outputs should go to the current
                            # output queue.
                            if self.output_queue is None:
                                continue
                            await self.output_queue.put(
                                ResultRecord(
                                    cast(ResultType, msg_type.decode("ascii")),
                                    msg_data.decode("utf8"),
                                )
                            )
                except asyncio.QueueFull:
                    pass
                if msg_type == RunnerReply.BUILD_FINISHED.frame:
                    # finalize incremental decoder
                    decoders[0].decode(b"", True)
                    decoders[1].decode(b"", True)
                elif msg_type == RunnerReply.FINISHED.frame:
                    # finalize incremental decoder
                    decoders[0].decode(b"", True)
                    decoders[1].decode(b"", True)
                    self.finished_at = time.monotonic()
            except ChannelNotEstablished as e:
                stalls += 1
                if stalls > REDIAL_STALL_LIMIT:
                    log.warning("the kernel channel stayed unreachable ({}); giving up", e)
                    self._is_socket_invalid = True
                    break
                await asyncio.sleep(REDIAL_BACKOFF)
                continue
            except InvalidSocket:
                self._is_socket_invalid = True
                break
            except (asyncio.CancelledError, GeneratorExit):
                break
            except Exception:
                log.exception("unexpected error")
                break
            stalls = 0
