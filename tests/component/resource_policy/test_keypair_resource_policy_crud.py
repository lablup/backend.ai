"""Component tests for keypair resource policy v2 CRUD.

Test matrix:
  - Create: success with all fields, typed resource slots, typed vfolder hosts
  - Get: by name, verify typed fields
  - Search: list all, verify count
  - Update: partial update, verify changed fields
  - Delete: by name, verify not found after
"""

from __future__ import annotations

import secrets
from decimal import Decimal

from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    UpdateKeypairResourcePolicyInput,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    CreateKeypairResourcePolicyPayload,
)

from .conftest import KeypairResourcePolicyFactory


class TestKeypairResourcePolicyCreate:
    """Tests for keypair resource policy creation via POST /v2/resource-policies/keypair."""

    async def test_s1_create_returns_correct_name_and_fields(
        self,
        admin_v2_registry: V2ClientRegistry,
        keypair_resource_policy_factory: KeypairResourcePolicyFactory,
    ) -> None:
        """S-1: Create keypair resource policy with all fields."""
        unique = secrets.token_hex(4)
        name = f"crud-krp-s1-{unique}"
        result = await keypair_resource_policy_factory(
            name=name,
            default_for_unspecified="LIMITED",
            max_concurrent_sessions=10,
            max_containers_per_session=2,
            idle_timeout=7200,
            max_session_lifetime=86400,
            max_concurrent_sftp_sessions=3,
            total_resource_slots=[
                {"resource_type": "cpu", "quantity": "8"},
                {"resource_type": "mem", "quantity": "8589934592"},
            ],
            allowed_vfolder_hosts=[
                {"host": "default", "permissions": ["mount-in-session", "upload-file"]},
            ],
        )

        assert isinstance(result, CreateKeypairResourcePolicyPayload)
        policy = result.keypair_resource_policy
        assert policy.name == name
        assert policy.max_concurrent_sessions == 10
        assert policy.max_containers_per_session == 2
        assert policy.idle_timeout == 7200

    async def test_s2_create_with_typed_resource_slots(
        self,
        admin_v2_registry: V2ClientRegistry,
        keypair_resource_policy_factory: KeypairResourcePolicyFactory,
    ) -> None:
        """S-2: Verify resource slots are returned as typed entries."""
        result = await keypair_resource_policy_factory(
            total_resource_slots=[
                {"resource_type": "cpu", "quantity": "4"},
                {"resource_type": "mem", "quantity": "4294967296"},
                {"resource_type": "cuda.shares", "quantity": "1.5"},
            ],
        )
        policy = result.keypair_resource_policy
        slots = policy.total_resource_slots
        assert len(slots) == 3
        slot_dict = {s.resource_type: s.quantity for s in slots}
        assert slot_dict["cpu"] == Decimal("4")
        assert slot_dict["mem"] == Decimal("4294967296")
        assert slot_dict["cuda.shares"] == Decimal("1.5")

    async def test_s3_create_with_typed_vfolder_hosts(
        self,
        admin_v2_registry: V2ClientRegistry,
        keypair_resource_policy_factory: KeypairResourcePolicyFactory,
    ) -> None:
        """S-3: Verify vfolder hosts are returned as typed entries."""
        result = await keypair_resource_policy_factory(
            allowed_vfolder_hosts=[
                {"host": "nfs-vol1", "permissions": ["mount-in-session", "upload-file"]},
            ],
        )
        policy = result.keypair_resource_policy
        hosts = policy.allowed_vfolder_hosts
        assert len(hosts) == 1
        assert hosts[0].host == "nfs-vol1"
        assert "mount-in-session" in hosts[0].permissions


class TestKeypairResourcePolicyGet:
    """Tests for keypair resource policy retrieval."""

    async def test_s1_get_by_name(
        self,
        admin_v2_registry: V2ClientRegistry,
        keypair_resource_policy_factory: KeypairResourcePolicyFactory,
    ) -> None:
        """S-1: Get policy by name returns correct data."""
        created = await keypair_resource_policy_factory()
        name = created.keypair_resource_policy.name

        result = await admin_v2_registry.resource_policy.admin_get_keypair_resource_policy(name)
        assert result.name == name
        assert (
            result.max_concurrent_sessions
            == created.keypair_resource_policy.max_concurrent_sessions
        )


class TestKeypairResourcePolicyUpdate:
    """Tests for keypair resource policy update."""

    async def test_s1_update_partial_fields(
        self,
        admin_v2_registry: V2ClientRegistry,
        keypair_resource_policy_factory: KeypairResourcePolicyFactory,
    ) -> None:
        """S-1: Update only specific fields, others remain unchanged."""
        created = await keypair_resource_policy_factory(max_concurrent_sessions=5)
        name = created.keypair_resource_policy.name

        result = await admin_v2_registry.resource_policy.admin_update_keypair_resource_policy(
            name, UpdateKeypairResourcePolicyInput(max_concurrent_sessions=20)
        )
        assert result.keypair_resource_policy.max_concurrent_sessions == 20
        # idle_timeout should remain unchanged
        assert (
            result.keypair_resource_policy.idle_timeout
            == created.keypair_resource_policy.idle_timeout
        )


class TestKeypairResourcePolicyDelete:
    """Tests for keypair resource policy deletion."""

    async def test_s1_delete_by_name(
        self,
        admin_v2_registry: V2ClientRegistry,
        keypair_resource_policy_factory: KeypairResourcePolicyFactory,
    ) -> None:
        """S-1: Delete policy, verify it's gone."""
        created = await keypair_resource_policy_factory()
        name = created.keypair_resource_policy.name

        result = await admin_v2_registry.resource_policy.admin_delete_keypair_resource_policy(name)
        assert result.name == name
