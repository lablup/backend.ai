from __future__ import annotations

from abc import abstractmethod, ABCMeta
import asyncio
import codecs
from collections import OrderedDict, UserDict
from dataclasses import dataclass
import io
import json
import logging
import math
import re
import secrets
import time
from typing import (
    Any,
    Dict,
    FrozenSet,
    List,
    Literal,
    Mapping,
    Optional,
    Set,
    Sequence,
    Tuple,
    TypedDict,
    Union,
)

from async_timeout import timeout
import zmq, zmq.asyncio

from ai.backend.common import msgpack
from ai.backend.common.asyncio import current_loop
from ai.backend.common.docker import ImageRef
from ai.backend.common.enum_extension import StringSetFlag
from ai.backend.common.types import aobject, KernelId
from ai.backend.common.logging import BraceStyleAdapter
from .exception import UnsupportedBaseDistroError
from .resources import KernelResourceSpec

log = BraceStyleAdapter(logging.getLogger(__name__))

# msg types visible to the API client.
# (excluding control signals such as 'finished' and 'waiting-input'
# since they are passed as separate status field.)
ConsoleItemType = Literal[
    'stdout', 'stderr', 'media', 'html', 'log', 'completion',
]
outgoing_msg_types: FrozenSet[ConsoleItemType] = frozenset([
    'stdout', 'stderr', 'media', 'html', 'log', 'completion',
])
ResultType = Union[ConsoleItemType, Literal[
    'continued',
    'clean-finished',
    'build-finished',
    'finished',
    'exec-timeout',
    'waiting-input',
]]


class KernelFeatures(StringSetFlag):
    UID_MATCH = 'uid-match'
    USER_INPUT = 'user-input'
    BATCH_MODE = 'batch'
    QUERY_MODE = 'query'
    TTY_MODE = 'tty'


class ClientFeatures(StringSetFlag):
    INPUT = 'input'
    CONTINUATION = 'continuation'


# TODO: use Python 3.7 contextvars for per-client feature selection
default_client_features = frozenset({
    ClientFeatures.INPUT.value,
    ClientFeatures.CONTINUATION.value,
})
default_api_version = 4


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


@dataclass
class ResultRecord:
    msg_type: ResultType
    data: Optional[str] = None


class NextResult(TypedDict, total=False):
    runId: Optional[str]
    status: ResultType
    exitCode: Optional[int]
    options: Optional[Mapping[str, Any]]
    # v1
    stdout: Optional[str]
    stderr: Optional[str]
    media: Optional[Sequence[Any]]
    html: Optional[Sequence[Any]]
    # v2
    console: Optional[Sequence[Any]]


