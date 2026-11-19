"""Write specs for the SSH keypairs a user holds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.ssh_keypair.creators import SSHKeypairCreator
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import TestSeedFieldCreator


@dataclass(frozen=True)
class TestSeedSSHKeypairOf(TestSeedFieldCreator[UserData, SSHKeypairData]):
    """An SSH public key the user holds, with no private key."""

    public_key: str
    is_default: bool

    @override
    def kind(self) -> str:
        if self.is_default:
            return Says("default SSH 키 하나를 갖습니다", english="holds one default SSH key")
        return Says(
            "default 가 아닌 SSH 키 하나를 갖습니다",
            english="holds one SSH key that is not the default",
        )

    @override
    def owner_id(self, owner: UserData) -> UserID:
        return UserID(owner.id)

    @override
    def seed(self) -> SSHKeypairCreator:
        return SSHKeypairCreator(
            public_key=self.public_key, private_key=None, is_default=self.is_default
        )
