"""Query orders for scaling group rows."""

from __future__ import annotations

from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base import QueryOrder

__all__ = ("ScalingGroupOrders",)


class ScalingGroupOrders:
    """Query orders for scaling groups."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ScalingGroupRow.name.asc()
        return ScalingGroupRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ScalingGroupRow.created_at.asc()
        return ScalingGroupRow.created_at.desc()

    @staticmethod
    def is_active(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ScalingGroupRow.is_active.asc()
        return ScalingGroupRow.is_active.desc()

    @staticmethod
    def is_public(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ScalingGroupRow.is_public.asc()
        return ScalingGroupRow.is_public.desc()
