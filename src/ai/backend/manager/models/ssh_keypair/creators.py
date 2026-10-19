from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow


@dataclass
class SSHKeypairCreator(FieldCreator[UserID, SSHKeypairRow, SSHKeypairData]):
    public_key: str
    private_key: str | None = None
    is_default: bool = False

    @override
    def field_id(self, row: SSHKeypairRow) -> SSHKeypairID:
        return row.id

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: UserID) -> SSHKeypairRow:
        return SSHKeypairRow(
            user_id=owner_id,
            public_key=self.public_key,
            private_key=self.private_key,
            is_default=self.is_default,
        )

    @override
    def to_data(self, row: SSHKeypairRow) -> SSHKeypairData:
        return SSHKeypairData(
            id=row.id,
            user_id=row.user_id,
            public_key=row.public_key,
            private_key=row.private_key,
            is_default=row.is_default,
        )
