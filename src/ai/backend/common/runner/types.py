import asyncio
import logging
from collections.abc import Coroutine, Sequence
from typing import Any

from ai.backend.common.observer.types import AbstractObserver
from ai.backend.common.resource.types import AbstractResource
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


class Runner:
    """
    Runner is a utility class that manages the lifecycle of resources and observers.
    It sets up resources, starts observers, and cleans up resources when closed.
    Parameters
    ----------
    resources : Sequence[AbstractResource]
        A sequence of resources to be managed by the runner.
        Each resource should implement the AbstractResource interface.

    Examples
    --------
    runner = Runner(resources=[MyResource(), AnotherResource()])
    await runner.register_observer(MyObserver())
    await runner.start()
    """

    _resources: Sequence[AbstractResource]
    _closed_event: asyncio.Event
    _tasks: set[asyncio.Task[None]]

    def __init__(self, resources: Sequence[AbstractResource]) -> None:
        self._resources = resources
        self._closed_event = asyncio.Event()
        self._tasks = set()

    def _track(self, coro: Coroutine[Any, Any, None]) -> None:
        # The event loop only keeps weak references to tasks, so a fire-and-forget
        # task may be garbage collected mid-execution. Hold a strong reference until
        # it completes, then drop it via the done callback.
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def register_observer(self, observer: AbstractObserver) -> None:
        """
        Create a task to run the observer.
        This will run the observer in a loop until the runner is closed.
        """
        if self._closed_event.is_set():
            raise RuntimeError("Runner is already closed.")
        log.info("observer starting", observer_name=observer.name)
        self._track(self._run_observer(observer))

    async def _run_observer(self, observer: AbstractObserver) -> None:
        while not self._closed_event.is_set():
            try:
                async with asyncio.timeout(observer.timeout()):
                    await observer.observe()
            except TimeoutError:
                log.warning(
                    "observer timed out",
                    observer_name=observer.name,
                    timeout_sec=observer.timeout(),
                )
            except Exception:
                log.exception("observer failed", observer_name=observer.name)
            await asyncio.sleep(observer.observe_interval())
        await observer.cleanup()
        log.info("observer closed", observer_name=observer.name)

    async def _setup(self) -> None:
        for resource in self._resources:
            try:
                await resource.setup()
                log.info("resource set up", resource_name=resource.name)
            except Exception:
                log.exception("resource setup failed", resource_name=resource.name)
                raise

    async def _cleanup(self) -> None:
        for resource in self._resources:
            try:
                await resource.release()
                log.info("resource released", resource_name=resource.name)
            except Exception:
                log.exception("resource release failed", resource_name=resource.name)

    async def start(self) -> None:
        """
        Start the runner.
        This will setup all resources and start runner loop.
        It will run until the runner is closed.
        """
        if self._closed_event.is_set():
            raise RuntimeError("Runner is already closed.")
        log.info("runner starting")
        try:
            await self._setup()
        except Exception:
            await self._cleanup()
            raise
        self._track(self._run())
        log.info("runner started")

    async def _run(self) -> None:
        try:
            await self._closed_event.wait()
        finally:
            log.info("runner cleaning up")
            await self._cleanup()
            log.info("runner closed")

    async def close(self) -> None:
        """
        Close the runner.
        This will stop all observers and cleanup all resources.
        """
        self._closed_event.set()
        # Give the event loop a chance to schedule the _run() task
        # that's waiting on the closed_event
        await asyncio.sleep(0)