class AbstractKernel(UserDict, aobject, metaclass=ABCMeta):

    version: int
    agent_config: Mapping[str, Any]
    kernel_id: KernelId
    image: ImageRef
    resource_spec: KernelResourceSpec
    service_ports: Any
    data: Dict[Any, Any]
    last_used: float
    termination_reason: Optional[str]
    clean_event: Optional[asyncio.Future]
    stats_enabled: bool
    # FIXME: apply TypedDict to data in Python 3.8
    environ: Mapping[str, Any]

    _tasks: Set[asyncio.Task]

    runner: 'AbstractCodeRunner'

    def __init__(
        self, kernel_id: KernelId, image: ImageRef, version: int, *,
        agent_config: Mapping[str, Any],
        resource_spec: KernelResourceSpec,
        service_ports: Any,  # TODO: type-annotation
        data: Dict[Any, Any],
        environ: Mapping[str, Any],
    ) -> None:
        self.agent_config = agent_config
        self.kernel_id = kernel_id
        self.image = image
        self.version = version
        self.resource_spec = resource_spec
        self.service_ports = service_ports
        self.data = data
        self.last_used = time.monotonic()
        self.termination_reason = None
        self.clean_event = None
        self.stats_enabled = False
        self._tasks = set()
        self.environ = environ

    async def init(self) -> None:
        log.debug('kernel.init(k:{0}, api-ver:{1}, client-features:{2}): '
                  'starting new runner',
                  self.kernel_id, default_api_version, default_client_features)
        self.runner = await self.create_code_runner(
            client_features=default_client_features,
            api_version=default_api_version)

    def __getstate__(self) -> Mapping[str, Any]:
        props = self.__dict__.copy()
        del props['agent_config']
        del props['clean_event']
        del props['_tasks']
        return props

    def __setstate__(self, props) -> None:
        self.__dict__.update(props)
        # agent_config is set by the pickle.loads() caller.
        self.clean_event = None
        self._tasks = set()

    @abstractmethod
    async def close(self) -> None:
        """
        Release internal resources used for interacting with the kernel.
        Note that this does NOT terminate the container.
        """
        pass

    # We don't have "allocate_slots()" method here because:
    # - resource_spec is initialized by allocating slots at computer's alloc_map
    #   when creating new kernels.
    # - restoration from running containers is done by computer's classmethod
    #   "restore_from_container"

    def release_slots(self, computer_ctxs) -> None:
        """
        Release the resource slots occupied by the kernel
        to the allocation maps.
        """
        for accel_key, accel_alloc in self.resource_spec.allocations.items():
            computer_ctxs[accel_key].alloc_map.free(accel_alloc)

    @abstractmethod
    async def create_code_runner(
        self, *,
        client_features: FrozenSet[str],
        api_version: int,
    ) -> 'AbstractCodeRunner':
        raise NotImplementedError

    @abstractmethod
    async def check_status(self):
        raise NotImplementedError

    @abstractmethod
    async def get_completions(self, text, opts):
        raise NotImplementedError

    @abstractmethod
    async def get_logs(self):
        raise NotImplementedError

    @abstractmethod
    async def interrupt_kernel(self):
        raise NotImplementedError

    @abstractmethod
    async def start_service(self, service, opts):
        raise NotImplementedError

    @abstractmethod
    async def shutdown_service(self, service):
        raise NotImplementedError

    @abstractmethod
    async def get_service_apps(self):
        raise NotImplementedError

    @abstractmethod
    async def accept_file(self, filename, filedata):
        raise NotImplementedError

    @abstractmethod
    async def download_file(self, filepath):
        raise NotImplementedError

    @abstractmethod
    async def list_files(self, path: str):
        raise NotImplementedError

    async def execute(
        self,
        run_id: Optional[str],
        mode: Literal['batch', 'query', 'input', 'continue'],
        text: str,
        *,
        opts: Mapping[str, Any],
        api_version: int,
        flush_timeout: float,
    ) -> NextResult:
        myself = asyncio.current_task()
        assert myself is not None
        self._tasks.add(myself)
        try:
            await self.runner.attach_output_queue(run_id)
            try:
                if mode == 'batch':
                    await self.runner.feed_batch(opts)
                elif mode == 'query':
                    await self.runner.feed_code(text)
                elif mode == 'input':
                    await self.runner.feed_input(text)
                elif mode == 'continue':
                    pass
            except zmq.ZMQError:
                # cancel the operation by myself
                # since the peer is gone.
                raise asyncio.CancelledError
            return await self.runner.get_next_result(
                api_ver=api_version,
                flush_timeout=flush_timeout,
            )
        except asyncio.CancelledError:
            await self.runner.close()
            raise
        finally:
            self._tasks.remove(myself)


_zctx = None


