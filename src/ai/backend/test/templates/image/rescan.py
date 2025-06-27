import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import override
from uuid import UUID

from ai.backend.client.session import AsyncSession
from ai.backend.common.bgtask.types import BgtaskStatus
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.container_registry import ContainerRegistriesContext
from ai.backend.test.contexts.image import RescannedImagesContext
from ai.backend.test.data.image import RescannedImagesMeta
from ai.backend.test.templates.session.utils import verify_bgtask_events
from ai.backend.test.templates.template import WrapperTestTemplate
from ai.backend.test.tester.dependency import ContainerRegistryDep

# TODO: Add timeout, and set concurrency limit
# _TIMEOUT = 10


class ImageRescanTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "rescan_image"

    async def _create_rescan_tasks(
        self, client_session: AsyncSession, container_registry_deps: list[ContainerRegistryDep]
    ) -> dict[str, asyncio.Task[str]]:
        tasks: dict[str, asyncio.Task[str]] = {}

        for registry_dep in container_registry_deps:
            key = f"{registry_dep.name}/{registry_dep.project}"
            task = asyncio.create_task(
                self._run_single_rescan(client_session, registry_dep), name=f"rescan_{key}"
            )
            tasks[key] = task

        return tasks

    async def _run_single_rescan(
        self, client_session: AsyncSession, registry_dep: ContainerRegistryDep
    ) -> str:
        resp = await client_session.Image.rescan_images(registry_dep.name, registry_dep.project)
        bgtask_id = resp["task_id"]

        result_str = await verify_bgtask_events(
            client_session,
            bgtask_id,
            expected_events={BgtaskStatus.DONE, BgtaskStatus.PARTIAL_SUCCESS},
            failure_events={BgtaskStatus.FAILED, BgtaskStatus.CANCELLED},
        )

        if result_str is None:
            raise RuntimeError(f"Rescan task {bgtask_id} failed or was cancelled.")

        return result_str

    async def _execute_rescan_tasks(
        self, rescan_tasks: dict[str, asyncio.Task[str]]
    ) -> dict[str, list[UUID]]:
        """Execute all rescan tasks and process their results."""

        # Execute all tasks concurrently
        result_strings = await asyncio.gather(*rescan_tasks.values(), return_exceptions=False)

        # Process results: convert string representations to actual UUID lists
        rescan_results: dict[str, list[UUID]] = {}
        for key, result_str in zip(rescan_tasks.keys(), result_strings):
            try:
                # Parse the string representation of list[UUID] back to actual list[UUID]
                uuid_list = eval(result_str, {"UUID": UUID})
                rescan_results[key] = uuid_list
            except Exception as e:
                raise RuntimeError(f"Failed to parse result for {key}: {result_str}") from e

        return rescan_results

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        client_session = ClientSessionContext.current()
        container_registry_deps = ContainerRegistriesContext.current()

        rescan_tasks = await self._create_rescan_tasks(client_session, container_registry_deps)
        rescan_results = await self._execute_rescan_tasks(rescan_tasks)

        with RescannedImagesContext.with_current(RescannedImagesMeta(rescan_results)):
            yield
