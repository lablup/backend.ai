python_test_utils(
    sources=[
        "*.py",
        "!test_*.py",
    ],
    dependencies=[
        "//:reqs#aiosqlite",  # not auto-inferred
        # pytest_plugins in conftest.py
        "src/ai/backend/testutils/bootstrap.py",
        "src/ai/backend/testutils/db_fixtures.py",
        "src/ai/backend/testutils/otel.py",
    ],
)

python_tests(
    name="tests",
)
