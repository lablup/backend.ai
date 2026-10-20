from dataclasses import dataclass

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.types import FieldData
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.secret.types import SecretValue


@dataclass(frozen=True)
class SSHKeypairData(FieldData):
    id: SSHKeypairID
    user_id: UserID
    public_key: str
    private_key: SecretValue | None
    is_default: bool
