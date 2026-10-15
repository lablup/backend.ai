from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.dotfile import DotfileID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.dotfile.types import DotfileData, DotfileEntry
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass(frozen=True)
class DotfileEntryCreator(FieldCreator[EntityIdentifier, DotfileRow, DotfileData]):
    entry: DotfileEntry

    @override
    def field_id(self, row: DotfileRow) -> DotfileID:
        return row.id

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: EntityIdentifier) -> DotfileRow:
        return DotfileRow(
            entity_type=owner_id.entity_type(),
            entity_id=owner_id,
            path=self.entry.path,
            perm=self.entry.perm,
            data=self.entry.data,
            is_default=False,
        )

    @override
    def to_data(self, row: DotfileRow) -> DotfileData:
        return row.to_data()
