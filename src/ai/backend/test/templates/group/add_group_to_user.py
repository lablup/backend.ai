from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from typing import override

from ai.backend.client.output.fields import user_fields
from ai.backend.test.contexts.auth import KeypairContext
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.group import CreatedGroupContext
from ai.backend.test.templates.template import WrapperTestTemplate


@dataclass
class _UserInfo:
    user_email: str
    group_ids: list[str]


class AddGroupToKeypairTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "add_group"

    @override
    @actxmgr
    async def _context(self):
        created_group_meta = CreatedGroupContext.current()
        keypair = KeypairContext.current()
        client_session = ClientSessionContext.current()
        user_info = await self._get_user_info_by_keypair(client_session, keypair.access_key)

        original_group_ids = user_info.group_ids.copy()
        new_group_ids = user_info.group_ids + [str(created_group_meta.group_id)]

        try:
            result = await client_session.User.update(
                user_info.user_email,
                group_ids=new_group_ids,
            )
            if not result["ok"]:
                raise RuntimeError(f"Failed to update user groups: {result}")
            yield
        finally:
            await client_session.User.update(
                user_info.user_email,
                group_ids=original_group_ids,
            )
            user_info_after = await self._get_user_info_by_keypair(
                client_session, keypair.access_key
            )
            if set(user_info_after.group_ids) != set(original_group_ids):
                raise RuntimeError(
                    f"User groups after update do not match original groups: "
                    f"{user_info_after.group_ids} != {original_group_ids}"
                )

    async def _get_user_info_by_keypair(self, client_session, access_key: str) -> _UserInfo:
        keypair_info = await client_session.KeyPair(access_key).info()
        user_id = keypair_info["user_id"]
        user_info = await client_session.User.detail(user_id, fields=(user_fields["groups"],))
        groups_info = user_info["groups"]
        group_ids = [group["id"] for group in groups_info]
        return _UserInfo(user_email=keypair_info["user_id"], group_ids=group_ids)
