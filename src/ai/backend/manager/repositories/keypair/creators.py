"""CreatorSpec implementations for keypair repository."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.keypair.types import KeyPairSecrets
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class KeyPairCreatorSpec(CreatorSpec[KeyPairRow]):
    """CreatorSpec for keypair creation with RBAC support."""

    secrets: KeyPairSecrets
    user_id: uuid.UUID
    is_active: bool
    is_admin: bool
    is_default: bool
    resource_policy: str
    rate_limit: int | None = None

    @override
    def build_row(self) -> KeyPairRow:
        # `rate_limit` of None leaves the column to its default rather than writing NULL.
        return KeyPairRow(
            user=self.user_id,
            access_key=self.secrets.access_key,
            secret_key=self.secrets.secret_key,
            is_active=self.is_active,
            is_admin=self.is_admin,
            is_default=self.is_default,
            resource_policy=self.resource_policy,
            rate_limit=self.rate_limit,
            ssh_public_key=self.secrets.ssh_public_key,
            ssh_private_key=self.secrets.ssh_private_key,
        )
