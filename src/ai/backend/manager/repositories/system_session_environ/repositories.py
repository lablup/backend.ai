from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.system_session_environ.repository import (
    SystemSessionEnvironRepository,
)
from ai.backend.manager.repositories.system_session_environ.value_resolver import (
    AccessKeyValueResolver,
    ClusterHostsValueResolver,
    ClusterReplicasValueResolver,
    ClusterSizeValueResolver,
    PreopenPortsValueResolver,
    SessionIdValueResolver,
    SessionNameValueResolver,
    SystemSessionEnvironValueResolverRegistry,
    UserEmailValueResolver,
    UserNameValueResolver,
    UserUuidValueResolver,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class SystemSessionEnvironRepositories:
    repository: SystemSessionEnvironRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        value_resolver_registry = SystemSessionEnvironValueResolverRegistry([
            SessionIdValueResolver(),
            SessionNameValueResolver(),
            ClusterSizeValueResolver(),
            ClusterReplicasValueResolver(),
            ClusterHostsValueResolver(),
            PreopenPortsValueResolver(),
            UserUuidValueResolver(),
            UserEmailValueResolver(),
            UserNameValueResolver(),
            AccessKeyValueResolver(),
        ])
        value_resolver_registry.ensure_every_value_source_registered()
        return cls(
            repository=SystemSessionEnvironRepository(
                args.v2_ops_provider, value_resolver_registry
            ),
        )
