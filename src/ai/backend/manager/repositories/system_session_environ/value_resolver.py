from __future__ import annotations

from abc import ABC, abstractmethod
from itertools import groupby
from typing import override

from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironValueSource
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.views.sokovan.lifecycle import SessionDataForStart

__all__ = (
    "AccessKeyValueResolver",
    "ClusterHostsValueResolver",
    "ClusterReplicasValueResolver",
    "ClusterSizeValueResolver",
    "PreopenPortsValueResolver",
    "SessionIdValueResolver",
    "SessionNameValueResolver",
    "SystemSessionEnvironValueResolver",
    "SystemSessionEnvironValueResolverRegistry",
    "UserEmailValueResolver",
    "UserNameValueResolver",
    "UserUuidValueResolver",
)


class SystemSessionEnvironValueResolver(ABC):
    """Turns one value source into the value a starting session receives."""

    @classmethod
    @abstractmethod
    def value_source(cls) -> SystemSessionEnvironValueSource:
        raise NotImplementedError

    @abstractmethod
    def resolve(self, session: SessionDataForStart) -> str:
        raise NotImplementedError


class SessionIdValueResolver(SystemSessionEnvironValueResolver):
    @override
    @classmethod
    def value_source(cls) -> SystemSessionEnvironValueSource:
        return SystemSessionEnvironValueSource.SESSION_ID

    @override
    def resolve(self, session: SessionDataForStart) -> str:
        return str(session.session_id)


class SessionNameValueResolver(SystemSessionEnvironValueResolver):
    @override
    @classmethod
    def value_source(cls) -> SystemSessionEnvironValueSource:
        return SystemSessionEnvironValueSource.SESSION_NAME

    @override
    def resolve(self, session: SessionDataForStart) -> str:
        return session.name


class ClusterSizeValueResolver(SystemSessionEnvironValueResolver):
    @override
    @classmethod
    def value_source(cls) -> SystemSessionEnvironValueSource:
        return SystemSessionEnvironValueSource.CLUSTER_SIZE

    @override
    def resolve(self, session: SessionDataForStart) -> str:
        return str(len(session.kernels))


class ClusterReplicasValueResolver(SystemSessionEnvironValueResolver):
    @override
    @classmethod
    def value_source(cls) -> SystemSessionEnvironValueSource:
        return SystemSessionEnvironValueSource.CLUSTER_REPLICAS

    @override
    def resolve(self, session: SessionDataForStart) -> str:
        replicas = {
            role: len(list(group))
            for role, group in groupby(
                sorted(session.kernels, key=lambda kernel: kernel.cluster_role),
                key=lambda kernel: kernel.cluster_role,
            )
        }
        return ",".join(f"{role}:{count}" for role, count in replicas.items())


class ClusterHostsValueResolver(SystemSessionEnvironValueResolver):
    @override
    @classmethod
    def value_source(cls) -> SystemSessionEnvironValueSource:
        return SystemSessionEnvironValueSource.CLUSTER_HOSTS

    @override
    def resolve(self, session: SessionDataForStart) -> str:
        return ",".join(
            kernel.cluster_hostname or f"{kernel.cluster_role}{kernel.cluster_idx}"
            for kernel in session.kernels
        )


class PreopenPortsValueResolver(SystemSessionEnvironValueResolver):
    @override
    @classmethod
    def value_source(cls) -> SystemSessionEnvironValueSource:
        return SystemSessionEnvironValueSource.PREOPEN_PORTS

    @override
    def resolve(self, session: SessionDataForStart) -> str:
        if not session.kernels:
            return ""
        return ",".join(str(port) for port in session.kernels[0].preopen_ports)


class UserUuidValueResolver(SystemSessionEnvironValueResolver):
    @override
    @classmethod
    def value_source(cls) -> SystemSessionEnvironValueSource:
        return SystemSessionEnvironValueSource.USER_UUID

    @override
    def resolve(self, session: SessionDataForStart) -> str:
        return str(session.user_uuid)


class UserEmailValueResolver(SystemSessionEnvironValueResolver):
    @override
    @classmethod
    def value_source(cls) -> SystemSessionEnvironValueSource:
        return SystemSessionEnvironValueSource.USER_EMAIL

    @override
    def resolve(self, session: SessionDataForStart) -> str:
        return session.user_email


class UserNameValueResolver(SystemSessionEnvironValueResolver):
    @override
    @classmethod
    def value_source(cls) -> SystemSessionEnvironValueSource:
        return SystemSessionEnvironValueSource.USER_NAME

    @override
    def resolve(self, session: SessionDataForStart) -> str:
        return session.user_name


class AccessKeyValueResolver(SystemSessionEnvironValueResolver):
    @override
    @classmethod
    def value_source(cls) -> SystemSessionEnvironValueSource:
        return SystemSessionEnvironValueSource.ACCESS_KEY

    @override
    def resolve(self, session: SessionDataForStart) -> str:
        return str(session.access_key)


class SystemSessionEnvironValueResolverRegistry:
    _resolver_by_value_source: dict[
        SystemSessionEnvironValueSource, SystemSessionEnvironValueResolver
    ]

    def __init__(self, resolvers: list[SystemSessionEnvironValueResolver]) -> None:
        self._resolver_by_value_source = {
            resolver.value_source(): resolver for resolver in resolvers
        }

    def ensure_every_value_source_registered(self) -> None:
        unregistered_sources = set(SystemSessionEnvironValueSource) - set(
            self._resolver_by_value_source
        )
        if unregistered_sources:
            raise UnreachableError(
                "No system session environ value resolver is registered for "
                f"{sorted(unregistered_sources)}"
            )

    def resolve(self, source: SystemSessionEnvironValueSource, session: SessionDataForStart) -> str:
        try:
            resolver = self._resolver_by_value_source[source]
        except KeyError as e:
            raise UnreachableError(
                f"No system session environ value resolver is registered for {source}"
            ) from e
        return resolver.resolve(session)
