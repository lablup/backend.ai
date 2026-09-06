"""Component tests for the stored secret operations on REST v2.

Test matrix:
  - Status: names the write provider and counts one row per column and key id
  - Re-encryption: writes every row it reads
  - Both: a regular user is refused
"""

from __future__ import annotations

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry

_KEYPAIR_SECRET_COLUMN = "keypairs.secret_key"


class TestSecretStatus:
    async def test_the_status_names_the_write_provider(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        status = await admin_v2_registry.secret.admin_status()
        assert status.write_provider_type == "plain"
        assert [(count.column, count.provider_type) for count in status.counts] == [
            (_KEYPAIR_SECRET_COLUMN, "plain")
        ]


class TestSecretReencryption:
    async def test_a_pass_writes_every_row_it_reads(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        result = await admin_v2_registry.secret.admin_reencrypt()
        assert result.scanned >= 1
        assert result.reencrypted == result.scanned
        assert [count.column for count in result.status.counts] == [_KEYPAIR_SECRET_COLUMN]


class TestPermission:
    async def test_a_regular_user_cannot_reencrypt(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.secret.admin_reencrypt()

    async def test_a_regular_user_cannot_read_the_status(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.secret.admin_status()
