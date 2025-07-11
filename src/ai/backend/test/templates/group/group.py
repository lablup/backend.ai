import asyncio
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.domain import DomainContext
from ai.backend.test.contexts.group import CreatedGroupContext
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.data.group import CreatedGroupMeta
from ai.backend.test.templates.template import WrapperTestTemplate


class GroupTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "create_group"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id
        group_name = f"test-group-{str(test_id)}"
        client_session = ClientSessionContext.current()
        domain_ctx = DomainContext.current()

        try:
            result = await client_session.Group.create(
                domain_name=domain_ctx.name,
                name=group_name,
            )
            group_id = result["group"]["id"]

            with CreatedGroupContext.with_current(
                CreatedGroupMeta(
                    group_id=group_id,
                    group_name=group_name,
                )
            ):
                yield
        finally:
            info = await client_session.Group.detail(group_id)
            if info is not None:
                await self._retry_purge_group(client_session, group_id)

    async def _retry_purge_group(self, client_session, group_id: str) -> None:
        for _ in range(3):
            try:
                await client_session.Group.purge(group_id)
                return
            except BackendAPIError as e:
                if e.status == 400:
                    # Wait for other resources(ex. Model Service) to be cleaned up
                    await asyncio.sleep(10)
