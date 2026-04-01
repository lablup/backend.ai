"""Query orders for deployment revision preset rows."""

from __future__ import annotations

from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.repositories.base import QueryOrder

__all__ = ("DeploymentRevisionPresetOrders",)


class DeploymentRevisionPresetOrders:
    @staticmethod
    def rank(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DeploymentRevisionPresetRow.rank.asc()
        return DeploymentRevisionPresetRow.rank.desc()

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DeploymentRevisionPresetRow.name.asc()
        return DeploymentRevisionPresetRow.name.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DeploymentRevisionPresetRow.id.asc()
        return DeploymentRevisionPresetRow.id.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DeploymentRevisionPresetRow.created_at.asc()
        return DeploymentRevisionPresetRow.created_at.desc()
