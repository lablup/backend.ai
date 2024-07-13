resources(
    name="redis-cluster-compose",
    sources=[
        "redis-cluster.yml",
        "sentinel.conf",
    ],
)

python_test_utils(
    dependencies=[
        ":redis-cluster-compose",
    ],
    sources=[
        "__init__.py",
        "conftest.py",
        "*.py",
        "!test_*.py",
    ],
)

python_tests(
    name="tests",
    dependencies=[
        ":redis-cluster-compose",
    ],
)
