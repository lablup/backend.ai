# Same infrastructure set as tests/component (postgres + etcd + redis), run in a separate CI job.
__defaults__({python_tests: dict(batch_compatibility_tag="unit-common")})

python_test_utils(
    sources=[
        "*.py",
        "!test_*.py",
    ],
    dependencies=[
        "src/ai/backend/testutils/otel.py",  # pytest_plugins in conftest.py
    ],
)

python_tests(
    name="tests",
)
