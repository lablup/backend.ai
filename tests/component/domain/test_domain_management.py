from __future__ import annotations

import secrets
import uuid
from collections.abc import Callable, Coroutine
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.exceptions import ConflictError, NotFoundError, ServerError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.domain import (
    CreateDomainResponse,
    DeleteDomainRequest,
    DomainFilter,
    GetDomainResponse,
    PurgeDomainRequest,
    SearchDomainsRequest,
)
from ai.backend.common.dto.manager.domain.types import DomainOrder, DomainOrderField, OrderDirection
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.group import groups
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import users

DomainFactory = Callable[..., Coroutine[Any, Any, CreateDomainResponse]]


class TestDomainSoftDeleteEdgeCases:
    async def test_soft_delete_already_inactive_domain(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """S-DEL-2: Soft-deleting an already-inactive domain succeeds idempotently."""
        created = await domain_factory()
        domain_name = created.domain.name

        first = await admin_registry.domain.delete(DeleteDomainRequest(name=domain_name))
        assert first.deleted is True

        second = await admin_registry.domain.delete(DeleteDomainRequest(name=domain_name))
        assert second.deleted is True

        get_result = await admin_registry.domain.get(domain_name)
        assert isinstance(get_result, GetDomainResponse)
        assert get_result.domain.is_active is False

    async def test_soft_delete_nonexistent_domain_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-DEL-BIZ-1: Soft-deleting nonexistent domain → NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.domain.delete(
                DeleteDomainRequest(name="nonexistent-domain-xyz-99999")
            )


class TestDomainPurgeValidation:
    async def test_purge_domain_with_groups_raises_conflict(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """F-PURGE-BIZ-3: Purging domain with groups → ConflictError."""
        created = await domain_factory()
        with pytest.raises(ConflictError):
            await admin_registry.domain.purge(PurgeDomainRequest(name=created.domain.name))

    async def test_purge_domain_with_users_raises_conflict(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
        db_engine: SAEngine,
    ) -> None:
        """F-PURGE-BIZ-2: Purging domain with users → ConflictError."""
        created = await domain_factory()
        domain_name = created.domain.name
        user_uuid = uuid.uuid4()
        unique = secrets.token_hex(4)

        async with db_engine.begin() as conn:
            await conn.execute(groups.delete().where(groups.c.domain_name == domain_name))
            await conn.execute(
                sa.insert(users).values(
                    uuid=str(user_uuid),
                    username=f"test-user-{unique}",
                    email=f"test-user-{unique}@test.local",
                    password=PasswordInfo(
                        password=secrets.token_urlsafe(8),
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=600_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    full_name=f"Test User {unique}",
                    description=f"Test user for purge test {unique}",
                    status=UserStatus.ACTIVE,
                    status_info="test",
                    domain_name=domain_name,
                    resource_policy="default",
                    role=UserRole.USER,
                )
            )

        try:
            with pytest.raises(ConflictError):
                await admin_registry.domain.purge(PurgeDomainRequest(name=domain_name))
        finally:
            async with db_engine.begin() as conn:
                await conn.execute(users.delete().where(users.c.uuid == str(user_uuid)))

    async def test_purge_domain_with_active_kernels_raises_conflict(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
        db_engine: SAEngine,
    ) -> None:
        """F-PURGE-BIZ-1: Purging domain with active kernels → ConflictError."""
        created = await domain_factory()
        domain_name = created.domain.name
        user_uuid = uuid.uuid4()
        session_id = uuid.uuid4()

        async with db_engine.begin() as conn:
            group_result = await conn.execute(
                sa.select(groups.c.id).where(groups.c.domain_name == domain_name).limit(1)
            )
            group_id = group_result.scalar_one()

        async with db_engine.begin() as conn:
            await conn.execute(
                sa.insert(SessionRow.__table__).values(
                    id=session_id,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    occupying_slots=ResourceSlot(),
                    requested_slots=ResourceSlot(),
                    priority=10,
                    cluster_size=1,
                    use_host_network=False,
                )
            )
            await conn.execute(
                sa.insert(kernels).values(
                    session_id=session_id,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    cluster_role="main",
                    cluster_size=1,
                    cluster_idx=0,
                    local_rank=0,
                    cluster_hostname="localhost",
                    status=KernelStatus.RUNNING,
                    occupied_slots=ResourceSlot(),
                    requested_slots=ResourceSlot(),
                    occupied_shares={},
                    repl_in_port=0,
                    repl_out_port=0,
                    stdin_port=0,
                    stdout_port=0,
                    use_host_network=False,
                )
            )

        try:
            with pytest.raises(ConflictError):
                await admin_registry.domain.purge(PurgeDomainRequest(name=domain_name))
        finally:
            async with db_engine.begin() as conn:
                await conn.execute(kernels.delete().where(kernels.c.session_id == session_id))
                await conn.execute(
                    SessionRow.__table__.delete().where(SessionRow.__table__.c.id == session_id)
                )

    async def test_purge_nonexistent_domain_raises_server_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-PURGE-BIZ-4: Purging nonexistent domain → ServerError (HTTP 500)."""
        with pytest.raises(ServerError):
            await admin_registry.domain.purge(
                PurgeDomainRequest(name="nonexistent-domain-xyz-99999")
            )

    async def test_purge_validation_order_kernels_checked_first(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
        db_engine: SAEngine,
    ) -> None:
        """F-PURGE-BIZ-5: Active kernels + users + groups → first error is kernels."""
        created = await domain_factory()
        domain_name = created.domain.name
        user_uuid = uuid.uuid4()
        session_id = uuid.uuid4()
        unique = secrets.token_hex(4)

        async with db_engine.begin() as conn:
            group_result = await conn.execute(
                sa.select(groups.c.id).where(groups.c.domain_name == domain_name).limit(1)
            )
            group_id = group_result.scalar_one()

        async with db_engine.begin() as conn:
            await conn.execute(
                sa.insert(SessionRow.__table__).values(
                    id=session_id,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    occupying_slots=ResourceSlot(),
                    requested_slots=ResourceSlot(),
                    priority=10,
                    cluster_size=1,
                    use_host_network=False,
                )
            )
            await conn.execute(
                sa.insert(kernels).values(
                    session_id=session_id,
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    cluster_role="main",
                    cluster_size=1,
                    cluster_idx=0,
                    local_rank=0,
                    cluster_hostname="localhost",
                    status=KernelStatus.RUNNING,
                    occupied_slots=ResourceSlot(),
                    requested_slots=ResourceSlot(),
                    occupied_shares={},
                    repl_in_port=0,
                    repl_out_port=0,
                    stdin_port=0,
                    stdout_port=0,
                    use_host_network=False,
                )
            )
            await conn.execute(
                sa.insert(users).values(
                    uuid=str(user_uuid),
                    username=f"test-user-{unique}",
                    email=f"test-user-{unique}@test.local",
                    password=PasswordInfo(
                        password=secrets.token_urlsafe(8),
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=600_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    full_name=f"Test User {unique}",
                    description=f"Test user for order test {unique}",
                    status=UserStatus.ACTIVE,
                    status_info="test",
                    domain_name=domain_name,
                    resource_policy="default",
                    role=UserRole.USER,
                )
            )

        try:
            with pytest.raises(ConflictError) as exc_info:
                await admin_registry.domain.purge(PurgeDomainRequest(name=domain_name))
            assert "kernels" in str(exc_info.value.data).lower()
        finally:
            async with db_engine.begin() as conn:
                await conn.execute(kernels.delete().where(kernels.c.session_id == session_id))
                await conn.execute(
                    SessionRow.__table__.delete().where(SessionRow.__table__.c.id == session_id)
                )
                await conn.execute(users.delete().where(users.c.uuid == str(user_uuid)))


class TestDomainSearchExtended:
    async def test_search_second_page_returns_different_domain(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """S-4: Second page query — offset=1 returns different domain than offset=0."""
        unique = secrets.token_hex(4)
        prefix = f"srch-pg-{unique}"
        await domain_factory(name=f"{prefix}-a")
        await domain_factory(name=f"{prefix}-b")

        first_page = await admin_registry.domain.search(
            SearchDomainsRequest(
                filter=DomainFilter(name=StringFilter(contains=prefix)),
                limit=1,
                offset=0,
            )
        )
        second_page = await admin_registry.domain.search(
            SearchDomainsRequest(
                filter=DomainFilter(name=StringFilter(contains=prefix)),
                limit=1,
                offset=1,
            )
        )

        assert first_page.pagination.total >= 2
        assert len(first_page.domains) == 1
        assert len(second_page.domains) == 1
        assert first_page.domains[0].name != second_page.domains[0].name

    async def test_search_domains_sorted_by_name_ascending(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """S-5: Order by name ascending — returned domains are sorted alphabetically."""
        unique = secrets.token_hex(4)
        prefix = f"sort-{unique}"
        await domain_factory(name=f"{prefix}-zzz")
        await domain_factory(name=f"{prefix}-aaa")

        result = await admin_registry.domain.search(
            SearchDomainsRequest(
                filter=DomainFilter(name=StringFilter(contains=prefix)),
                order=[DomainOrder(field=DomainOrderField.NAME, direction=OrderDirection.ASC)],
            )
        )

        assert result.pagination.total >= 2
        names = [d.name for d in result.domains]
        assert names == sorted(names)
        assert names[0].endswith("-aaa")

    async def test_search_nonexistent_name_returns_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """S-6: Search with nonexistent name filter → empty result with pagination.total == 0."""
        unique = secrets.token_hex(16)
        result = await admin_registry.domain.search(
            SearchDomainsRequest(
                filter=DomainFilter(name=StringFilter(contains=f"definitely-nonexistent-{unique}")),
            )
        )
        assert result.pagination.total == 0
        assert len(result.domains) == 0
