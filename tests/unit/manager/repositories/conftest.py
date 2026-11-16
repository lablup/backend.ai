from __future__ import annotations

import uuid
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import (
    DomainEntityType,
    DomainID,
    DomainName,
)
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.models.base import ensure_all_tables_registered
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.fixtures import DomainFactory, DomainFixtureData

# Register all models so SQLAlchemy's global configure_mappers() can resolve every
# row's string relationships regardless of which models a test shard happens to import.
ensure_all_tables_registered()


@pytest.fixture
def domain_factory() -> DomainFactory:
    """Return an async callable that inserts a domain row and returns its identifiers.

    The factory takes the target SQLAlchemy engine (so each test class can
    supply its own ``with_tables``-managed engine) along with any keyword
    overrides for the ``domains`` row. The returned ``DomainFixtureData``
    exposes both ``domain_name`` and ``domain_id`` so call sites are ready for
    the upcoming domain PK migration to UUID.
    """
    from ai.backend.manager.models.domain.row import (
        domains,
    )  # lazy: avoid registering DomainRow globally
    from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow

    async def _create(
        engine: ExtendedAsyncSAEngine,
        **overrides: Any,
    ) -> DomainFixtureData:
        values: dict[str, Any] = {
            "name": f"test-domain-{uuid.uuid4().hex[:8]}",
            "description": "Test domain",
            "is_active": True,
            "total_resource_slots": ResourceSlot({}),
            "allowed_vfolder_hosts": VFolderHostPermissionMap({}),
            "allowed_docker_registries": [],
            "dotfiles": b"",
            "integration_id": None,
        }
        values.update(overrides)
        async with engine.begin() as conn:
            result = await conn.execute(
                sa.insert(domains).values(values).returning(domains.c.id, domains.c.name)
            )
            row = result.one()
            # The node ops writes when a domain is created. A relation expects both
            # sides to be in the graph already.
            await conn.execute(
                sa.insert(VirtualEntityRow.__table__).values(
                    entity_type=DomainEntityType(), entity_id=row.id
                )
            )
        return DomainFixtureData(domain_name=DomainName(row.name), domain_id=DomainID(row.id))

    return _create
