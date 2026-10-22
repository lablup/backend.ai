from dataclasses import dataclass
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.bootstrap_script_revision.row import BootstrapScriptRevisionRow


@dataclass
class CurrentDefaultRevisionQuerier:
    """The latest revision of the entity's live default script, the content a session runs."""

    entity_type: EntityType
    entity_id: UUID

    def build_select(self) -> sa.sql.Select[Any]:
        return (
            sa.select(BootstrapScriptRevisionRow)
            .join(BootstrapScriptRow, BootstrapScriptRow.id == BootstrapScriptRevisionRow.script_id)
            .where(
                BootstrapScriptRow.entity_type == self.entity_type,
                BootstrapScriptRow.entity_id == self.entity_id,
                BootstrapScriptRow.is_default,
                BootstrapScriptRow.deleted_at.is_(None),
            )
            .order_by(BootstrapScriptRevisionRow.revision_number.desc())
            .limit(1)
        )
