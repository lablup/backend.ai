import asyncio
import logging
from typing import Sequence

from ai.backend.logging.utils import BraceStyleAdapter

from .observer import AbstractObserver
from .resource import AbstractResource

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class Runner:
    _resources: Sequence[AbstractResource]
    _closed_event: asyncio.Event

    def __init__(self, resources: Sequence[AbstractResource]):
        self._resources = resources
        self._closed_event = asyncio.Event()

    async def start_observer(self, observer: AbstractObserver) -> None:
        """
        Start the observer.
        This will run the observer in a loop until the runner is closed.
        """
        if self._closed_event.is_set():
            raise RuntimeError("Runner is already closed.")
        log.info("Starting observer: {}", observer.name)
        asyncio.create_task(self._run_observer(observer))

    async def _run_observer(self, observer: AbstractObserver) -> None:
        while not self._closed_event.is_set():
            try:
                await observer.observe()
            except Exception as e:
                log.error(
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
                log.error(
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
                log.error(
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
            log.error(
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
