from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import Optional, override

from ai.backend.client.func.user import UserRole, UserStatus
from ai.backend.client.output.fields import group_fields, keypair_fields, user_fields
from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.domain import DomainContext
from ai.backend.test.contexts.group import GroupContext
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.contexts.user import CreatedUserContext
from ai.backend.test.data.user import CreatedUserMeta
from ai.backend.test.templates.template import WrapperTestTemplate
from ai.backend.test.tester.dependency import DomainDep, GroupDep


class UserTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "create_user"

    async def _resolve_group_id(
        self,
        client_session: AsyncSession,
        group_dep: GroupDep,
        domain_dep: DomainDep,
    ) -> str:
        group_data = await client_session.Group.from_name(
            group_dep.name,
            fields=[group_fields["id"]],
            domain_name=domain_dep.name,
        )
        if not group_data:
            raise RuntimeError(
                f"Cannot find the group {group_dep.name!r} in the domain {domain_dep.name!r}"
            )
        assert len(group_data) == 1, f"Expected exactly one group, found {len(group_data)}"
        return group_data[0]["id"]

    async def _create_user_with_keypair(
        self,
        client_session: AsyncSession,
        domain_name: str,
        username: str,
        password: str,
        email: str,
        description: str,
        group_id: str,
    ) -> CreatedUserMeta:
        response = await client_session.User.create(
            domain_name,
            email,
            password,
            username=username,
            description=description,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            need_password_change=False,
            group_ids=[group_id],
            fields=(
                user_fields["uuid"],
                user_fields["username"],
                user_fields["email"],
            ),
        )
        if not response.get("ok", False):
            raise RuntimeError(f"User.create failed: {response.get('msg', 'Unknown error')}")

        user_info = response["user"]
        if user_info is None:
            raise RuntimeError("User.create returned None user data")

        keypair_info = await client_session.KeyPair.list(
            user_id=email,
            fields=[keypair_fields["access_key"], keypair_fields["secret_key"]],
        )
        assert len(keypair_info) > 0, "Keypair list should not be empty"
        keypair_info = keypair_info[0]

        user_meta = CreatedUserMeta(
            email=user_info["email"],
            password=password,
            access_key=keypair_info["access_key"],
            secret_key=keypair_info["secret_key"],
        )
        return user_meta

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id
        client_session = ClientSessionContext.current()
        domain_ctx = DomainContext.current()
        group_ctx = GroupContext.current()
        group_id = await self._resolve_group_id(client_session, group_ctx, domain_ctx)

        username = f"test-{str(test_id)[:8]}"
        password = "password1234"
        email = f"{username}@tester_email.com"
        description = f"Test user for {test_id}, used in tester package"

        user_meta: Optional[CreatedUserMeta] = None
        user_meta = await self._create_user_with_keypair(
            client_session,
            domain_ctx.name,
            username,
            password,
            email,
            description,
            group_id,
        )
        try:
            with CreatedUserContext.with_current(user_meta):
                yield
        finally:
            if user_meta:
                await client_session.User.delete(email)
                await client_session.User.purge(email)
