"""Insert specs for the keypairs table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.keypair.types import KeyPairData, KeyPairSecrets
from ai.backend.manager.errors.keypair import KeypairResourcePolicyNotFound
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class KeypairCreator(FieldCreator[UserID, KeyPairRow, KeyPairData]):
    """Creator for one keypair, written under the user that owns it.

    Never marks the row default: the marker moves only through the switch, so issuing
    a key cannot take it off the key the user authorizes with.
    """

    secrets: KeyPairSecrets
    is_active: bool
    is_admin: bool
    resource_policy: str
    rate_limit: int | None = None

    @override
    def field_id(self, row: KeyPairRow) -> KeyPairID:
        return row.id

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                constraint_name="fk_keypairs_resource_policy_keypair_resource_policies",
                error=KeypairResourcePolicyNotFound(self.resource_policy),
            ),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                constraint_name="fk_keypairs_user_users",
                error=UserNotFound("The keypair's owner does not exist."),
            ),
        )

    @override
    def build_row(self, owner_id: UserID) -> KeyPairRow:
        # `rate_limit` of None leaves the column to its default rather than writing NULL.
        return KeyPairRow(
            user=owner_id,
            access_key=self.secrets.access_key,
            secret_key=self.secrets.secret_key,
            is_active=self.is_active,
            is_admin=self.is_admin,
            resource_policy=self.resource_policy,
            rate_limit=self.rate_limit,
            ssh_public_key=self.secrets.ssh_public_key,
            ssh_private_key=self.secrets.ssh_private_key,
        )

    @override
    def to_data(self, row: KeyPairRow) -> KeyPairData:
        return row.to_data()
