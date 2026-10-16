from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.dotfile.row import DotfileRow


class DotfileOrders:
    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DotfileRow.created_at.asc()
        return DotfileRow.created_at.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DotfileRow.id.asc()
        return DotfileRow.id.desc()
