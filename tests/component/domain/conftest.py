from __future__ import annotations

import secrets
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import pytest
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.domain import (
    CreateDomainRequest,
    CreateDomainResponse,
    PurgeDomainRequest,
)
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.auth.registry import register_auth_routes

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api.rest.types import ModuleRegistrar
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow

DomainFactory = Callable[..., Coroutine[Any, Any, CreateDomainResponse]]


@pytest.fixture()
def server_module_registrars() -> list[ModuleRegistrar]:
    """Load only the modules required for domain-domain tests."""
    return [register_auth_routes, register_admin_routes]


@pytest.fixture()
async def project_resource_policy_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[None]:
    """Insert the 'default' project_resource_policy required for domain group creation.

    When a domain is created, the API internally creates a default group that
    references resource_policy="default" in project_resource_policies.  This
    fixture seeds that row so the FK constraint is satisfied.
    Uses on_conflict_do_nothing() for idempotency in case the row already exists.
    """
    async with db_engine.begin() as conn:
        await conn.execute(
            pg_insert(ProjectResourcePolicyRow.__table__)
            .values(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            .on_conflict_do_nothing()
        )
    yield
    async with db_engine.begin() as conn:
        await conn.execute(
            ProjectResourcePolicyRow.__table__.delete().where(
                ProjectResourcePolicyRow.__table__.c.name == "default"
            )
        )


@pytest.fixture()
async def domain_factory(
    admin_registry: BackendAIClientRegistry,
    db_engine: SAEngine,
    project_resource_policy_fixture: None,
) -> AsyncIterator[DomainFactory]:
    """Factory fixture that creates domains via SDK and purges them on teardown."""
    created_names: list[str] = []

    async def _create(**overrides: Any) -> CreateDomainResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "name": f"test-domain-{unique}",
            "description": f"Test domain {unique}",
            "is_active": True,
        }
        params.update(overrides)
        result = await admin_registry.domain.create(CreateDomainRequest(**params))
        created_names.append(result.domain.name)
        return result

    yield _create

    for name in reversed(created_names):
        try:
            await admin_registry.domain.purge(PurgeDomainRequest(name=name))
        except Exception:
            # Fallback: remove domain rows directly when the API purge cannot complete.
            async with db_engine.begin() as conn:
                await conn.execute(domains.delete().where(domains.c.name == name))


@pytest.fixture()
async def target_domain(
    domain_factory: DomainFactory,
) -> CreateDomainResponse:
    """Pre-created domain for tests that need an existing domain."""
    return await domain_factory()
