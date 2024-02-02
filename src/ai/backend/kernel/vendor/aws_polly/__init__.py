import asyncio
import ctypes
import logging
import os
import threading

import janus

from ... import BaseRunner
from .inproc import PollyInprocRunner

log = logging.getLogger()


class Runner(BaseRunner):
    log_prefix = "vendor.aws_polly-kernel"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inproc_runner = None
        self.sentinel = object()
        self.input_queue = None
        self.output_queue = None
        # NOTE: If credentials are missing,
        #       boto3 will try to use the instance role.
        self.access_key = self.child_env.get("AWS_ACCESS_KEY_ID", None)
        self.secret_key = self.child_env.get("AWS_SECRET_ACCESS_KEY", None)
        os.environ["AWS_DEFAULT_REGION"] = self.child_env.get(
            "AWS_DEFAULT_REGION", "ap-northeast-2"
        )

    async def init_with_loop(self):
        self.input_queue = janus.Queue()
        self.output_queue = janus.Queue()

    async def build_heuristic(self) -> int:
        raise NotImplementedError

    async def execute_heuristic(self) -> int:
        raise NotImplementedError

    async def query(self, code_text) -> int:
        self.ensure_inproc_runner()
        await self.input_queue.async_q.put(code_text)
        # Read the generated outputs until done
        while True:
            try:
                msg = await self.output_queue.async_q.get()
            except asyncio.CancelledError:
                break
            self.output_queue.async_q.task_done()
            if msg is self.sentinel:
                break
            self.outsock.send_multipart(msg)
        return 0

    async def complete(self, data):
        self.outsock.send_multipart([
            b"completion",
            [],
        ])

    async def interrupt(self):
        if self.inproc_runner is None:
            log.error("No user code is running!")
            return
        # A dirty hack to raise an exception inside a running thread.
        target_tid = self.inproc_runner.ident
        if target_tid not in {t.ident for t in threading.enumerate()}:
            log.error("Interrupt failed due to missing thread.")
            return
        affected_count = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(target_tid), ctypes.py_object(KeyboardInterrupt)
        )
        if affected_count == 0:
            log.error("Interrupt failed due to invalid thread identity.")
        elif affected_count > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(target_tid), ctypes.c_long(0))
            log.error("Interrupt broke the interpreter state -- recommended to reset the session.")

    async def start_service(self, service_info):
        return None, {}

    def ensure_inproc_runner(self):
        if self.inproc_runner is None:
            self.inproc_runner = PollyInprocRunner(
                self.input_queue.sync_q,
                self.output_queue.sync_q,
                self.sentinel,
                self.access_key,
                self.secret_key,
            )
            self.inproc_runner.start()