class AbstractCodeRunner(aobject, metaclass=ABCMeta):

    kernel_id: KernelId
    started_at: float
    finished_at: Optional[float]
    exec_timeout: float
    max_record_size: int
    client_features: FrozenSet[str]

    input_sock: zmq.asyncio.Socket
    output_sock: zmq.asyncio.Socket

    completion_queue: asyncio.Queue[bytes]
    service_queue: asyncio.Queue[bytes]
    service_apps_info_queue: asyncio.Queue[bytes]
    status_queue: asyncio.Queue[bytes]
    output_queue: Optional[asyncio.Queue[ResultRecord]]
    current_run_id: Optional[str]
    pending_queues: OrderedDict[str, Tuple[asyncio.Event, asyncio.Queue[ResultRecord]]]

    read_task: Optional[asyncio.Task]
    status_task: Optional[asyncio.Task]
    watchdog_task: Optional[asyncio.Task]

    _closed: bool

    def __init__(
        self,
        kernel_id: KernelId,
        *,
        exec_timeout: float = 0,
        client_features: FrozenSet[str] = None,
    ) -> None:
        global _zctx
        self.kernel_id = kernel_id
        self.started_at = time.monotonic()
        self.finished_at = None
        if not math.isfinite(exec_timeout) or exec_timeout < 0:
            raise ValueError('execution timeout must be a zero or finite positive number.')
        self.kernel_id = kernel_id
        self.exec_timeout = exec_timeout
        self.max_record_size = 10 * (2 ** 20)  # 10 MBytes
        self.client_features = client_features or frozenset()
        if _zctx is None:
            _zctx = zmq.asyncio.Context()
        self.zctx = _zctx  # share the global context
        self.input_sock = self.zctx.socket(zmq.PUSH)
        self.output_sock = self.zctx.socket(zmq.PULL)
        self.completion_queue = asyncio.Queue(maxsize=128)
        self.service_queue = asyncio.Queue(maxsize=128)
        self.service_apps_info_queue = asyncio.Queue(maxsize=128)
        self.status_queue = asyncio.Queue(maxsize=128)
        self.output_queue = None
        self.pending_queues = OrderedDict()
        self.current_run_id = None
        self.read_task = None
        self.status_task = None
        self.watchdog_task = None
        self._closed = False

    async def __ainit__(self) -> None:
        loop = current_loop()
        self.input_sock.connect(await self.get_repl_in_addr())
        self.input_sock.setsockopt(zmq.LINGER, 50)
        self.output_sock.connect(await self.get_repl_out_addr())
        self.output_sock.setsockopt(zmq.LINGER, 50)
        self.status_task = loop.create_task(self.ping_status())
        self.read_task = loop.create_task(self.read_output())
        if self.exec_timeout > 0:
            self.watchdog_task = loop.create_task(self.watchdog())
        else:
            self.watchdog_task = None

    def __getstate__(self):
        props = self.__dict__.copy()
        del props['zctx']
        del props['input_sock']
        del props['output_sock']
        del props['completion_queue']
        del props['service_queue']
        del props['service_apps_info_queue']
        del props['status_queue']
        del props['output_queue']
        del props['pending_queues']
        del props['read_task']
        del props['status_task']
        del props['watchdog_task']
        del props['_closed']
        return props

    def __setstate__(self, props):
        global _zctx
        self.__dict__.update(props)
        if _zctx is None:
            _zctx = zmq.asyncio.Context()
        self.zctx = _zctx  # share the global context
        self.input_sock = self.zctx.socket(zmq.PUSH)
        self.output_sock = self.zctx.socket(zmq.PULL)
        self.completion_queue = asyncio.Queue(maxsize=128)
        self.service_queue = asyncio.Queue(maxsize=128)
        self.service_apps_info_queue = asyncio.Queue(maxsize=128)
        self.status_queue = asyncio.Queue(maxsize=128)
        self.output_queue = None
        self.pending_queues = OrderedDict()
        self.read_task = None
        self.status_task = None
        self.watchdog_task = None
        self._closed = False
        # __ainit__() is called by the caller.

    @abstractmethod
    async def get_repl_in_addr(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_repl_out_addr(self) -> str:
        raise NotImplementedError

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            if self.watchdog_task and not self.watchdog_task.done():
                self.watchdog_task.cancel()
                await self.watchdog_task
            if self.status_task and not self.status_task.done():
                self.status_task.cancel()
                await self.status_task
            if self.read_task and not self.read_task.done():
                self.read_task.cancel()
                await self.read_task
            if self.input_sock:
                self.input_sock.close()
            if self.output_sock:
                self.output_sock.close()
            # WARNING:
            # destroying zmq contexts here with possibility of re-entrance
            # may cause deadlocks.
        except Exception:
            log.exception("AbstractCodeRunner.close(): unexpected error")

    async def ping_status(self):
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

    async def feed_batch(self, opts):
        if self.input_sock.closed:
            raise asyncio.CancelledError
        clean_cmd = opts.get('clean', '')
        if clean_cmd is None:
            clean_cmd = ''
        await self.input_sock.send_multipart([
            b'clean',
            clean_cmd.encode('utf8'),
        ])
        build_cmd = opts.get('build', '')
        if build_cmd is None:
            build_cmd = ''
        await self.input_sock.send_multipart([
            b'build',
            build_cmd.encode('utf8'),
        ])
        exec_cmd = opts.get('exec', '')
        if exec_cmd is None:
            exec_cmd = ''
        await self.input_sock.send_multipart([
            b'exec',
            exec_cmd.encode('utf8'),
        ])

    async def feed_code(self, text: str):
        if self.input_sock.closed:
            raise asyncio.CancelledError
        await self.input_sock.send_multipart([b'code', text.encode('utf8')])

    async def feed_input(self, text: str):
        if self.input_sock.closed:
            raise asyncio.CancelledError
        await self.input_sock.send_multipart([b'input', text.encode('utf8')])

    async def feed_interrupt(self):
        if self.input_sock.closed:
            raise asyncio.CancelledError
        await self.input_sock.send_multipart([b'interrupt', b''])

    async def feed_and_get_status(self):
        if self.input_sock.closed:
            raise asyncio.CancelledError
        await self.input_sock.send_multipart([b'status', b''])
        try:
            result = await self.status_queue.get()
            self.status_queue.task_done()
            return msgpack.unpackb(result)
        except asyncio.CancelledError:
            return None

    async def feed_and_get_completion(self, code_text, opts):
        if self.input_sock.closed:
            raise asyncio.CancelledError
        payload = {
            'code': code_text,
        }
        payload.update(opts)
        await self.input_sock.send_multipart([
            b'complete',
            json.dumps(payload).encode('utf8'),
        ])
        try:
            result = await self.completion_queue.get()
            self.completion_queue.task_done()
            return json.loads(result)
        except asyncio.CancelledError:
            return []

    async def feed_start_service(self, service_info):
        if self.input_sock.closed:
            raise asyncio.CancelledError
        await self.input_sock.send_multipart([
            b'start-service',
            json.dumps(service_info).encode('utf8'),
        ])
        try:
            with timeout(10):
                result = await self.service_queue.get()
            self.service_queue.task_done()
            return json.loads(result)
        except asyncio.CancelledError:
            return {'status': 'failed', 'error': 'cancelled'}
        except asyncio.TimeoutError:
            return {'status': 'failed', 'error': 'timeout'}

    async def feed_shutdown_service(self, service_name: str):
        if self.input_sock.closed:
            raise asyncio.CancelledError
        await self.input_sock.send_multipart([
            b'shutdown-service',
            json.dumps(service_name).encode('utf8'),
        ])

    async def feed_service_apps(self):
        await self.input_sock.send_multipart([
            b'get-apps',
            ''.encode('utf8'),
        ])
        try:
            with timeout(10):
                result = await self.service_apps_info_queue.get()
            self.service_apps_info_queue.task_done()
            return json.loads(result)
        except asyncio.CancelledError:
            return {'status': 'failed', 'error': 'cancelled'}
        except asyncio.TimeoutError:
            return {'status': 'failed', 'error': 'timeout'}

    async def watchdog(self) -> None:
        try:
            await asyncio.sleep(self.exec_timeout)
            if self.output_queue is not None:
                # TODO: what to do if None?
                await self.output_queue.put(ResultRecord('exec-timeout', None))
        except asyncio.CancelledError:
            pass

    @staticmethod
    def aggregate_console(result: NextResult, records: Sequence[ResultRecord], api_ver: int) -> None:

        if api_ver == 1:

            stdout_items = []
            stderr_items = []
            media_items = []
            html_items = []

            for rec in records:
                if rec.msg_type == 'stdout':
                    stdout_items.append(rec.data or '')
                elif rec.msg_type == 'stderr':
                    stderr_items.append(rec.data or '')
                elif rec.msg_type == 'media' and rec.data is not None:
                    o = json.loads(rec.data)
                    media_items.append((o['type'], o['data']))
                elif rec.msg_type == 'html':
                    html_items.append(rec.data)

            result['stdout'] = ''.join(stdout_items)
            result['stderr'] = ''.join(stderr_items)
            result['media'] = media_items
            result['html'] = html_items

        elif api_ver >= 2:

            console_items: List[Tuple[ConsoleItemType, Union[str, Tuple[str, str]]]] = []
            last_stdout = io.StringIO()
            last_stderr = io.StringIO()

            for rec in records:

                if last_stdout.tell() and rec.msg_type != 'stdout':
                    console_items.append(('stdout', last_stdout.getvalue()))
                    last_stdout.seek(0)
                    last_stdout.truncate(0)
                if last_stderr.tell() and rec.msg_type != 'stderr':
                    console_items.append(('stderr', last_stderr.getvalue()))
                    last_stderr.seek(0)
                    last_stderr.truncate(0)

                if rec.msg_type == 'stdout':
                    last_stdout.write(rec.data or '')
                elif rec.msg_type == 'stderr':
                    last_stderr.write(rec.data or '')
                elif rec.msg_type == 'media' and rec.data is not None:
                    o = json.loads(rec.data)
                    console_items.append(('media', (o['type'], o['data'])))
                elif rec.msg_type in outgoing_msg_types:
                    # FIXME: currently mypy cannot handle dynamic specialization of literals.
                    console_items.append((rec.msg_type, rec.data))  # type: ignore

            if last_stdout.tell():
                console_items.append(('stdout', last_stdout.getvalue()))
            if last_stderr.tell():
                console_items.append(('stderr', last_stderr.getvalue()))

            result['console'] = console_items
            last_stdout.close()
            last_stderr.close()

        else:
            raise AssertionError('Unrecognized API version')

    async def get_next_result(self, api_ver=2, flush_timeout=2.0) -> NextResult:
        # Context: per API request
        has_continuation = ClientFeatures.CONTINUATION in self.client_features
        try:
            records = []
            result: NextResult
            assert self.output_queue is not None
            with timeout(flush_timeout if has_continuation else None):
                while True:
                    rec = await self.output_queue.get()
                    if rec.msg_type in outgoing_msg_types:
                        records.append(rec)
                    self.output_queue.task_done()
                    if rec.msg_type == 'finished':
                        data = json.loads(rec.data) if rec.data else {}
                        raise RunFinished(data)
                    elif rec.msg_type == 'clean-finished':
                        data = json.loads(rec.data) if rec.data else {}
                        raise CleanFinished(data)
                    elif rec.msg_type == 'build-finished':
                        data = json.loads(rec.data) if rec.data else {}
                        raise BuildFinished(data)
                    elif rec.msg_type == 'waiting-input':
                        opts = json.loads(rec.data) if rec.data else {}
                        raise InputRequestPending(opts)
                    elif rec.msg_type == 'exec-timeout':
                        raise ExecTimeout
        except asyncio.CancelledError:
            self.resume_output_queue()
            raise
        except asyncio.TimeoutError:
            result = {
                'runId': self.current_run_id,
                'status': 'continued',
                'exitCode': None,
                'options': None,
            }
            type(self).aggregate_console(result, records, api_ver)
            self.resume_output_queue()
            return result
        except CleanFinished as e:
            result = {
                'runId': self.current_run_id,
                'status': 'clean-finished',
                'exitCode': e.data.get('exitCode'),
                'options': None,
            }
            type(self).aggregate_console(result, records, api_ver)
            self.resume_output_queue()
            return result
        except BuildFinished as e:
            result = {
                'runId': self.current_run_id,
                'status': 'build-finished',
                'exitCode': e.data.get('exitCode'),
                'options': None,
            }
            type(self).aggregate_console(result, records, api_ver)
            self.resume_output_queue()
            return result
        except RunFinished as e:
            result = {
                'runId': self.current_run_id,
                'status': 'finished',
                'exitCode': e.data.get('exitCode'),
                'options': None,
            }
            type(self).aggregate_console(result, records, api_ver)
            self.next_output_queue()
            return result
        except ExecTimeout:
            result = {
                'runId': self.current_run_id,
                'status': 'exec-timeout',
                'exitCode': None,
                'options': None,
            }
            log.warning('Execution timeout detected on kernel '
                        f'{self.kernel_id}')
            type(self).aggregate_console(result, records, api_ver)
            self.next_output_queue()
            return result
        except InputRequestPending as e:
            result = {
                'runId': self.current_run_id,
                'status': 'waiting-input',
                'exitCode': None,
                'options': e.data,
            }
            type(self).aggregate_console(result, records, api_ver)
            self.resume_output_queue()
            return result
        except Exception:
            log.exception('unexpected error')
            raise

    async def attach_output_queue(self, run_id: Optional[str]) -> None:
        # Context: per API request
        if run_id is None:
            run_id = secrets.token_hex(16)
        assert run_id is not None
        if run_id not in self.pending_queues:
            q: asyncio.Queue[ResultRecord] = asyncio.Queue(maxsize=4096)
            activated = asyncio.Event()
            self.pending_queues[run_id] = (activated, q)
        else:
            activated, q = self.pending_queues[run_id]
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
        assert self.output_queue is q

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
        assert self.current_run_id is not None
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
            codecs.getincrementaldecoder('utf8')(errors='replace'),
            codecs.getincrementaldecoder('utf8')(errors='replace'),
        )
        while True:
            try:
                msg_type, msg_data = await self.output_sock.recv_multipart()
                try:
                    if msg_type == b'status':
                        await self.status_queue.put(msg_data)
                    elif msg_type == b'completion':
                        await self.completion_queue.put(msg_data)
                    elif msg_type == b'service-result':
                        await self.service_queue.put(msg_data)
                    elif msg_type == b'apps-result':
                        await self.service_apps_info_queue.put(msg_data)
                    elif msg_type == b'stdout':
                        if self.output_queue is None:
                            continue
                        if len(msg_data) > self.max_record_size:
                            msg_data = msg_data[:self.max_record_size]
                        await self.output_queue.put(
                            ResultRecord(
                                'stdout',
                                decoders[0].decode(msg_data),
                            ))
                    elif msg_type == b'stderr':
                        if self.output_queue is None:
                            continue
                        if len(msg_data) > self.max_record_size:
                            msg_data = msg_data[:self.max_record_size]
                        await self.output_queue.put(
                            ResultRecord(
                                'stderr',
                                decoders[1].decode(msg_data),
                            ))
                    else:
                        # Normal outputs should go to the current
                        # output queue.
                        if self.output_queue is None:
                            continue
                        await self.output_queue.put(
                            ResultRecord(
                                msg_type.decode('ascii'),
                                msg_data.decode('utf8'),
                            ))
                except asyncio.QueueFull:
                    pass
                if msg_type == b'build-finished':
                    # finalize incremental decoder
                    decoders[0].decode(b'', True)
                    decoders[1].decode(b'', True)
                elif msg_type == b'finished':
                    # finalize incremental decoder
                    decoders[0].decode(b'', True)
                    decoders[1].decode(b'', True)
                    self.finished_at = time.monotonic()
            except (asyncio.CancelledError, GeneratorExit):
                break
            except Exception:
                log.exception('unexpected error')
                break


