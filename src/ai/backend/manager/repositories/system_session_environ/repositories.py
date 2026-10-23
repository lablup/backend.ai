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
        value_resolver_registry = SystemSessionEnvironValueResolverRegistry()
        value_resolver_registry.register(SessionIdValueResolver())
        value_resolver_registry.register(SessionNameValueResolver())
        value_resolver_registry.register(ClusterSizeValueResolver())
        value_resolver_registry.register(ClusterReplicasValueResolver())
        value_resolver_registry.register(ClusterHostsValueResolver())
        value_resolver_registry.register(PreopenPortsValueResolver())
        value_resolver_registry.register(UserUuidValueResolver())
        value_resolver_registry.register(UserEmailValueResolver())
        value_resolver_registry.register(UserNameValueResolver())
        value_resolver_registry.register(AccessKeyValueResolver())
        value_resolver_registry.ensure_every_value_source_registered()
        return cls(
            repository=SystemSessionEnvironRepository(
                args.v2_ops_provider, value_resolver_registry
            ),
        )
