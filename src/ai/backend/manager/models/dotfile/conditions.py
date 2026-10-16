import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.dotfile.row import DotfileRow


class DotfileConditions:
    @staticmethod
    def by_entity(entity: EntityIdentifier) -> QueryCondition:
        return lambda: sa.and_(
            DotfileRow.entity_type == entity.entity_type(), DotfileRow.entity_id == entity
        )

    @staticmethod
    def by_path(path: str) -> QueryCondition:
        return lambda: DotfileRow.path == path

    @staticmethod
    def by_is_default(is_default: bool) -> QueryCondition:
        return lambda: DotfileRow.is_default.is_(is_default)
