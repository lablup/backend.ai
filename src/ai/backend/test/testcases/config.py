from ai.backend.common.types import ClusterMode
from ai.backend.test.tester.dependency import ClusterDep

STANDARD_CLUSTER_CONFIGS = [
    ClusterDep(
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=1,
    ),
    ClusterDep(
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=3,
    ),
    ClusterDep(
        cluster_mode=ClusterMode.MULTI_NODE,
        cluster_size=3,
    ),
]
