from __future__ import annotations

import uuid
from typing import Any

import graphql
import pytest

from ai.backend.common import msgpack
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.dotfile import InvalidDotfilePath
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.api.gql_legacy.domain import CreateDomainNodeInput, ModifyDomainNodeInput


def _packed(path: str) -> bytes:
    return msgpack.packb([{"path": path, "perm": "644", "data": "x"}])


def _input(input_class: Any, **values: Any) -> Any:
    """Build the input the way GraphQL execution does, with omitted fields undefined."""
    return input_class._meta.container({
        **dict.fromkeys(input_class._meta.fields, graphql.Undefined),
        **values,
    })


class TestDomainNodeInputDotfiles:
    @pytest.mark.parametrize("path", ["/etc/passwd", "../config/x", "kconfig.dat"])
    def test_create_rejects(self, path: str) -> None:
        with pytest.raises(InvalidDotfilePath):
            _input(CreateDomainNodeInput, name="d", dotfiles=_packed(path)).to_action()

    @pytest.mark.parametrize("path", ["/etc/passwd", "../config/x", "kconfig.dat"])
    def test_modify_rejects(self, path: str) -> None:
        with pytest.raises(InvalidDotfilePath):
            _input(ModifyDomainNodeInput, dotfiles=_packed(path)).to_action(DomainID(uuid.uuid4()))

    @pytest.mark.parametrize(
        "packed",
        [b"\xc1", msgpack.packb([{"perm": "644", "data": "x"}])],
        ids=["broken", "no-path"],
    )
    def test_create_rejects_malformed_data(self, packed: bytes) -> None:
        with pytest.raises(InvalidAPIParameters):
            _input(CreateDomainNodeInput, name="d", dotfiles=packed).to_action()

    @pytest.mark.parametrize(
        "packed",
        [b"\xc1", msgpack.packb([{"perm": "644", "data": "x"}])],
        ids=["broken", "no-path"],
    )
    def test_modify_rejects_malformed_data(self, packed: bytes) -> None:
        with pytest.raises(InvalidAPIParameters):
            _input(ModifyDomainNodeInput, dotfiles=packed).to_action(DomainID(uuid.uuid4()))

    def test_modify_accepts_path_under_work_dir(self) -> None:
        packed = _packed(".bashrc")
        action = _input(ModifyDomainNodeInput, dotfiles=packed).to_action(DomainID(uuid.uuid4()))
        assert action.updater.dotfiles.optional_value() == packed

    def test_modify_without_dotfiles_skips_the_check(self) -> None:
        action = _input(ModifyDomainNodeInput).to_action(DomainID(uuid.uuid4()))
        assert action.updater.dotfiles.optional_value() is None
