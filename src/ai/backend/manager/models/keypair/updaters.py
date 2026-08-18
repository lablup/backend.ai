"""Update specs for the keypairs table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater


@dataclass
class KeypairDotfilesUpdater(DataUpdater[KeyPairRow, KeyPairData]):
    """Replaces the packed dotfile entries a keypair hands to its sessions."""

    access_key: AccessKey
    dotfiles: bytes

    @property
    @override
    def row_class(self) -> type[KeyPairRow]:
        return KeyPairRow

    @override
    def pk_value(self) -> str:
        return self.access_key

    @override
    def build_values(self) -> dict[str, Any]:
        return {"dotfiles": self.dotfiles}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: KeyPairRow) -> KeyPairData:
        return row.to_data()


@dataclass
class KeypairBootstrapScriptUpdater(DataUpdater[KeyPairRow, KeyPairData]):
    """Replaces the bootstrap script a keypair carries."""

    access_key: AccessKey
    script: str

    @property
    @override
    def row_class(self) -> type[KeyPairRow]:
        return KeyPairRow

    @override
    def pk_value(self) -> str:
        return self.access_key

    @override
    def build_values(self) -> dict[str, Any]:
        return {"bootstrap_script": self.script}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: KeyPairRow) -> KeyPairData:
        return row.to_data()
