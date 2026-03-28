"""Query orders for resource policy rows."""

from __future__ import annotations

from ai.backend.manager.repositories.base import QueryOrder

from .row import KeyPairResourcePolicyRow, ProjectResourcePolicyRow, UserResourcePolicyRow


class KeypairResourcePolicyOrders:
    """Query orders for sorting keypair resource policies."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairResourcePolicyRow.name.asc()
        return KeyPairResourcePolicyRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairResourcePolicyRow.created_at.asc()
        return KeyPairResourcePolicyRow.created_at.desc()


class UserResourcePolicyOrders:
    """Query orders for sorting user resource policies."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserResourcePolicyRow.name.asc()
        return UserResourcePolicyRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserResourcePolicyRow.created_at.asc()
        return UserResourcePolicyRow.created_at.desc()


class ProjectResourcePolicyOrders:
    """Query orders for sorting project resource policies."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectResourcePolicyRow.name.asc()
        return ProjectResourcePolicyRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectResourcePolicyRow.created_at.asc()
        return ProjectResourcePolicyRow.created_at.desc()
