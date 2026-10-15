from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.dotfile.row import DotfileRow


class DotfileConditions:
    @staticmethod
    def by_path(path: str) -> QueryCondition:
        return lambda: DotfileRow.path == path

    @staticmethod
    def by_is_default(is_default: bool) -> QueryCondition:
        return lambda: DotfileRow.is_default.is_(is_default)
