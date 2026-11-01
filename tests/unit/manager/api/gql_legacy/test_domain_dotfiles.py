from __future__ import annotations

import uuid

import pytest

from ai.backend.common import msgpack
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.dotfile import InvalidDotfilePath
from ai.backend.manager.api.gql_legacy.domain import CreateDomainNodeInput, ModifyDomainNodeInput


def _packed(path: str) -> bytes:
    return msgpack.packb([{"path": path, "perm": "644", "data": "x"}])


class TestDomainNodeInputDotfiles:
    @pytest.mark.parametrize("path", ["/etc/passwd", "../config/x", "kconfig.dat"])
    def test_create_rejects(self, path: str) -> None:
        with pytest.raises(InvalidDotfilePath):
            CreateDomainNodeInput(name="d", dotfiles=_packed(path)).to_action()

    @pytest.mark.parametrize("path", ["/etc/passwd", "../config/x", "kconfig.dat"])
    def test_modify_rejects(self, path: str) -> None:
        with pytest.raises(InvalidDotfilePath):
            ModifyDomainNodeInput(dotfiles=_packed(path)).to_action(DomainID(uuid.uuid4()))

    def test_modify_accepts_path_under_work_dir(self) -> None:
        action = ModifyDomainNodeInput(dotfiles=_packed(".bashrc")).to_action(
            DomainID(uuid.uuid4())
        )
        assert action.updater.dotfiles.value() == _packed(".bashrc")

    def test_modify_without_dotfiles_skips_the_check(self) -> None:
        ModifyDomainNodeInput().to_action(DomainID(uuid.uuid4()))
