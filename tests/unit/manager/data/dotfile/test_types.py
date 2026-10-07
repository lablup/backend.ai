from __future__ import annotations

from ai.backend.manager.data.dotfile.types import verify_dotfile_name


def test_dotfile_name_validator() -> None:
    assert not verify_dotfile_name(".terminfo")
    assert not verify_dotfile_name(".config")
    assert not verify_dotfile_name(".ssh/authorized_keys")
    assert verify_dotfile_name(".bashrc")
    assert verify_dotfile_name(".ssh/id_rsa")
