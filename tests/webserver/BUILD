python_test_utils(
    name="test_utils",
    sources=[
        "**/__init__.py",
        "**/conftest.py",
    ],
)

python_tests(
    name="tests",
    dependencies=[
        "src/ai/backend/web:service",
    ],
    sources=[
        "**/test_*.py",
    ],
)
