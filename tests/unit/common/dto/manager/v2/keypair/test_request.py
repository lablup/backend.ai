"""Tests for keypair v2 request DTOs."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.keypair.request import AdminRegisterSSHKeypairInput
from ai.backend.common.exception import BackendAISchemaValidationFailed

_SSH_PUBLIC_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICq33r1BP5Jbc+JSvADo7sDmG1TUyNz/GmRQzraa1krs"


class TestAdminRegisterSSHKeypairInput:
    def test_accepts_an_ssh_public_key(self) -> None:
        req = AdminRegisterSSHKeypairInput(access_key="AKIATEST", ssh_public_key=_SSH_PUBLIC_KEY)
        assert req.ssh_public_key == _SSH_PUBLIC_KEY

    @pytest.mark.parametrize(
        "ssh_public_key",
        ["", "not-an-ssh-public-key"],
        ids=["empty", "unknown-key-type"],
    )
    def test_rejects_a_non_ssh_public_key(self, ssh_public_key: str) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            AdminRegisterSSHKeypairInput(access_key="AKIATEST", ssh_public_key=ssh_public_key)
