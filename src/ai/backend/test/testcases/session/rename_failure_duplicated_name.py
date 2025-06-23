from typing import override

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.session import (
    ClusterContext,
    CreatedSessionMetaContext,
    SessionContext,
)
from ai.backend.test.templates.template import TestCode


class SessionRenameFailureDuplicatedName(TestCode):
    @override
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        session_meta = CreatedSessionMetaContext.current()
        session_name = session_meta.name

        image_dep = ImageContext.current()
        cluster_dep = ClusterContext.current()
        session_dep = SessionContext.current()
        second_session_name = session_name + "_second"

        # TODO: Make second session creation/deletion with template
        await client_session.ComputeSession.get_or_create(
            image_dep.name,
            resources=session_dep.resources,
            type_="interactive",
            name=second_session_name,
            cluster_mode=cluster_dep.cluster_mode,
            cluster_size=cluster_dep.cluster_size,
        )
        try:
            await client_session.ComputeSession(name=second_session_name).rename(session_name)
            raise AssertionError(
                "Renaming a session to a name that already exists should raise an error"
            )
        except BackendAPIError:
            pass
        finally:
            await client_session.ComputeSession(name=second_session_name).destroy()
