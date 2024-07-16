from __future__ import annotations

import asyncio
import concurrent.futures
import enum
import json
import logging
import os
import resource
import signal
import sys
import time
import urllib.error
import urllib.request
import uuid
from abc import ABCMeta, abstractmethod
from functools import partial
from pathlib import Path
from typing import (
    Awaitable,
    ClassVar,
    Dict,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

import janus
import msgpack
import zmq
from jupyter_client.asynchronous.client import AsyncKernelClient
from jupyter_client.kernelspec import KernelSpecManager
from jupyter_client.manager import AsyncKernelManager

from .compat import current_loop
from .intrinsic import (
    init_sshd_service,
    prepare_sshd_service,
    prepare_ttyd_service,
)
from .jupyter_client import aexecute_interactive
from .logging import BraceStyleAdapter, setup_logger
from .service import ServiceParser
from .utils import TracebackSourceFilter, scan_proc_stats, wait_local_port_open

logger = logging.getLogger()
logger.addFilter(TracebackSourceFilter(str(Path(__file__).parent)))
log = BraceStyleAdapter(logger)

TReturn = TypeVar("TReturn")


class FailureSentinel(enum.Enum):
    TOKEN = 0


FAILURE = FailureSentinel.TOKEN


class HealthStatus(enum.Enum):
    HEALTHY = 0
    UNHEALTHY = 1
    UNDETERMINED = 2


async def pipe_output(stream, outsock, target, log_fd):
    assert target in ("stdout", "stderr")
    target = target.encode("ascii")
    console_fd = sys.stdout.fileno() if target == "stdout" else sys.stderr.fileno()
    loop = current_loop()
    try:
        while True:
            data = await stream.read(4096)
            if not data:
                break
            await asyncio.gather(
                loop.run_in_executor(None, os.write, console_fd, data),
                loop.run_in_executor(None, os.write, log_fd, data),
                outsock.send_multipart([target, data]),
                return_exceptions=True,
            )
    except asyncio.CancelledError:
        pass
    except Exception:
        log.exception("unexpected error")


async def terminate_and_wait(proc: asyncio.subprocess.Process, timeout: float = 2.0) -> None:
    try:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
    except ProcessLookupError:
        pass


def glob_path(base: Path | str, pattern: str) -> Path | None:
    paths = [*Path(base).glob(pattern)]
    if paths:
        return paths[0]
    return None


def promote_path(path_env: str, path_to_promote: Path | str | None) -> str:
    if not path_to_promote:
        return path_env
    paths = path_env.split(":")
    path_to_promote = os.fsdecode(path_to_promote)
    result_paths = [p for p in paths if path_to_promote != p]
    result_paths.insert(0, path_to_promote)
    return ":".join(result_paths)


class BaseRunner(metaclass=ABCMeta):
    log_prefix: ClassVar[str] = "generic-kernel"
    log_queue: janus.Queue[logging.LogRecord]
    task_queue: asyncio.Queue[Awaitable[None]]
    default_runtime_path: ClassVar[Optional[str]] = None
    default_child_env: ClassVar[dict[str, str]] = {
        "LANG": "C.UTF-8",
        "HOME": "/home/work",
        "TERM": "xterm",
        "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", ""),
        "LD_PRELOAD": os.environ.get("LD_PRELOAD", ""),
        "SSH_AUTH_SOCK": os.environ.get("SSH_AUTH_SOCK", ""),
        "SSH_AGENT_PID": os.environ.get("SSH_AGENT_PID", ""),
    }
    default_child_env_path = ":".join([
        "/usr/local/sbin",
        "/usr/local/bin",
        "/usr/sbin",
        "/usr/bin",
        "/sbin",
        "/bin",
    ])
    default_child_env_shell = "/bin/ash" if Path("/bin/ash").is_file() else "/bin/bash"
    jupyter_kspec_name: ClassVar[str] = ""
    kernel_mgr: Optional[AsyncKernelManager] = None
    kernel_client: Optional[AsyncKernelClient] = None

    child_env: MutableMapping[str, str]
    subproc: Optional[asyncio.subprocess.Process]
    service_parser: Optional[ServiceParser]
    runtime_path: Path

    services_running: Dict[str, asyncio.subprocess.Process]

    intrinsic_host_ports_mapping: Mapping[str, int]

    _build_success: Optional[bool]

    # Set by subclasses.
    user_input_queue: Optional[asyncio.Queue[str]]

    _main_task: asyncio.Task
    _run_task: asyncio.Task
    _health_check_task: Optional[asyncio.Task]

    def __init__(self, runtime_path: Path) -> None:
        self.subproc = None
        self.runtime_path = runtime_path
        self.child_env = {**os.environ, **self.default_child_env}
        # set some defaults only when they are missing from the image
        if "PATH" not in self.child_env:
            self.child_env["PATH"] = self.default_child_env_path
        if "SHELL" not in self.child_env:
            self.child_env["SHELL"] = self.default_child_env_shell
        config_dir = Path("/home/config")
        try:
            evdata = (config_dir / "environ.txt").read_text()
            for line in evdata.splitlines():
                k, v = line.split("=", 1)
                self.child_env[k] = v
                os.environ[k] = v
        except FileNotFoundError:
            pass
        except Exception:
            log.exception("Reading /home/config/environ.txt failed!")

        path_env = self.child_env["PATH"]
        if Path("/usr/local/cuda/bin").is_dir():
            path_env = promote_path(path_env, "/usr/local/cuda/bin")
        if Path("/usr/local/nvidia/bin").is_dir():
            path_env = promote_path(path_env, "/usr/local/nvidia/bin")
        if Path("/home/linuxbrew/.linuxbrew").is_dir():
            path_env = promote_path(path_env, "/home/linuxbrew/.linuxbrew/bin")
        path_env = promote_path(path_env, "/home/work/.local/bin")
        self.child_env["PATH"] = path_env

        self.started_at: float = time.monotonic()
        self.services_running = {}

        self.intrinsic_host_ports_mapping = {}

        # If the subclass implements interatcive user inputs, it should set a
        # asyncio.Queue-like object to self.user_input_queue in the
        # init_with_loop() method.
        self.user_input_queue = None

        # build status tracker to skip the execute step
        self._build_success = None

        # A reference to the health check task for model-serving kernels.
        # It will be cancelled gracefully on kernel shutdown.
        self._health_check_task = None

    async def _init(self, cmdargs) -> None:
        self.cmdargs = cmdargs
        loop = current_loop()
        self._service_lock = asyncio.Lock()

        # Initialize event loop.
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        loop.set_default_executor(executor)

        self.zctx = zmq.asyncio.Context()

        intrinsic_host_ports_mapping_path = Path("/home/config/intrinsic-ports.json")
        if intrinsic_host_ports_mapping_path.is_file():
            intrinsic_host_ports_mapping = json.loads(
                await asyncio.get_running_loop().run_in_executor(
                    None,
                    lambda: intrinsic_host_ports_mapping_path.read_text(),
                )
            )
            self.intrinsic_host_ports_mapping = intrinsic_host_ports_mapping

        insock_port = self.intrinsic_host_ports_mapping.get("replin", "2000")
        outsock_port = self.intrinsic_host_ports_mapping.get("replout", "2001")
        self.insock = self.zctx.socket(zmq.PULL)
        self.insock.bind(f"tcp://*:{insock_port}")
        print(f"binding to tcp://*:{insock_port}")
        self.outsock = self.zctx.socket(zmq.PUSH)
        self.outsock.bind(f"tcp://*:{outsock_port}")
        print(f"binding to tcp://*:{outsock_port}")

        self.log_queue = janus.Queue()
        self.task_queue = asyncio.Queue()
        self.init_done = asyncio.Event()

        setup_logger(self.log_queue.sync_q, self.log_prefix, cmdargs.debug)
        self._log_task = loop.create_task(self._handle_logs())
        await asyncio.sleep(0)

        self.service_parser = ServiceParser({
            "runtime_path": str(self.runtime_path),
        })
        service_def_folder = Path("/etc/backend.ai/service-defs")
        if service_def_folder.is_dir():
            await self.service_parser.parse(service_def_folder)
            log.debug("Loaded new-style service definitions.")

        self._main_task = loop.create_task(self.main_loop(cmdargs))
        self._run_task = loop.create_task(self.run_tasks())

    async def _shutdown(self) -> None:
        try:
            self.insock.close()
            log.debug("shutting down...")
            self._run_task.cancel()
            self._main_task.cancel()
            await self._run_task
            await self._main_task
            if health_check_task := self._health_check_task:
                health_check_task.cancel()
                await health_check_task
            log.debug("terminating service processes...")
            running_procs = [*self.services_running.values()]
            async with self._service_lock:
                await asyncio.gather(
                    *(terminate_and_wait(proc) for proc in running_procs),
                    return_exceptions=True,
                )
                await asyncio.sleep(0.01)
            log.debug("terminated.")
        finally:
            # allow remaining logs to be flushed.
            await asyncio.sleep(0.1)
            try:
                if self.outsock:
                    self.outsock.close()
                await self._shutdown_jupyter_kernel()
            finally:
                self._log_task.cancel()
                await self._log_task

    async def _init_jupyter_kernel(self) -> None:
        """Detect ipython kernel spec for backend.ai and start it if found.

        Called after `init_with_loop`. `jupyter_kspec_name` should be defined to
        initialize jupyter kernel.
        """
        # Make inline backend defaults in Matplotlib.
        kconfigdir = Path("/home/work/.ipython/profile_default/")
        kconfigdir.mkdir(parents=True, exist_ok=True)
        kconfig_file = kconfigdir / "ipython_kernel_config.py"
        kconfig_file.write_text("c.InteractiveShellApp.matplotlib = 'inline'")

        kernelspec_mgr = KernelSpecManager()
        kernelspec_mgr.ensure_native_kernel = False
        kspecs = kernelspec_mgr.get_all_specs()
        for kname in kspecs:
            if self.jupyter_kspec_name in kname:
                log.debug("starting " + kname + " kernel...")
                self.kernel_mgr = AsyncKernelManager(kernel_name=kname)
                await self.kernel_mgr.start_kernel()
                if not await self.kernel_mgr.is_alive():
                    log.error("jupyter query mode is disabled: failed to start jupyter kernel")
                else:
                    self.kernel_client = self.kernel_mgr.client()  # type: ignore
                    assert self.kernel_client is not None
                    self.kernel_client.start_channels(shell=True, iopub=True, stdin=True, hb=True)
                    try:
                        await self.kernel_client.wait_for_ready(timeout=10)
                        # self.init_jupyter_kernel()
                    except RuntimeError:
                        # Clean up for client and kernel will be done in `shutdown`.
                        log.error("jupyter channel is not active!")
                        self.kernel_mgr = None
                break
        else:
            log.debug("jupyter query mode is not available: no jupyter kernelspec found")
            self.kernel_mgr = None

    async def _shutdown_jupyter_kernel(self):
        if self.kernel_mgr and await self.kernel_mgr.is_alive():
            assert self.kernel_client is not None
            log.info("shutting down " + self.jupyter_kspec_name + " kernel...")
            await self.kernel_mgr.shutdown_kernel()
            self.kernel_client.stop_channels()
            assert not await self.kernel_mgr.is_alive(), "ipykernel failed to shutdown"

    async def _handle_exception(
        self, coro: Awaitable[TReturn], help_text: str | None = None
    ) -> TReturn | FailureSentinel:
        try:
            return await coro
        except Exception as e:
            match e:
                case FileNotFoundError():
                    msg = "File not found: {!r}"
                    if help_text:
                        msg += f" ({help_text})"
                    log.exception(msg, e.filename)
                case _:
                    msg = "Unexpected error!"
                    if help_text:
                        msg += f" ({help_text})"
                    log.exception(msg)
            return FAILURE

    async def _init_with_loop(self) -> None:
        if self.init_done is not None:
            self.init_done.clear()
        try:
            ret = await self._handle_exception(
                self.init_with_loop(),
                "Check the image configs/labels like `ai.backend.runtime-path`",
            )
            if ret is FAILURE:
                log.warning(
                    "We are skipping the runtime-specific initialization failure, "
                    "and the container may not work as expected."
                )
            await self._handle_exception(
                init_sshd_service(self.child_env),
                "Verify agent installation with the embedded prebuilt binaries",
            )
        finally:
            if self.init_done is not None:
                self.init_done.set()

    @abstractmethod
    async def init_with_loop(self) -> None:
        """Initialize after the event loop is created."""

    async def _clean(self, clean_cmd: Optional[str]) -> None:
        ret = 0
        try:
            if clean_cmd is None or clean_cmd == "":
                # skipped
                return
            elif clean_cmd == "*":
                ret = await self.clean_heuristic()
            else:
                ret = await self.run_subproc(clean_cmd)
        except Exception:
            log.exception("unexpected error")
            ret = -1
        finally:
            await asyncio.sleep(0.01)  # extra delay to flush logs
            payload = json.dumps({
                "exitCode": ret,
            }).encode("utf8")
            await self.outsock.send_multipart([b"clean-finished", payload])

    async def clean_heuristic(self) -> int:
        # it should not do anything by default.
        return 0

    async def _bootstrap(self, script_path: Path) -> None:
        log.info("Running the user bootstrap script...")
        ret = 0
        try:
            ret = await self.run_subproc(["/bin/sh", str(script_path)])
        except Exception:
            log.exception("unexpected error while executing the user bootstrap script")
            ret = -1
        finally:
            await asyncio.sleep(0.01)  # extra delay to flush logs
            log.info("The user bootstrap script has exited with code {}", ret)

    async def _build(self, build_cmd: Optional[str]) -> None:
        ret = 0
        try:
            if build_cmd is None or build_cmd == "":
                # skipped
                return
            elif build_cmd == "*":
                if Path("Makefile").is_file():
                    ret = await self.run_subproc("make")
                else:
                    ret = await self.build_heuristic()
            else:
                ret = await self.run_subproc(build_cmd)
        except Exception:
            log.exception("unexpected error")
            ret = -1
        finally:
            await asyncio.sleep(0.01)  # extra delay to flush logs
            self._build_success = ret == 0
            payload = json.dumps({
                "exitCode": ret,
            }).encode("utf8")
            await self.outsock.send_multipart([b"build-finished", payload])

    @abstractmethod
    async def build_heuristic(self) -> int:
        """Process build step."""

    async def _execute(self, exec_cmd: str) -> None:
        ret = 0
        try:
            if exec_cmd is None or exec_cmd == "":
                # skipped
                return
            elif exec_cmd == "*":
                ret = await self.execute_heuristic()
            else:
                ret = await self.run_subproc(exec_cmd, batch=True)
        except Exception:
            log.exception("unexpected error")
            ret = -1
        finally:
            await asyncio.sleep(0.01)  # extra delay to flush logs
            payload = json.dumps({
                "exitCode": ret,
            }).encode("utf8")
            await self.outsock.send_multipart([b"finished", payload])

    @abstractmethod
    async def execute_heuristic(self) -> int:
        """Process execute step."""

    async def _query(self, code_text: str) -> None:
        ret = 0
        try:
            ret = await self.query(code_text)
        except Exception:
            log.exception("unexpected error")
            ret = -1
        finally:
            payload = json.dumps({
                "exitCode": ret,
            }).encode("utf8")
            await self.outsock.send_multipart([b"finished", payload])

    async def query(self, code_text) -> int:
        """Run user's code in query mode.

        The default interface is jupyter kernel. To use different interface,
        `Runner` subclass should override this method.
        """
        if not hasattr(self, "kernel_mgr") or self.kernel_mgr is None:
            log.error("query mode is disabled: failed to start jupyter kernel")
            return 127

        assert self.kernel_client is not None
        log.debug("executing in query mode...")

        async def output_hook(msg):
            content = msg.get("content", "")
            if msg["msg_type"] == "stream":
                # content['name'] will be 'stdout' or 'stderr'.
                await self.outsock.send_multipart([
                    content["name"].encode("ascii"),
                    content["text"].encode("utf-8"),
                ])
            elif msg["msg_type"] == "error":
                tbs = "\n".join(content["traceback"])
                await self.outsock.send_multipart([b"stderr", tbs.encode("utf-8")])
            elif msg["msg_type"] in ["execute_result", "display_data"]:
                data = content["data"]
                if len(data) < 1:
                    return
                if len(data) > 1:
                    data.pop("text/plain", None)
                dtype, dval = list(data.items())[0]

                if dtype == "text/plain":
                    await self.outsock.send_multipart([b"stdout", dval.encode("utf-8")])
                elif dtype == "text/html":
                    await self.outsock.send_multipart([b"media", dval.encode("utf-8")])
                # elif dtype == 'text/markdown':
                #     NotImplementedError
                # elif dtype == 'text/latex':
                #     NotImplementedError
                # elif dtype in ['application/json', 'application/javascript']:
                #     NotImplementedError
                elif dtype in ["image/png", "image/jpeg"]:
                    await self.outsock.send_multipart([
                        b"media",
                        json.dumps({
                            "type": dtype,
                            "data": f"data:{dtype};base64,{dval}",
                        }).encode("utf-8"),
                    ])
                elif dtype == "image/svg+xml":
                    await self.outsock.send_multipart([
                        b"media",
                        json.dumps({"type": dtype, "data": dval}).encode("utf8"),
                    ])

        async def stdin_hook(msg):
            assert self.kernel_client is not None
            assert self.user_input_queue is not None
            if msg["msg_type"] == "input_request":
                prompt = msg["content"]["prompt"]
                password = msg["content"]["password"]
                if prompt:
                    await self.outsock.send_multipart([b"stdout", prompt.encode("utf-8")])
                await self.outsock.send_multipart([
                    b"waiting-input",
                    json.dumps({"is_password": password}).encode("utf-8"),
                ])
                user_input = await self.user_input_queue.get()
                self.kernel_client.input(user_input)

        # Run jupyter kernel's blocking execution method in an executor pool.
        allow_stdin = False if self.user_input_queue is None else True
        stdin_hook = None if self.user_input_queue is None else stdin_hook  # type: ignore
        try:
            await aexecute_interactive(
                self.kernel_client,
                code_text,
                timeout=None,
                output_hook=output_hook,
                allow_stdin=allow_stdin,
                stdin_hook=stdin_hook,
            )
        except Exception as e:
            log.exception(str(e))
            return 127
        return 0

    async def _complete(self, completion_data) -> Sequence[str]:
        result: Sequence[str] = []
        try:
            result = await self.complete(completion_data)
        except Exception:
            log.exception("unexpected error")
        finally:
            return result

    async def complete(self, completion_data) -> Sequence[str]:
        """Return the list of strings to be shown in the auto-complete list.

        The default interface is jupyter kernel. To use different interface,
        `Runner` subclass should override this method.
        """
        # TODO: implement with jupyter_client
        """
        matches = []
        self.outsock.send_multipart([
            b'completion',
            json.dumps(matches).encode('utf8'),
        ])
        """
        # if hasattr(self, 'kernel_mgr') and self.kernel_mgr is not None:
        #     self.kernel_mgr.complete(data, len(data))
        # else:
        #     return []
        return []

    async def _interrupt(self):
        try:
            if self.subproc:
                self.subproc.send_signal(signal.SIGINT)
                return
            return await self.interrupt()
        except Exception:
            log.exception("unexpected error")
        finally:
            # this is a unidirectional command -- no explicit finish!
            pass

    async def interrupt(self):
        """Interrupt the running user code (only called for query-mode).

        The default interface is jupyter kernel. To use different interface,
        `Runner` subclass should implement its own `complete` method.
        """
        if hasattr(self, "kernel_mgr") and self.kernel_mgr is not None:
            await self.kernel_mgr.interrupt_kernel()

    async def log_oom(self):
        log.warning("Out-of-memory detected!")
        prev_pid_set = {}
        for history in self._pid_set_history:  # merge the history
            prev_pid_set.update(history)
        for _ in range(30):
            current_pid_set = scan_proc_stats()
            terminated_pid_list = sorted(set(prev_pid_set.keys()) - set(current_pid_set.keys()))
            if not terminated_pid_list:
                await asyncio.sleep(0.5)
                continue
            else:
                break
        else:
            log.warning("failed to get the information of oom-killed processes")
            return
        pgsize = resource.getpagesize()
        for pid, pstat in map(lambda p: (p, prev_pid_set[p]), terminated_pid_list):
            process_tree = []
            count = 0
            while True:
                if count > 0:
                    indent = ("   " * (count - 1)) + "└─ "
                else:
                    indent = ""
                cmdline = pstat["cmdline"].replace(b"\0", b" ").decode("utf8")
                elapsed_time = "{:,.2f}".format(time.monotonic() - pstat["starttime"])
                vm_size = "{:,}".format(pstat["vsize"] // (2**20))
                rss = "{:,}".format((pstat["rss"] * pgsize) // (2**20))
                process_tree.append(
                    f"{indent}{pid} (running for {elapsed_time}s, vm: {vm_size}m, rss:"
                    f" {rss}m): {cmdline}"
                )
                ppid = pstat["ppid"]
                if ppid == 0 or ppid == pid:
                    break
                pid = ppid
                pstat = prev_pid_set[ppid]
                count += 1
            log.warning(
                "detected potentially oom-killed process:\n{}",
                "\n".join(process_tree),
            )

    async def log_event(self, data):
        match data["type"]:
            case "oom":
                await self.log_oom()
            case _:
                log.info(
                    "Agent-notified event: {}",
                    data,
                )

    async def _send_status(self):
        data = {
            "started_at": self.started_at,
        }
        await self.outsock.send_multipart([
            b"status",
            msgpack.packb(data, use_bin_type=True),
        ])

    @abstractmethod
    async def start_service(self, service_info):
        """Start an application service daemon."""
        return None, {}

    async def start_model_service(self, model_info):
        assert self.service_parser is not None
        model_service_info = model_info.get("service")
        result = {}
        started = False
        try:
            if model_service_info is None:
                result = {"status": "failed", "error": "service info not provided"}
                return
            service_name = f"{model_info['name']}-{model_service_info['port']}"
            self.service_parser.add_model_service(service_name, model_service_info)
            service_info = {
                "name": service_name,
                "port": model_service_info["port"],
                "ports": [model_service_info["port"]],
                "protocol": "http",
                "options": {},
            }
            result = await self._start_service(
                service_info, cwd=model_info["model_path"], do_not_wait=True
            )
            started = result["status"] == "running" or result["status"] == "started"
        finally:
            if not started:
                result = {"status": "failed", "error": "service failed to start"}
            await self.outsock.send_multipart([
                b"model-service-result",
                json.dumps(result).encode("utf8"),
            ])
            if started:
                if model_service_info.get("health_check"):
                    self._health_check_task = asyncio.create_task(
                        self.check_model_health(model_info["name"], model_service_info)
                    )
                else:
                    await self.outsock.send_multipart([
                        b"model-service-status",
                        json.dumps({"model_name": model_info["name"], "is_healthy": True}).encode(
                            "utf8"
                        ),
                    ])

    async def check_model_health(self, model_name, model_service_info):
        health_check_info = model_service_info.get("health_check")
        health_check_endpoint = (
            f"http://localhost:{model_service_info['port']}{health_check_info['path']}"
        )
        retries = 0
        current_health_status = HealthStatus.UNDETERMINED
        while True:
            new_health_status = HealthStatus.UNHEALTHY
            try:
                async with asyncio.timeout(health_check_info["max_wait_time"]):
                    try:
                        resp = await asyncio.get_running_loop().run_in_executor(
                            None, urllib.request.urlopen, health_check_endpoint
                        )
                        if resp.status == health_check_info["expected_status_code"]:
                            new_health_status = HealthStatus.HEALTHY
                    except urllib.error.URLError:
                        pass
                    # falling to here means that health check has failed, so just wait until
                    # timeout is fired to fill out the gap between max_wait_time and actual time elapsed
                    await asyncio.sleep(health_check_info["max_wait_time"])
            except asyncio.TimeoutError:
                pass
            finally:
                if (
                    new_health_status == HealthStatus.HEALTHY
                    and current_health_status != HealthStatus.HEALTHY
                ):
                    current_health_status = HealthStatus.HEALTHY
                    retries = 0
                    log.info("check_model_health(): new status -> healthy")
                    await self.outsock.send_multipart([
                        b"model-service-status",
                        json.dumps({"model_name": model_name, "is_healthy": True}).encode("utf8"),
                    ])
                elif new_health_status == HealthStatus.UNHEALTHY:
                    if (
                        retries > health_check_info["max_retries"]
                        and current_health_status != HealthStatus.UNHEALTHY
                    ):
                        current_health_status = HealthStatus.UNHEALTHY
                        log.info("check_model_health(): new status -> unhealthy")
                        await self.outsock.send_multipart([
                            b"model-service-status",
                            json.dumps({"model_name": model_name, "is_healthy": False}).encode(
                                "utf8"
                            ),
                        ])
                    retries += 1

    async def _start_service_and_feed_result(self, service_info):
        result = await self._start_service(service_info)
        await self.outsock.send_multipart([
            b"service-result",
            json.dumps(result).encode("utf8"),
        ])

    async def _start_service(self, service_info, *, cwd: Optional[str] = None, do_not_wait=False):
        error_reason = None
        try:
            async with self._service_lock:
                try:
                    if service_info["protocol"] == "preopen":
                        # skip subprocess spawning as we assume the user runs it manually.
                        return {"status": "started"}
                    if service_info["name"] in self.services_running:
                        return {"status": "running"}
                    if service_info["protocol"] == "pty":
                        error_reason = "not implemented yet"
                        return {"status": "failed", "error": error_reason}
                    _cwd = Path.cwd()
                    if cwd:
                        _cwd = Path(cwd)
                    cmdargs: Optional[Sequence[Union[str, os.PathLike]]]
                    env: Mapping[str, str]
                    cmdargs, env = None, {}
                    if service_info["name"] == "ttyd":
                        cmdargs, env = await prepare_ttyd_service(service_info)
                    elif service_info["name"] == "sshd":
                        cmdargs, env = await prepare_sshd_service(service_info)
                    elif self.service_parser is not None:
                        self.service_parser.variables["ports"] = service_info["ports"]
                        cmdargs, env = await self.service_parser.start_service(
                            service_info["name"],
                            self.child_env.keys(),
                            service_info["options"],
                        )
                    if cmdargs is None:
                        # fall-back to legacy service routine
                        start_info = await self.start_service(service_info)
                        if start_info is None:
                            cmdargs, env = None, {}
                        elif len(start_info) == 3:
                            cmdargs, env, _cwd = start_info
                        elif len(start_info) == 2:
                            cmdargs, env = start_info
                    if cmdargs is None:
                        # still not found?
                        error_reason = "unsupported service: {0}".format(service_info["name"])
                        return {
                            "status": "failed",
                            "error": error_reason,
                        }
                    log.debug("cmdargs: {0}", cmdargs)
                    log.debug("env: {0}", env)
                    service_env = {**self.child_env, **env}
                    # avoid conflicts with Python binary used by service apps.
                    if "LD_LIBRARY_PATH" in service_env:
                        service_env["LD_LIBRARY_PATH"] = service_env["LD_LIBRARY_PATH"].replace(
                            "/opt/backend.ai/lib:", ""
                        )
                    try:
                        proc = await asyncio.create_subprocess_exec(
                            *map(str, cmdargs),
                            env=service_env,
                            cwd=_cwd,
                        )
                        self.services_running[service_info["name"]] = proc
                        asyncio.create_task(self._wait_service_proc(service_info["name"], proc))
                        if not do_not_wait:
                            async with asyncio.timeout(5.0):
                                await wait_local_port_open(service_info["port"])
                        log.info(
                            "Service {} has started (pid: {}, port: {})",
                            service_info["name"],
                            proc.pid,
                            service_info["port"],
                        )
                        return {"status": "started"}
                    except asyncio.CancelledError:
                        # This may happen if the service process gets started but it fails to
                        # open the port and then terminates (with an error).
                        error_reason = f"the process did not start properly: {cmdargs[0]}"
                        return {
                            "status": "failed",
                            "error": error_reason,
                        }
                    except asyncio.TimeoutError:
                        # Takes too much time to open a local port.
                        if service_info["name"] in self.services_running:
                            await terminate_and_wait(proc, timeout=10.0)
                            self.services_running.pop(service_info["name"], None)
                            error_reason = (
                                f"opening the service port timed out: {service_info['name']}"
                            )
                        else:
                            error_reason = "TimeoutError (unknown)"
                        return {
                            "status": "failed",
                            "error": error_reason,
                        }
                    except PermissionError:
                        error_reason = f"the target file is not executable: {cmdargs[0]}"
                        return {
                            "status": "failed",
                            "error": error_reason,
                        }
                    except FileNotFoundError:
                        error_reason = f"the executable file is not found: {cmdargs[0]}"
                        return {
                            "status": "failed",
                            "error": error_reason,
                        }
                except Exception as e:
                    log.exception("start_service: unexpected error")
                    error_reason = repr(e)
                    return {
                        "status": "failed",
                        "error": error_reason,
                    }
        finally:
            if error_reason:
                log.warn("failed to start model service {}: {}", service_info["name"], error_reason)

    async def _wait_service_proc(
        self,
        service_name: str,
        proc: asyncio.subprocess.Process,
    ) -> None:
        exitcode = await proc.wait()
        log.info(
            f"Service {service_name} (pid: {proc.pid}) has terminated with exit code: {exitcode}"
        )
        self.services_running.pop(service_name, None)

    async def run_subproc(self, cmd: Union[str, List[str]], batch: bool = False):
        """A thin wrapper for an external command."""
        loop = current_loop()
        if Path("/home/work/.logs").is_dir():
            kernel_id = os.environ["BACKENDAI_KERNEL_ID"]
            kernel_id_hex = uuid.UUID(kernel_id).hex
            log_path = Path(
                "/home/work/.logs/task/"
                f"{kernel_id_hex[:2]}/{kernel_id_hex[2:4]}/{kernel_id_hex[4:]}.log",
            )
            log_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            log_path = Path(os.path.devnull)
        try:
            # errors like "command not found" is handled by the spawned shell.
            # (the subproc will terminate immediately with return code 127)
            if isinstance(cmd, (list, tuple)):
                exec_func = partial(asyncio.create_subprocess_exec, *map(str, cmd))
            else:
                exec_func = partial(asyncio.create_subprocess_shell, str(cmd))
            pipe_opts = {}
            pipe_opts["stdout"] = asyncio.subprocess.PIPE
            pipe_opts["stderr"] = asyncio.subprocess.PIPE
            with open(log_path, "ab") as log_out:
                env = {**self.child_env}
                if batch:
                    env["_BACKEND_BATCH_MODE"] = "1"
                proc = await exec_func(
                    env=env,
                    stdin=None,
                    **pipe_opts,
                )
                self.subproc = proc
                pipe_tasks = [
                    loop.create_task(
                        pipe_output(proc.stdout, self.outsock, "stdout", log_out.fileno())
                    ),
                    loop.create_task(
                        pipe_output(proc.stderr, self.outsock, "stderr", log_out.fileno())
                    ),
                ]
                retcode = await proc.wait()
                await asyncio.gather(*pipe_tasks)
            return retcode
        except Exception:
            log.exception("unexpected error")
            return -1
        finally:
            self.subproc = None

    async def shutdown(self):
        pass

    async def _shutdown_service(self, service_name: str):
        try:
            async with self._service_lock:
                if service_name in self.services_running:
                    await terminate_and_wait(self.services_running[service_name])
                    self.services_running.pop(service_name, None)
        except Exception:
            log.exception("unexpected error (shutdown_service)")

    async def handle_user_input(self, reader, writer):
        try:
            if self.user_input_queue is None:
                writer.write(b"<user-input is unsupported>")
            else:
                await self.outsock.send_multipart([b"waiting-input", b""])
                text = await self.user_input_queue.get()
                writer.write(text.encode("utf8"))
            await writer.drain()
            writer.close()
        except Exception:
            log.exception("unexpected error (handle_user_input)")

    async def run_tasks(self):
        while True:
            try:
                coro = await self.task_queue.get()

                if (
                    self._build_success is not None
                    and coro.func == self._execute
                    and not self._build_success
                ):
                    self._build_success = None
                    # skip exec step with "command not found" exit code
                    payload = json.dumps({
                        "exitCode": 127,
                    }).encode("utf8")
                    await self.outsock.send_multipart([b"finished", payload])
                    self.task_queue.task_done()
                    continue

                await coro()
                self.task_queue.task_done()
            except asyncio.CancelledError:
                break

    async def _handle_logs(self):
        log_queue = self.log_queue.async_q
        try:
            while True:
                rec = await log_queue.get()
                await self.outsock.send_multipart(rec)
                log_queue.task_done()
        except asyncio.CancelledError:
            self.log_queue.close()
            await self.log_queue.wait_closed()

    async def _get_apps(self, service_name):
        result = {"status": "done", "data": []}
        if self.service_parser is not None:
            if service_name:
                apps = await self.service_parser.get_apps(selected_service=service_name)
            else:
                apps = await self.service_parser.get_apps()
            result["data"] = apps
        await self.outsock.send_multipart([
            b"apps-result",
            json.dumps(result).encode("utf8"),
        ])

    async def _monitor_processes(self):
        while True:
            self._pid_set_history.append(scan_proc_stats())
            if len(self._pid_set_history) > 2:
                self._pid_set_history.pop(0)
            try:
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                return

    async def main_loop(self, cmdargs):
        log.debug("starting user input server...")
        user_input_server = await asyncio.start_unix_server(
            self.handle_user_input, "/tmp/bai-user-input.sock"
        )
        log.debug("initializing krunner...")
        await self._init_with_loop()
        log.debug("initializing jupyter kernel...")
        await self._init_jupyter_kernel()

        user_bootstrap_path = Path("/home/work/bootstrap.sh")
        if user_bootstrap_path.is_file():
            log.debug("running user bootstrap script...")
            await self._bootstrap(user_bootstrap_path)

        self._pid_set_history = []
        monitor_proc_task = asyncio.create_task(self._monitor_processes())

        log.debug("starting intrinsic services: sshd, ttyd ...")
        intrinsic_spawn_coros = []
        intrinsic_spawn_coros.append(
            self._start_service(
                {
                    "name": "sshd",
                    "port": self.intrinsic_host_ports_mapping.get("sshd", 2200),
                    "protocol": "tcp",
                },
            )
        )
        intrinsic_spawn_coros.append(
            self._start_service(
                {
                    "name": "ttyd",
                    "port": self.intrinsic_host_ports_mapping.get("ttyd", 7681),
                    "protocol": "http",
                },
            )
        )
        results = await asyncio.gather(*intrinsic_spawn_coros, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                log.exception(
                    "error during starting intrinsic services",
                    exc_info=result,
                )

        log.debug("start serving...")
        while True:
            try:
                data = await self.insock.recv_multipart()
                if len(data) != 2:
                    # maybe some garbage data
                    continue
                op_type = data[0].decode("ascii")
                text = data[1].decode("utf8")
                if op_type == "clean":
                    await self.task_queue.put(partial(self._clean, text))
                if op_type == "build":  # batch-mode step 1
                    await self.task_queue.put(partial(self._build, text))
                elif op_type == "exec":  # batch-mode step 2
                    await self.task_queue.put(partial(self._execute, text))
                elif op_type == "code":  # query-mode
                    await self.task_queue.put(partial(self._query, text))
                elif op_type == "input":  # interactive input
                    if self.user_input_queue is not None:
                        await self.user_input_queue.put(text)
                elif op_type == "complete":  # auto-completion
                    data = json.loads(text)
                    await self._complete(data)
                elif op_type == "interrupt":
                    await self._interrupt()
                elif op_type == "status":
                    await self._send_status()
                elif op_type == "event":
                    data = json.loads(text)
                    asyncio.create_task(self.log_event(data))
                elif op_type == "start-model-service":  # activate a service port
                    data = json.loads(text)
                    asyncio.create_task(self.start_model_service(data))
                elif op_type == "start-service":  # activate a service port
                    data = json.loads(text)
                    asyncio.create_task(self._start_service_and_feed_result(data))
                elif op_type == "shutdown-service":  # shutdown the service by its name
                    data = json.loads(text)
                    await self._shutdown_service(data)
                elif op_type == "get-apps":
                    await self._get_apps(text)
            except asyncio.CancelledError:
                break
            except NotImplementedError:
                log.error("Unsupported operation for this kernel: {0}", op_type)
                await asyncio.sleep(0)
            except Exception:
                log.exception("main_loop: unexpected error")
                # we need to continue anyway unless we are shutting down
                continue
        user_input_server.close()
        await user_input_server.wait_closed()
        monitor_proc_task.cancel()
        await monitor_proc_task
        await self.shutdown()
