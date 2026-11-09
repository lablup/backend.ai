"""Upsert specs for the keypairs table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.resource_policy import KeyPairResourcePolicyUUID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.keypair.searchable_fields import KeyPairSearchableFields
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import FieldUpserter
from ai.backend.manager.secret.types import SecretValue

__all__ = ("KeypairUpserter",)


@dataclass
class KeypairUpserter(FieldUpserter[UserID, KeyPairRow, KeyPairData]):
    """Write a keypair of a user under its access key. Conflict key: access_key. The
    owner and the secret key are written on insert only, the secret as plaintext the way
    the `plain` write provider stores it. ``rate_limit`` of None leaves the column alone."""

    access_key: AccessKey
    secret_key: str
    is_active: bool
    is_admin: bool
    is_default: bool
    resource_policy_id: KeyPairResourcePolicyUUID
    rate_limit: int | None
    ssh_public_key: str | None
    ssh_private_key: str | None

    @override
    def row_class(self) -> type[KeyPairRow]:
        return KeyPairRow

    @override
    def index_elements(self) -> list[str]:
        return ["access_key"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self, owner_id: UserID) -> dict[str, Any]:
        return {
            "user": owner_id,
            "access_key": self.access_key,
            "secret_key": SecretValue(self.secret_key),
            **self._values(),
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {**self._values(), "updated_at": sa.func.now()}

    def _values(self) -> dict[str, Any]:
        """A resource policy id naming no row leaves ``resource_policy`` NULL, which the
        column refuses."""
        values: dict[str, Any] = {
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "is_default": self.is_default,
            "resource_policy": sa.select(KeyPairResourcePolicyRow.name)
            .where(KeyPairResourcePolicyRow.uuid == self.resource_policy_id)
            .scalar_subquery(),
            "ssh_public_key": self.ssh_public_key,
            "ssh_private_key": self.ssh_private_key,
        }
        if self.rate_limit is not None:
            values["rate_limit"] = self.rate_limit
        return values

    @override
    def to_data(self, row: KeyPairRow) -> KeyPairData:
        return KeyPairSearchableFields.own.to_data(row)
