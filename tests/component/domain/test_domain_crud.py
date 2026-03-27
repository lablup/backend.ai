"""Component tests for Domain CRUD lifecycle.

Covers create, get (by name and list), and modify operations through
the HTTP API via the SDK client with a real database.

Test matrix:
  - Domain creation: success, auto model-store group, domain node with scaling group,
    duplicate name, empty name, name exceeding 64 chars.
  - Domain get: by name, list all, name filter.
  - Domain modify: resource_slots, allowed_docker_registries, active status toggle.
  - Permission control: regular user blocked from create and modify.
"""

from __future__ import annotations

import secrets
from collections.abc import Callable, Coroutine
from typing import Any

import pytest
import sqlalchemy as sa
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.exceptions import (
    InvalidRequestError,
    PermissionDeniedError,
)
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.domain import (
    CreateDomainRequest,
    CreateDomainResponse,
    DomainFilter,
    SearchDomainsRequest,
    UpdateDomainRequest,
)
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.manager.models.group import groups
from ai.backend.manager.models.scaling_group import (
    ScalingGroupOpts,
    scaling_groups,
    sgroups_for_domains,
)

DomainFactory = Callable[..., Coroutine[Any, Any, CreateDomainResponse]]


# ---------------------------------------------------------------------------
# Domain Create
# ---------------------------------------------------------------------------


