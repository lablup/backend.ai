from __future__ import annotations

from ai.backend.manager.actions.registry import SidecarProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult, ScopedFieldsOpsResult
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.data.resource_usage_history.types import (
    DomainUsageBucketData,
    ProjectUsageBucketData,
    UserUsageBucketData,
)
from ai.backend.manager.services.resource_usage.actions.global_search_domain_usage_buckets import (
    GlobalSearchDomainUsageBucketsAction,
)
from ai.backend.manager.services.resource_usage.actions.global_search_project_usage_buckets import (
    GlobalSearchProjectUsageBucketsAction,
)
from ai.backend.manager.services.resource_usage.actions.global_search_user_usage_buckets import (
    GlobalSearchUserUsageBucketsAction,
)
from ai.backend.manager.services.resource_usage.actions.search_domain_usage_buckets import (
    SearchDomainUsageBucketsAction,
)
from ai.backend.manager.services.resource_usage.actions.search_project_usage_buckets import (
    SearchProjectUsageBucketsAction,
)
from ai.backend.manager.services.resource_usage.actions.search_user_usage_buckets import (
    SearchUserUsageBucketsAction,
)


class ResourceUsageProcessors:
    """The usage buckets, read two ways each.

    A bucket is one owner's usage over one window — a sidecar of the graph, not a node in
    it — so a read reports no entity. The super-admin path names no scope; the other names
    exactly one.

    Writes are not here: sokovan records usage through the repository, with no caller to
    gate.
    """

    global_search_domain_usage_buckets: GlobalActionProcessor[
        GlobalSearchDomainUsageBucketsAction, BatchOpsResult[DomainUsageBucketData]
    ]
    search_domain_usage_buckets: ScopeActionProcessor[
        SearchDomainUsageBucketsAction, ScopedFieldsOpsResult[DomainUsageBucketData]
    ]
    global_search_project_usage_buckets: GlobalActionProcessor[
        GlobalSearchProjectUsageBucketsAction, BatchOpsResult[ProjectUsageBucketData]
    ]
    search_project_usage_buckets: ScopeActionProcessor[
        SearchProjectUsageBucketsAction, ScopedFieldsOpsResult[ProjectUsageBucketData]
    ]
    global_search_user_usage_buckets: GlobalActionProcessor[
        GlobalSearchUserUsageBucketsAction, BatchOpsResult[UserUsageBucketData]
    ]
    search_user_usage_buckets: ScopeActionProcessor[
        SearchUserUsageBucketsAction, ScopedFieldsOpsResult[UserUsageBucketData]
    ]

    def __init__(
        self,
        domain: SidecarProcessorGroup[DomainUsageBucketData],
        project: SidecarProcessorGroup[ProjectUsageBucketData],
        user: SidecarProcessorGroup[UserUsageBucketData],
    ) -> None:
        self.global_search_domain_usage_buckets = domain.global_search_ops(
            GlobalSearchDomainUsageBucketsAction
        )
        self.search_domain_usage_buckets = domain.search_ops(SearchDomainUsageBucketsAction)
        self.global_search_project_usage_buckets = project.global_search_ops(
            GlobalSearchProjectUsageBucketsAction
        )
        self.search_project_usage_buckets = project.search_ops(SearchProjectUsageBucketsAction)
        self.global_search_user_usage_buckets = user.global_search_ops(
            GlobalSearchUserUsageBucketsAction
        )
        self.search_user_usage_buckets = user.search_ops(SearchUserUsageBucketsAction)
