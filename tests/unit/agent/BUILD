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
