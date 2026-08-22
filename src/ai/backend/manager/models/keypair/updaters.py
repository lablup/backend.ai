"""Update specs for the keypairs table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater


@dataclass
class KeypairDotfilesUpdater(DataUpdater[KeyPairRow, KeyPairData]):
    """Replaces the packed dotfile entries a keypair hands to its sessions."""

    keypair_id: KeyPairID
    dotfiles: bytes

    @property
    @override
    def row_class(self) -> type[KeyPairRow]:
        return KeyPairRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return KeyPairRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.keypair_id

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

    keypair_id: KeyPairID
    script: str

    @property
    @override
    def row_class(self) -> type[KeyPairRow]:
        return KeyPairRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return KeyPairRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.keypair_id

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
