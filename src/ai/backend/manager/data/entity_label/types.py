from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.entity_label import EntityLabelID, EntityLabelKey
from ai.backend.common.data.entity.types import FieldData, RuntimeEntityID


@dataclass(frozen=True)
class EntityLabelData(FieldData):
    """One ``key=value`` label and the entity carrying it.

    The entity is an id that answers its own type: a label goes on anything, so the
    type is a value read off the row.
    """

    id: EntityLabelID
    entity: RuntimeEntityID
    key: EntityLabelKey
    value: str
    created_at: datetime
    updated_at: datetime
