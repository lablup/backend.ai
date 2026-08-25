"""Component tests for the keypair secret re-encryption on REST v2.

Test matrix:
  - Status: names the write provider and counts one row per key id
  - Re-encryption: writes every row it reads, and leaves them on the write provider
  - Both: a regular user is refused
"""

from __future__ import annotations

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry


class TestSecretStatus:
    async def test_the_status_names_the_write_provider(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        status = await admin_v2_registry.keypair.admin_secret_status()
        assert status.write_provider_type == "plain"
        assert [count.provider_type for count in status.counts] == ["plain"]


class TestSecretReencryption:
    async def test_a_pass_writes_every_row_it_reads(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        result = await admin_v2_registry.keypair.admin_reencrypt_secrets()
        assert result.scanned >= 1
        assert result.reencrypted == result.scanned
        assert [count.provider_type for count in result.status.counts] == ["plain"]


class TestPermission:
    async def test_a_regular_user_cannot_reencrypt(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.keypair.admin_reencrypt_secrets()

    async def test_a_regular_user_cannot_read_the_status(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.keypair.admin_secret_status()
