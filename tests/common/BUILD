python_test_utils(
    name="test_utils",
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
