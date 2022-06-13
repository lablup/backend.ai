resources(
    name="redis-cluster-compose",
    sources=[
        "redis/redis-cluster.yml",
        "redis/redis-sentinel.dockerfile",
        "redis/sentinel.conf",
    ],
)

python_test_utils(
    name="test_utils",
    dependencies=[
        ":redis-cluster-compose",
    ],
    sources=[
        "**/__init__.py",
        "**/conftest.py",
        "redis/*.py",
        "!redis/test_*.py",
    ],
)

python_tests(
    name="tests",
    dependencies=[
        "src/ai/backend/common:lib",
        "src/ai/backend/testutils:lib",
        ":redis-cluster-compose",
    ],
    sources=[
        "**/test_*.py",
    ],
)

pex_binary(
    name="spawn-sentinel-cluster",
    dependencies=[
        ":test_utils",
    ],
    entry_point="redis/docker.py",
)

pex_binary(
    name="spawn-compose-redis-sentinel-cluster",
    dependencies=[
        ":test_utils",
    ],
    entry_point="redis/docker.py",
)

pex_binary(
    name="spawn-native-redis-sentinel-cluster",
    dependencies=[
        ":test_utils",
    ],
    entry_point="redis/native.py",
)
