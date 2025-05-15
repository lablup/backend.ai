import asyncio
import codecs
import enum
import io
import logging
import math
import secrets
from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import (
    Mapping,
    Sequence,
)
from dataclasses import dataclass
from typing import (
    Any,
    Final,
    FrozenSet,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    cast,
)

import zmq
import zmq.asyncio
from async_timeout import timeout

from ai.backend.common import msgpack
from ai.backend.common.asyncio import current_loop
from ai.backend.common.enum_extension import StringSetFlag
from ai.backend.common.events.dispatcher import (
    EventProducer,
)
from ai.backend.common.events.model_serving import (
    ModelServiceStatusEvent,
)
from ai.backend.common.json import dump_json, load_json
from ai.backend.common.types import (
    KernelId,
    ModelServiceStatus,
    SessionId,
)
from ai.backend.logging import BraceStyleAdapter

from ..exception import InvalidSocket
from ..types import AgentEventData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

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
outgoing_msg_types: FrozenSet[ConsoleItemType] = frozenset([
    "stdout",
    "stderr",
    "media",
    "html",
    "log",
    "completion",
])


class RunEvent(Exception):
    data: Any

    def __init__(self, data=None):
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


class ClientFeatures(StringSetFlag):
    INPUT = "input"
    CONTINUATION = "continuation"


# TODO: use Python 3.7 contextvars for per-client feature selection
DEFAULT_CLIENT_FEATURES = frozenset({
    ClientFeatures.INPUT.value,
    ClientFeatures.CONTINUATION.value,
})
DEFATUL_API_VERSION: Final[int] = 4


class ExecResultType(enum.StrEnum):
    CONTINUED = "continued"
    CLEAN_FINISHED = "clean-finished"
    BUILD_FINISHED = "build-finished"
    FINISHED = "finished"
    EXEC_TIMEOUT = "exec-timeout"
    WAITING_INPUT = "waiting-input"