class TestDomainCreateCRUD:
    """Tests for domain creation via POST /admin/domains."""

    async def test_s1_create_domain_returns_correct_name_and_config(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """S-1: Create domain → returns domain with correct name and config."""
        unique = secrets.token_hex(4)
        name = f"crud-create-s1-{unique}"
        result = await domain_factory(
            name=name,
            description=f"CRUD test domain {unique}",
            is_active=True,
        )
        assert isinstance(result, CreateDomainResponse)
        assert result.domain.name == name
        assert result.domain.description == f"CRUD test domain {unique}"
        assert result.domain.is_active is True
        assert result.domain.created_at is not None
        assert result.domain.modified_at is not None

    async def test_s2_create_domain_auto_creates_model_store_group(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
        db_engine: SAEngine,
    ) -> None:
        """S-2: Create domain → model-store group automatically created."""
        result = await domain_factory()
        domain_name = result.domain.name

        async with db_engine.connect() as conn:
            row = await conn.execute(
                sa.select(groups.c.name, groups.c.type).where(
                    (groups.c.domain_name == domain_name) & (groups.c.name == "model-store")
                )
            )
            model_store = row.fetchone()

        assert model_store is not None, "model-store group was not created for the domain"
        assert model_store.name == "model-store"

    async def test_s3_create_domain_with_total_resource_slots(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """S-3: Create domain with total_resource_slots → slots persisted in response."""
        result = await domain_factory(
            total_resource_slots={"cpu": "4", "mem": "4294967296"},
        )
        assert result.domain.total_resource_slots is not None
        assert "cpu" in result.domain.total_resource_slots

    async def test_s4_create_domain_with_allowed_docker_registries(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """S-4: Create domain with allowed_docker_registries → registries persisted."""
        registries = ["registry.example.com", "docker.io"]
        result = await domain_factory(
            allowed_docker_registries=registries,
        )
        assert result.domain.allowed_docker_registries == registries

    async def test_s5_create_domain_with_is_active_false(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """S-5: Create domain with is_active=False → domain created as inactive."""
        result = await domain_factory(is_active=False)
        assert result.domain.is_active is False

    async def test_s6_create_domain_node_with_scaling_group_association(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
        db_engine: SAEngine,
    ) -> None:
        """S-6: Domain created → can associate scaling group via sgroups_for_domains."""
        result = await domain_factory()
        domain_name = result.domain.name

        # Insert a scaling group and associate it with the domain directly.
        sgroup_name = f"crud-sg-{secrets.token_hex(4)}"
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.insert(scaling_groups).values(
                    name=sgroup_name,
                    description=f"CRUD test scaling group {sgroup_name}",
                    is_active=True,
                    is_public=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
            await conn.execute(
                sa.insert(sgroups_for_domains).values(
                    scaling_group=sgroup_name,
                    domain=domain_name,
                )
            )

        try:
            async with db_engine.connect() as conn:
                row = await conn.execute(
                    sa.select(sgroups_for_domains.c.scaling_group).where(
                        (sgroups_for_domains.c.domain == domain_name)
                        & (sgroups_for_domains.c.scaling_group == sgroup_name)
                    )
                )
                assoc = row.fetchone()
            assert assoc is not None, "scaling group association was not created"
        finally:
            async with db_engine.begin() as conn:
                await conn.execute(
                    sgroups_for_domains.delete().where(
                        sgroups_for_domains.c.scaling_group == sgroup_name
                    )
                )
                await conn.execute(
                    scaling_groups.delete().where(scaling_groups.c.name == sgroup_name)
                )

    async def test_f_biz1_create_domain_with_duplicate_name_raises_conflict(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """F-BIZ-1: Create domain with duplicate name → InvalidRequestError (400).

        The server returns 400 (not 409) for duplicate domain names.
        """
        result = await domain_factory()
        duplicate_name = result.domain.name

        with pytest.raises(InvalidRequestError):
            await admin_registry.domain.create(
                CreateDomainRequest(name=duplicate_name, description="Duplicate attempt")
            )

    async def test_f_val1_create_domain_with_empty_name_raises_bad_request(
        self,
        admin_registry: BackendAIClientRegistry,
        project_resource_policy_fixture: None,
    ) -> None:
        """F-VAL-1: Create domain with whitespace-only name → InvalidRequestError (400).

        The name passes Pydantic's max_length check but is rejected by the
        service layer (strips to empty string).
        """
        with pytest.raises(InvalidRequestError):
            await admin_registry.domain.create(
                CreateDomainRequest(name="   ", description="Empty name attempt")
            )

    async def test_f_val2_create_domain_with_name_exceeding_64_chars_raises_validation_error(
        self,
    ) -> None:
        """F-VAL-2: Create domain with name > 64 chars → Pydantic ValidationError on client side.

        The Pydantic max_length=64 constraint is enforced at model instantiation time
        on the client before the request is sent to the server.
        """
        with pytest.raises(PydanticValidationError):
            CreateDomainRequest(name="a" * 65, description="Long name attempt")

    @pytest.mark.xfail(
        strict=True,
        reason="Server returns 500 for 64-char domain name — likely server-side validation issue",
    )
    async def test_f_val2b_domain_name_at_exactly_64_chars_is_valid(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """F-VAL-2b: Domain name with exactly 64 chars is accepted (boundary check).

        NOTE: The server currently returns 500 for 64-char domain names.
        This appears to be a server-side validation issue. Marked xfail until fixed.
        """
        name_64 = "a" * 64
        result = await domain_factory(name=name_64)
        assert result.domain.name == name_64

    async def test_f_auth1_regular_user_cannot_create_domain(
        self,
        user_registry: BackendAIClientRegistry,
        project_resource_policy_fixture: None,
    ) -> None:
        """F-AUTH-1: Regular user cannot create domain → PermissionDeniedError (403)."""
        unique = secrets.token_hex(4)
        with pytest.raises(PermissionDeniedError):
            await user_registry.domain.create(
                CreateDomainRequest(
                    name=f"denied-create-{unique}",
                    description="Should be denied",
                )
            )


# ---------------------------------------------------------------------------
# Domain Get / List
# ---------------------------------------------------------------------------


class TestDomainGetCRUD:
    """Tests for domain retrieval via GET /admin/domains/{name} and POST /admin/domains/search."""

    async def test_s1_get_domain_by_name_returns_matching_domain(
        self,
        admin_registry: BackendAIClientRegistry,
        target_domain: CreateDomainResponse,
    ) -> None:
        """S-1: Get domain by name → returns domain with matching name and fields."""
        get_result = await admin_registry.domain.get(target_domain.domain.name)
        assert get_result.domain.name == target_domain.domain.name
        assert get_result.domain.description == target_domain.domain.description
        assert get_result.domain.is_active == target_domain.domain.is_active

    async def test_s2_get_domain_response_contains_all_fields(
        self,
        admin_registry: BackendAIClientRegistry,
        target_domain: CreateDomainResponse,
    ) -> None:
        """S-2: Get domain by name → response contains all required DTO fields."""
        get_result = await admin_registry.domain.get(target_domain.domain.name)
        domain = get_result.domain
        assert domain.name is not None
        assert domain.created_at is not None
        assert domain.modified_at is not None
        assert isinstance(domain.total_resource_slots, dict)
        assert isinstance(domain.allowed_docker_registries, list)
        assert isinstance(domain.allowed_vfolder_hosts, dict)

    async def test_s3_list_domains_returns_list_including_test_domain(
        self,
        admin_registry: BackendAIClientRegistry,
        target_domain: CreateDomainResponse,
    ) -> None:
        """S-3: List all domains → list includes the created test domain."""
        result = await admin_registry.domain.search(SearchDomainsRequest())
        domain_names = [d.name for d in result.domains]
        assert target_domain.domain.name in domain_names
        assert result.pagination.total >= 1

    async def test_s4_search_domains_with_name_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """S-4: Search domains with name filter → returns only matching domains."""
        unique = secrets.token_hex(4)
        marker = f"crud-get-filter-{unique}"
        await domain_factory(name=marker)

        result = await admin_registry.domain.search(
            SearchDomainsRequest(
                filter=DomainFilter(name=StringFilter(contains=marker)),
            )
        )
        assert result.pagination.total >= 1
        assert any(d.name == marker for d in result.domains)

    async def test_s5_search_domains_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """S-5: Search with limit=1 → returns at most 1 domain."""
        result = await admin_registry.domain.search(SearchDomainsRequest(limit=1, offset=0))
        assert result.pagination.limit == 1
        assert len(result.domains) <= 1

    async def test_s6_search_domains_by_active_status_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """S-6: Search active domains → returns only active domains."""
        await domain_factory(is_active=True)
        result = await admin_registry.domain.search(
            SearchDomainsRequest(
                filter=DomainFilter(is_active=True),
            )
        )
        assert all(d.is_active is True for d in result.domains)


# ---------------------------------------------------------------------------
# Domain Modify
# ---------------------------------------------------------------------------


class TestDomainModifyCRUD:
    """Tests for domain modification via PATCH /admin/domains/{name}."""

    async def test_s1_modify_domain_total_resource_slots(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """S-1: Modify domain total_resource_slots → updated value returned."""
        result = await domain_factory()
        domain_name = result.domain.name

        update_result = await admin_registry.domain.update(
            domain_name,
            UpdateDomainRequest(
                total_resource_slots={"cpu": "8", "mem": "8589934592"},
            ),
        )
        assert update_result.domain.name == domain_name
        assert update_result.domain.total_resource_slots is not None
        assert "cpu" in update_result.domain.total_resource_slots

    async def test_s2_modify_domain_allowed_docker_registries(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """S-2: Modify domain allowed_docker_registries → updated registries returned."""
        result = await domain_factory()
        domain_name = result.domain.name
        new_registries = ["registry.example.com", "gcr.io"]

        update_result = await admin_registry.domain.update(
            domain_name,
            UpdateDomainRequest(allowed_docker_registries=new_registries),
        )
        assert update_result.domain.allowed_docker_registries == new_registries

    async def test_s3_deactivate_domain_updates_active_status(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """S-3: Modify is_active=False (deactivate) → domain becomes inactive."""
        result = await domain_factory(is_active=True)
        domain_name = result.domain.name
        assert result.domain.is_active is True

        update_result = await admin_registry.domain.update(
            domain_name,
            UpdateDomainRequest(is_active=False),
        )
        assert update_result.domain.is_active is False

    async def test_s4_reactivate_domain_updates_active_status(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """S-4: Modify is_active=True (reactivate) → domain becomes active again."""
        result = await domain_factory(is_active=False)
        domain_name = result.domain.name
        assert result.domain.is_active is False

        update_result = await admin_registry.domain.update(
            domain_name,
            UpdateDomainRequest(is_active=True),
        )
        assert update_result.domain.is_active is True

    async def test_s5_modify_multiple_fields_at_once(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        """S-5: Modify multiple fields in single request → all fields updated."""
        unique = secrets.token_hex(4)
        result = await domain_factory()
        domain_name = result.domain.name

        new_description = f"Updated description {unique}"
        new_registries = [f"registry-{unique}.example.com"]

        update_result = await admin_registry.domain.update(
            domain_name,
            UpdateDomainRequest(
                description=new_description,
                allowed_docker_registries=new_registries,
            ),
        )
        assert update_result.domain.description == new_description
        assert update_result.domain.allowed_docker_registries == new_registries

    async def test_s6_modify_domain_description(
        self,
        admin_registry: BackendAIClientRegistry,
        target_domain: CreateDomainResponse,
    ) -> None:
        """S-6: Modify description → updated description returned."""
        unique = secrets.token_hex(4)
        new_description = f"Updated CRUD description {unique}"

        update_result = await admin_registry.domain.update(
            target_domain.domain.name,
            UpdateDomainRequest(description=new_description),
        )
        assert update_result.domain.description == new_description
        assert update_result.domain.name == target_domain.domain.name

    async def test_f_auth1_regular_user_cannot_modify_domain(
        self,
        user_registry: BackendAIClientRegistry,
        target_domain: CreateDomainResponse,
    ) -> None:
        """F-AUTH-1: Regular user cannot modify domain → PermissionDeniedError (403)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.domain.update(
                target_domain.domain.name,
                UpdateDomainRequest(description="Unauthorized modification"),
            )
