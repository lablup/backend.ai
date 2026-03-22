"""CreatorSpec implementations for keypair repository."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.keypair.types import GeneratedKeyPairData, KeyPairCreator
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class KeyPairCreatorSpec(CreatorSpec[KeyPairRow]):
    """CreatorSpec for keypair creation with RBAC support."""

    creator: KeyPairCreator
    generated_data: GeneratedKeyPairData
    user_id: uuid.UUID
    email: str

    @override
    def build_row(self) -> KeyPairRow:
        return KeyPairRow.from_creator(
            self.creator,
            self.generated_data,
            self.user_id,
            self.email,
        )