class ExecMessageType(enum.StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"
    MEDIA = "media"
    HTML = "html"
    LOG = "log"
    COMPLETION = "completion"


@dataclass
class ResultRecord:
    msg_type: ExecResultType | str
    data: Optional[str] = None


@dataclass
class NextResult:
    runId: Optional[str]
    status: ExecResultType
    exitCode: Optional[int]
    options: Optional[Mapping[str, Any]]
    # v1
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    media: Sequence[Any] = []
    html: Sequence[Any] = []
    # v2
    console: Sequence[Any] = []


_zctx: Optional[zmq.asyncio.Context] = None


class RobustSocket:
    _zctx: zmq.asyncio.Context
    _sock: zmq.asyncio.Socket
    _socket_type: int
    _addr: str

    def __init__(
        self,
        socket_type: int,
        addr: str,
    ) -> None:
        self._init_zctx()
        self._socket_type = socket_type
        self._addr = addr
        self._sock = self._zctx.socket(self._socket_type)
        self._sock.connect(self._addr)
        self._sock.setsockopt(zmq.LINGER, 50)

    @property
    def addr(self) -> str:
        return self._addr

    @property
    def socket(self) -> zmq.asyncio.Socket:
        return self._sock

    def close(self) -> None:
        try:
            self._sock.close()
        except zmq.ZMQError:
            pass

    def _init_zctx(self) -> None:
        global _zctx
        if _zctx is None:
            _zctx = zmq.asyncio.Context()
        self._zctx = _zctx

    def recreate_socket(self):
        self._init_zctx()
        self._sock = self._zctx.socket(self._socket_type)
        self._sock.connect(self._addr)
        self._sock.setsockopt(zmq.LINGER, 50)


class SocketPair:
    _input_sock: RobustSocket
    _output_sock: RobustSocket

    def __init__(self, input_sock: RobustSocket, output_sock: RobustSocket):
        self._input_sock = input_sock
        self._output_sock = output_sock

    async def send_multipart(self, msg_parts: Sequence[bytes]) -> None:
        try:
            await self._input_sock.socket.send_multipart(msg_parts)
        except zmq.ZMQError as e:
            if e.errno in (zmq.ENOTSOCK, zmq.ETERM):
                log.warning(
                    f"Socket invalid, recreating socket (addr: {self._input_sock.addr}, err: {repr(e)})"
                )
                self._input_sock.recreate_socket()
                self._output_sock.recreate_socket()
                await self._input_sock.socket.send_multipart(msg_parts)
            else:
                log.error(
                    "Unexpected error while sending message to socket (addr: {}, err: {})",
                    self._input_sock.addr,
                    repr(e),
                )
                raise

    async def recv_multipart(self) -> list[bytes]:
        try:
            return await self._output_sock.socket.recv_multipart()
        except zmq.ZMQError as e:
            if e.errno in (zmq.ENOTSOCK, zmq.ETERM):
                log.exception(f"Socket invalid (addr: {self._output_sock.addr}, err: {repr(e)})")
                raise InvalidSocket
            else:
                raise

    def close(self) -> None:
        self._input_sock.close()
        self._output_sock.close()


def _aggregate_console_v1(result: NextResult, records: Sequence[ResultRecord]) -> None:
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

    result.stdout = "".join(stdout_items)
    result.stderr = "".join(stderr_items)
    result.media = media_items
    result.html = html_items


def _aggregate_console_v2(result: NextResult, records: Sequence[ResultRecord]) -> None:
    console_items: List[Tuple[ConsoleItemType, Union[str, Tuple[str, str]]]] = []
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

    result.console = console_items
    last_stdout.close()
    last_stderr.close()


def _aggregate_console(result: NextResult, records: Sequence[ResultRecord], api_ver: int) -> None:
    if api_ver == 1:
        _aggregate_console_v1(result, records)
        return
    if api_ver >= 2:
        _aggregate_console_v2(result, records)
        return
    raise AssertionError("Unrecognized API version")


class AbstractCodeRunner(ABC):
    @abstractmethod
    async def close(self) -> None:
        """
        Close the code runner.
        """
        raise NotImplementedError

    @abstractmethod
    async def ping(self) -> Optional[Mapping[str, float]]:
        raise NotImplementedError

    @abstractmethod
    async def ping_status(self):
        """
        This is to keep the REPL in/out port mapping in the Linux
        kernel's NAT table alive.
        """
        raise NotImplementedError

    @abstractmethod
    async def feed_batch(self, opts: Mapping[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def feed_code(self, text: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def feed_input(self, text: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def feed_event(self, evdata: AgentEventData) -> None:
        raise NotImplementedError

    @abstractmethod
    async def feed_interrupt(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def feed_and_get_status(self) -> Optional[Mapping[str, float]]:
        raise NotImplementedError

    @abstractmethod
    async def feed_and_get_completion(self, code_text, opts):
        raise NotImplementedError

    @abstractmethod
    async def feed_start_model_service(self, model_info):
        raise NotImplementedError

    @abstractmethod
    async def feed_start_service(self, service_info):
        raise NotImplementedError

    @abstractmethod
    async def feed_shutdown_service(self, service_name: str):
        raise NotImplementedError

    @abstractmethod
    async def feed_service_apps(self):
        raise NotImplementedError

    @abstractmethod
    async def watchdog(self, exec_timeout: float) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_next_result(self, api_ver=2, flush_timeout=2.0) -> NextResult:
        # Context: per API request
        raise NotImplementedError

    @abstractmethod
    async def attach_output_queue(self, run_id: Optional[str]) -> None:
        # Context: per API request
        raise NotImplementedError

    @abstractmethod
    def resume_output_queue(self) -> None:
        """
        Use this to conclude get_next_result() when the execution should be
        continued from the client.

        At that time, we need to reuse the current run ID and its output queue.
        We don't change self.output_queue here so that we can continue to read
        outputs while the client sends the continuation request.
        """
        raise NotImplementedError

    @abstractmethod
    def next_output_queue(self) -> None:
        """
        Use this to conclude get_next_result() when we have finished a "run".
        """
        raise NotImplementedError

    @abstractmethod
    async def read_output(self) -> None:
        """
        Read the output from the kernel and put it into the output queue.
        """
        raise NotImplementedError


class NopCodeRunner(AbstractCodeRunner):
    def __init__(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def ping(self) -> Optional[Mapping[str, float]]:
        return None

    async def ping_status(self) -> None:
        pass

    async def feed_batch(self, opts: Mapping[str, Any]) -> None:
        pass

    async def feed_code(self, text: str) -> None:
        pass

    async def feed_input(self, text: str) -> None:
        pass

    async def feed_event(self, evdata: AgentEventData) -> None:
        pass

    async def feed_interrupt(self) -> None:
        pass

    async def feed_and_get_status(self) -> Optional[Mapping[str, float]]:
        return None

    async def feed_and_get_completion(self, code_text, opts):
        return []

    async def feed_start_model_service(self, model_info):
        return {}

    async def feed_start_service(self, service_info):
        return {}

    async def feed_shutdown_service(self, service_name: str):
        pass

    async def feed_service_apps(self):
        return {}

    async def watchdog(self, exec_timeout: float) -> None:
        pass

    async def get_next_result(self, api_ver=2, flush_timeout=2.0) -> NextResult:
        raise NotImplementedError("NopCodeRunner does not support get_next_result()")

    async def attach_output_queue(self, run_id: Optional[str]) -> None:
        pass

    def resume_output_queue(self) -> None:
        pass

    def next_output_queue(self) -> None:
        pass

    async def read_output(self) -> None:
        pass


class CodeRunner(AbstractCodeRunner):
    _kernel_id: KernelId
    _session_id: SessionId
    _event_producer: EventProducer
    _client_features: FrozenSet[str]
    _sockets: SocketPair
    _max_record_size: int

    _completion_queue: asyncio.Queue[bytes]
    _service_queue: asyncio.Queue[bytes]
    _model_service_queue: asyncio.Queue[bytes]
    _service_apps_info_queue: asyncio.Queue[bytes]
    _status_queue: asyncio.Queue[bytes]
    _output_queue: Optional[asyncio.Queue[ResultRecord]]
    _pending_queues: OrderedDict[str, Tuple[asyncio.Event, asyncio.Queue[ResultRecord]]]
    _current_run_id: Optional[str]

    _tasks: list[asyncio.Task]
    _closed_event: asyncio.Event

    def __init__(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        event_producer: EventProducer,
        sockets: SocketPair,
        *,
        exec_timeout: float = 0,
        client_features: Optional[FrozenSet[str]] = None,
    ) -> None:
        if not math.isfinite(exec_timeout) or exec_timeout < 0:
            raise ValueError("execution timeout must be a zero or finite positive number.")
        self._kernel_id = kernel_id
        self._session_id = session_id
        self._event_producer = event_producer
        self._client_features = client_features or frozenset()
        self._sockets = sockets
        self._max_record_size = 10 * (2**20)  # 10 MBytes
        self._completion_queue = asyncio.Queue(maxsize=128)
        self._service_queue = asyncio.Queue(maxsize=128)
        self._model_service_queue = asyncio.Queue(maxsize=128)
        self._service_apps_info_queue = asyncio.Queue(maxsize=128)
        self._status_queue = asyncio.Queue(maxsize=128)
        self._output_queue = None
        self._pending_queues = OrderedDict()
        self._current_run_id = None
        loop = current_loop()
        self._closed_event = asyncio.Event()
        self._tasks = [loop.create_task(self.ping_status()), loop.create_task(self.read_output())]
        if exec_timeout > 0:
            self._tasks.append(loop.create_task(self.watchdog(exec_timeout)))

    async def close(self) -> None:
        if self._closed_event.is_set():
            return
        self._closed_event.set()
        try:
            for task in self._tasks:
                if task and not task.done():
                    task.cancel()
                    await task
            self._sockets.close()
            # WARNING:
            # destroying zmq contexts here with possibility of re-entrance
            # may cause deadlocks.
        except Exception as e:
            log.exception("AbstractCodeRunner.close(): unexpected error: {}", repr(e))

    async def ping(self) -> Optional[Mapping[str, float]]:
        try:
            return await self.feed_and_get_status()
        except Exception as e:
            log.error("AbstractCodeRunner.ping(): unexpected error ({})", repr(e))
            return None

    async def ping_status(self):
        """
        This is to keep the REPL in/out port mapping in the Linux
        kernel's NAT table alive.
        """
        try:
            while not self._closed_event.is_set():
                ret = await self.feed_and_get_status()
                if ret is None:
                    break
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error("AbstractCodeRunner.ping_status(): unexpected error ({})", repr(e))

    async def feed_batch(self, opts: Mapping[str, Any]) -> None:
        sock = self._sockets
        clean_cmd = opts.get("clean", "")
        if clean_cmd is None:
            clean_cmd = ""
        await sock.send_multipart([
            b"clean",
            clean_cmd.encode("utf8"),
        ])
        build_cmd = opts.get("build", "")
        if build_cmd is None:
            build_cmd = ""
        await sock.send_multipart([
            b"build",
            build_cmd.encode("utf8"),
        ])
        exec_cmd = opts.get("exec", "")
        if exec_cmd is None:
            exec_cmd = ""
        await sock.send_multipart([
            b"exec",
            exec_cmd.encode("utf8"),
        ])

    async def feed_code(self, text: str) -> None:
        sock = self._sockets
        await sock.send_multipart([b"code", text.encode("utf8")])

    async def feed_input(self, text: str) -> None:
        sock = self._sockets
        await sock.send_multipart([b"input", text.encode("utf8")])

    async def feed_event(self, evdata: AgentEventData) -> None:
        sock = self._sockets
        data = {
            "type": evdata.type,
            "data": evdata.data,
        }
        await sock.send_multipart([b"event", dump_json(data)])

    async def feed_interrupt(self) -> None:
        await self._sockets.send_multipart([b"interrupt", b""])

    async def feed_and_get_status(self) -> Optional[Mapping[str, float]]:
        await self._sockets.send_multipart([b"status", b""])
        try:
            result = await self._status_queue.get()
            self._status_queue.task_done()
            return msgpack.unpackb(result)
        except asyncio.CancelledError:
            return None

    async def feed_and_get_completion(self, code_text, opts):
        payload = {
            "code": code_text,
        }
        payload.update(opts)
        await self._sockets.send_multipart([
            b"complete",
            dump_json(payload),
        ])
        try:
            result = await self._completion_queue.get()
            self._completion_queue.task_done()
            return load_json(result)
        except asyncio.CancelledError:
            return []

    async def feed_start_model_service(self, model_info):
        await self._sockets.send_multipart([
            b"start-model-service",
            dump_json(model_info),
        ])
        if health_check_info := model_info.get("service", {}).get("health_check"):
            timeout_seconds = (
                health_check_info["max_retries"] * health_check_info["max_wait_time"] + 10
            )
        else:
            timeout_seconds = 10
        try:
            async with timeout(timeout_seconds):
                result = await self._model_service_queue.get()
            self._model_service_queue.task_done()
            return load_json(result)
        except asyncio.CancelledError:
            return {"status": "failed", "error": "cancelled"}
        except asyncio.TimeoutError:
            return {"status": "failed", "error": "timeout"}

    async def feed_start_service(self, service_info):
        await self._sockets.send_multipart([
            b"start-service",
            dump_json(service_info),
        ])
        try:
            with timeout(10):
                result = await self._service_queue.get()
            self._service_queue.task_done()
            return load_json(result)
        except asyncio.CancelledError:
            return {"status": "failed", "error": "cancelled"}
        except asyncio.TimeoutError:
            return {"status": "failed", "error": "timeout"}

    async def feed_shutdown_service(self, service_name: str):
        sock = self._sockets
        await sock.send_multipart([
            b"shutdown-service",
            dump_json(service_name),
        ])

    async def feed_service_apps(self):
        sock = self._sockets
        await sock.send_multipart([
            b"get-apps",
            "".encode("utf8"),
        ])
        try:
            with timeout(10):
                result = await self._service_apps_info_queue.get()
            self._service_apps_info_queue.task_done()
            return load_json(result)
        except asyncio.CancelledError:
            return {"status": "failed", "error": "cancelled"}
        except asyncio.TimeoutError:
            return {"status": "failed", "error": "timeout"}

    async def watchdog(self, exec_timeout: float) -> None:
        try:
            await asyncio.sleep(exec_timeout)
            if self._output_queue is not None:
                # TODO: what to do if None?
                await self._output_queue.put(ResultRecord(ExecResultType.EXEC_TIMEOUT, None))
        except asyncio.CancelledError:
            pass

    async def get_next_result(self, api_ver=2, flush_timeout=2.0) -> NextResult:
        # Context: per API request
        has_continuation = ClientFeatures.CONTINUATION in self._client_features
        records = []
        result: NextResult
        try:
            assert self._output_queue is not None
            with timeout(flush_timeout if has_continuation else None):
                while True:
                    rec = await self._output_queue.get()
                    if rec.msg_type in outgoing_msg_types:
                        records.append(rec)
                    self._output_queue.task_done()
                    if rec.msg_type == "finished":
                        data = load_json(rec.data) if rec.data else {}
                        raise RunFinished(data)
                    elif rec.msg_type == "clean-finished":
                        data = load_json(rec.data) if rec.data else {}
                        raise CleanFinished(data)
                    elif rec.msg_type == "build-finished":
                        data = load_json(rec.data) if rec.data else {}
                        raise BuildFinished(data)
                    elif rec.msg_type == "waiting-input":
                        opts = load_json(rec.data) if rec.data else {}
                        raise InputRequestPending(opts)
                    elif rec.msg_type == "exec-timeout":
                        raise ExecTimeout
        except asyncio.CancelledError:
            self.resume_output_queue()
            raise
        except asyncio.TimeoutError:
            result = NextResult(
                runId=self._current_run_id,
                status=ExecResultType.CONTINUED,
                exitCode=None,
                options=None,
            )
            _aggregate_console(result, records, api_ver)
            self.resume_output_queue()
            return result
        except CleanFinished as e:
            result = NextResult(
                runId=self._current_run_id,
                status=ExecResultType.CLEAN_FINISHED,
                exitCode=e.data.get("exitCode"),
                options=None,
            )
            _aggregate_console(result, records, api_ver)
            self.resume_output_queue()
            return result
        except BuildFinished as e:
            result = NextResult(
                runId=self._current_run_id,
                status=ExecResultType.BUILD_FINISHED,
                exitCode=e.data.get("exitCode"),
                options=None,
            )
            _aggregate_console(result, records, api_ver)
            self.resume_output_queue()
            return result
        except RunFinished as e:
            result = NextResult(
                runId=self._current_run_id,
                status=ExecResultType.FINISHED,
                exitCode=e.data.get("exitCode"),
                options=None,
            )
            _aggregate_console(result, records, api_ver)
            self.next_output_queue()
            return result
        except ExecTimeout:
            result = NextResult(
                runId=self._current_run_id,
                status=ExecResultType.EXEC_TIMEOUT,
                exitCode=None,
                options=None,
            )
            log.warning(f"Execution timeout detected on kernel {self._kernel_id}")
            _aggregate_console(result, records, api_ver)
            self.next_output_queue()
            return result
        except InputRequestPending as e:
            result = NextResult(
                runId=self._current_run_id,
                status=ExecResultType.WAITING_INPUT,
                exitCode=None,
                options=e.data,
            )
            _aggregate_console(result, records, api_ver)
            self.resume_output_queue()
            return result
        except Exception:
            log.exception("unexpected error")
            raise

    async def attach_output_queue(self, run_id: Optional[str]) -> None:
        # Context: per API request
        if run_id is None:
            run_id = secrets.token_hex(16)
        if run_id not in self._pending_queues:
            q: asyncio.Queue[ResultRecord] = asyncio.Queue(maxsize=4096)
            activated = asyncio.Event()
            self._pending_queues[run_id] = (activated, q)
        else:
            activated, q = self._pending_queues[run_id]
        if self._output_queue is None:
            self._output_queue = q
        else:
            if self._current_run_id == run_id:
                # No need to wait if we are continuing.
                pass
            else:
                # If there is an outstanding ongoning execution,
                # wait until it has "finished".
                await activated.wait()
                activated.clear()
        self._current_run_id = run_id
        assert self._output_queue is q

    def resume_output_queue(self) -> None:
        """
        Use this to conclude get_next_result() when the execution should be
        continued from the client.

        At that time, we need to reuse the current run ID and its output queue.
        We don't change self.output_queue here so that we can continue to read
        outputs while the client sends the continuation request.
        """
        if self._current_run_id is None:
            return
        self._pending_queues.move_to_end(self._current_run_id, last=False)

    def next_output_queue(self) -> None:
        """
        Use this to conclude get_next_result() when we have finished a "run".
        """
        assert self._current_run_id is not None
        self._pending_queues.pop(self._current_run_id, None)
        self._current_run_id = None
        if len(self._pending_queues) > 0:
            # Make the next waiting API request handler to proceed.
            _, (activated, q) = self._pending_queues.popitem(last=False)
            self._output_queue = q
            activated.set()
        else:
            # If there is no pending request, just ignore all outputs
            # from the kernel.
            self._output_queue = None

    async def read_output(self) -> None:
        # We should use incremental decoder because some kernels may
        # send us incomplete UTF-8 byte sequences (e.g., Julia).
        decoders = (
            codecs.getincrementaldecoder("utf8")(errors="replace"),
            codecs.getincrementaldecoder("utf8")(errors="replace"),
        )
        sock = self._sockets
        while not self._closed_event.is_set():
            try:
                data = await sock.recv_multipart()
                if len(data) != 2:
                    log.warning(f"Invalid data from output socket, skip. (data: {data})")
                    continue
                msg_type, msg_data = data
                try:
                    match msg_type:
                        case b"status":
                            await self._status_queue.put(msg_data)
                        case b"completion":
                            await self._completion_queue.put(msg_data)
                        case b"service-result":
                            await self._service_queue.put(msg_data)
                        case b"model-service-result":
                            await self._model_service_queue.put(msg_data)
                        case b"model-service-status":
                            response = load_json(msg_data)
                            event = ModelServiceStatusEvent(
                                self._kernel_id,
                                self._session_id,
                                response["model_name"],
                                (
                                    ModelServiceStatus.HEALTHY
                                    if response["is_healthy"]
                                    else ModelServiceStatus.UNHEALTHY
                                ),
                            )
                            await self._event_producer.produce_event(event)
                        case b"apps-result":
                            await self._service_apps_info_queue.put(msg_data)
                        case b"stdout":
                            if self._output_queue is None:
                                continue
                            if len(msg_data) > self._max_record_size:
                                msg_data = msg_data[: self._max_record_size]
                            await self._output_queue.put(
                                ResultRecord(
                                    "stdout",
                                    decoders[0].decode(msg_data),
                                )
                            )
                        case b"stderr":
                            if self._output_queue is None:
                                continue
                            if len(msg_data) > self._max_record_size:
                                msg_data = msg_data[: self._max_record_size]
                            await self._output_queue.put(
                                ResultRecord(
                                    "stderr",
                                    decoders[1].decode(msg_data),
                                )
                            )
                        case _:
                            # Normal outputs should go to the current
                            # output queue.
                            if self._output_queue is None:
                                continue
                            await self._output_queue.put(
                                ResultRecord(
                                    cast(ExecResultType, msg_type.decode("ascii")),
                                    msg_data.decode("utf8"),
                                )
                            )
                except asyncio.QueueFull:
                    pass
                if msg_type == b"build-finished":
                    # finalize incremental decoder
                    decoders[0].decode(b"", True)
                    decoders[1].decode(b"", True)
                elif msg_type == b"finished":
                    # finalize incremental decoder
                    decoders[0].decode(b"", True)
                    decoders[1].decode(b"", True)
            except InvalidSocket as e:
                log.error(
                    "Socket invalid, recreating socket (addr: {}, err: {})",
                    self._sockets._input_sock.addr,
                    repr(e),
                )
                break
            except (asyncio.CancelledError, GeneratorExit):
                break
            except Exception:
                log.exception("unexpected error")
                break
