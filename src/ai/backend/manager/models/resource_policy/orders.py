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

    @staticmethod
    def max_session_lifetime(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairResourcePolicyRow.max_session_lifetime.asc()
        return KeyPairResourcePolicyRow.max_session_lifetime.desc()

    @staticmethod
    def max_concurrent_sessions(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairResourcePolicyRow.max_concurrent_sessions.asc()
        return KeyPairResourcePolicyRow.max_concurrent_sessions.desc()

    @staticmethod
    def max_containers_per_session(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairResourcePolicyRow.max_containers_per_session.asc()
        return KeyPairResourcePolicyRow.max_containers_per_session.desc()

    @staticmethod
    def idle_timeout(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairResourcePolicyRow.idle_timeout.asc()
        return KeyPairResourcePolicyRow.idle_timeout.desc()

    @staticmethod
    def max_concurrent_sftp_sessions(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairResourcePolicyRow.max_concurrent_sftp_sessions.asc()
        return KeyPairResourcePolicyRow.max_concurrent_sftp_sessions.desc()

    @staticmethod
    def max_pending_session_count(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairResourcePolicyRow.max_pending_session_count.asc()
        return KeyPairResourcePolicyRow.max_pending_session_count.desc()


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

    @staticmethod
    def max_vfolder_count(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserResourcePolicyRow.max_vfolder_count.asc()
        return UserResourcePolicyRow.max_vfolder_count.desc()

    @staticmethod
    def max_concurrent_logins(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserResourcePolicyRow.max_concurrent_logins.asc()
        return UserResourcePolicyRow.max_concurrent_logins.desc()

    @staticmethod
    def max_quota_scope_size(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserResourcePolicyRow.max_quota_scope_size.asc()
        return UserResourcePolicyRow.max_quota_scope_size.desc()

    @staticmethod
    def max_session_count_per_model_session(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserResourcePolicyRow.max_session_count_per_model_session.asc()
        return UserResourcePolicyRow.max_session_count_per_model_session.desc()

    @staticmethod
    def max_customized_image_count(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserResourcePolicyRow.max_customized_image_count.asc()
        return UserResourcePolicyRow.max_customized_image_count.desc()


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

    @staticmethod
    def max_vfolder_count(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectResourcePolicyRow.max_vfolder_count.asc()
        return ProjectResourcePolicyRow.max_vfolder_count.desc()

    @staticmethod
    def max_quota_scope_size(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectResourcePolicyRow.max_quota_scope_size.asc()
        return ProjectResourcePolicyRow.max_quota_scope_size.desc()

    @staticmethod
    def max_network_count(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectResourcePolicyRow.max_network_count.asc()
        return ProjectResourcePolicyRow.max_network_count.desc()