def match_distro_data(data: Mapping[str, Any], distro: str) -> Tuple[str, Any]:
    """
    Find the latest or exactly matching entry from krunner_volumes mapping using the given distro
    string expression.

    It assumes that the keys of krunner_volumes mapping is a string concatenated with a distro
    prefix (e.g., "centos", "ubuntu") and a distro version composed of multiple integer components
    joined by single dots (e.g., "1.2.3", "18.04").
    """
    rx_ver_suffix = re.compile(r'(\d+(\.\d+)*)$')
    m = rx_ver_suffix.search(distro)
    if m is None:
        # Assume latest
        distro_prefix = distro
        distro_ver = None
    else:
        distro_prefix = distro[:-len(m.group(1))]
        distro_ver = m.group(1)

    # Check if there are static-build krunners first.
    if distro_prefix == 'alpine':
        libc_flavor = 'musl'
    else:
        libc_flavor = 'gnu'
    distro_key = f'static-{libc_flavor}'
    if volume := data.get(distro_key):
        return distro_key, volume

    # Search through the per-distro versions
    match_list = [
        (distro_key, value)
        for distro_key, value in data.items()
        if distro_key.startswith(distro_prefix)
    ]

    def _extract_version(item: Tuple[str, Any]) -> Tuple[int, ...]:
        m = rx_ver_suffix.search(item[0])
        if m is not None:
            return tuple(map(int, m.group(1).split('.')))
        return (0,)

    match_list = sorted(
        match_list,
        key=_extract_version,
        reverse=True)
    if match_list:
        if distro_ver is None:
            return match_list[0]
        for distro_key, value in match_list:
            if distro_key == distro:
                return (distro_key, value)
        return match_list[0]  # fallback to the latest of its kind
    raise UnsupportedBaseDistroError(distro)
