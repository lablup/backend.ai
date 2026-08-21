"""CreatorSpec implementations for keypair repository."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.keypair.types import KeyPairCreator, KeyPairSecrets
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class KeyPairCreatorSpec(CreatorSpec[KeyPairRow]):
    """CreatorSpec for keypair creation with RBAC support."""

    creator: KeyPairCreator
    generated_data: KeyPairSecrets
    user_id: uuid.UUID
    is_default: bool

    @override
    def build_row(self) -> KeyPairRow:
        return KeyPairRow(
            user=self.user_id,
            access_key=self.generated_data.access_key,
            secret_key=self.generated_data.secret_key,
            is_active=self.creator.is_active,
            is_admin=self.creator.is_admin,
            is_default=self.is_default,
            resource_policy=self.creator.resource_policy,
            rate_limit=self.creator.rate_limit,
            num_queries=0,
            ssh_public_key=self.generated_data.ssh_public_key,
            ssh_private_key=self.generated_data.ssh_private_key,
        )
