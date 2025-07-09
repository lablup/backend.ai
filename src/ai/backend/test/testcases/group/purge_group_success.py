from typing import override

from ai.backend.client.output.fields import group_fields
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.domain import DomainContext
from ai.backend.test.contexts.group import CreatedGroupContext
from ai.backend.test.templates.template import TestCode


class PurgeGroupSuccess(TestCode):
    @override
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        created_group_meta = CreatedGroupContext.current()
        domain_ctx = DomainContext.current()

        result = await client_session.Group.purge(str(created_group_meta.group_id))
        assert result["ok"] is True

        group_ids_raw = await client_session.Group.list(
            domain_name=domain_ctx.name, fields=(group_fields["id"],)
        )
        group_ids = [group["id"] for group in group_ids_raw]
        assert str(created_group_meta.group_id) not in group_ids, (
            "Group was not purged successfully."
        )
