import asyncio
import logging
from collections.abc import Sequence

from ai.backend.logging.utils import BraceStyleAdapter

from ..observer.types import AbstractObserver
from ..resource.types import AbstractResource

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


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

    def __init__(self, resources: Sequence[AbstractResource]):
        self._resources = resources
        self._closed_event = asyncio.Event()

    async def register_observer(self, observer: AbstractObserver) -> None:
        """
        Create a task to run the observer.
        This will run the observer in a loop until the runner is closed.
        """
        if self._closed_event.is_set():
            raise RuntimeError("Runner is already closed.")
        log.info("Starting observer: {}", observer.name)
        asyncio.create_task(self._run_observer(observer))

    async def _run_observer(self, observer: AbstractObserver) -> None:
        while not self._closed_event.is_set():
            try:
                async with asyncio.timeout(observer.timeout()):
                    await observer.observe()
            except asyncio.TimeoutError:
                log.warning(
                    "Observer {} timed out after {} seconds.",
                    observer.name,
                    observer.timeout(),
                )
            except Exception as e:
                log.exception(
                    "Error while observing: {}",
                    e,
                )
            await asyncio.sleep(observer.observe_interval())
        await observer.cleanup()
        log.info(
            "Observer closed: {}",
            observer.name,
        )

    async def _setup(self) -> None:
        for resource in self._resources:
            try:
                await resource.setup()
                log.info(
                    "Resource setup: {}",
                    resource.name,
                )
            except Exception as e:
                log.exception(
                    "Error while setting up resource: {}",
                    e,
                )
                raise

    async def _cleanup(self) -> None:
        for resource in self._resources:
            try:
                await resource.release()
                log.info(
                    "Resource released: {}",
                    resource.name,
                )
            except Exception as e:
                log.exception(
                    "Error while releasing resource: {}",
                    e,
                )

    async def start(self) -> None:
        """
        Start the runner.
        This will setup all resources and start runner loop.
        It will run until the runner is closed.
        """
        if self._closed_event.is_set():
            raise RuntimeError("Runner is already closed.")
        log.info("Starting runner.")
        try:
            await self._setup()
        except Exception as e:
            log.exception(
                "Error while starting runner: {}",
                e,
            )
            await self._cleanup()
            raise
        asyncio.create_task(self._run())
        log.info("Runner started.")

    async def _run(self) -> None:
        try:
            await self._closed_event.wait()
        finally:
            log.info("cleaning up runner.")
            await self._cleanup()
            log.info("Runner closed.")

    async def close(self) -> None:
        """
        Close the runner.
        This will stop all observers and cleanup all resources.
        """
        self._closed_event.set()
        # Give the event loop a chance to schedule the _run() task
        # that's waiting on the closed_event
        await asyncio.sleep(0)
