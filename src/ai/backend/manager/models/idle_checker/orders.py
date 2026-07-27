from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow


class IdleCheckerOrders:
    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return IdleCheckerRow.id.asc()
        return IdleCheckerRow.id.desc()

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return IdleCheckerRow.name.asc()
        return IdleCheckerRow.name.desc()

    @staticmethod
    def checker_type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return IdleCheckerRow.checker_type.asc()
        return IdleCheckerRow.checker_type.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return IdleCheckerRow.created_at.asc()
        return IdleCheckerRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return IdleCheckerRow.updated_at.asc()
        return IdleCheckerRow.updated_at.desc()
