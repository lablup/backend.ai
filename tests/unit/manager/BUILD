python_test_utils(
    sources=[
        "*.py",
        "!test_*.py",
    ],
    dependencies=[
        "//:reqs#aiosqlite",  # not auto-inferred
        "src/ai/backend/testutils",  # pytest_plugins in conftest.py
    ],
)

python_tests(
    name="tests",
)
