python_test_utils(
    name="utils",
    sources=["__init__.py"],
)

python_tests(
    name="tests",
    sources=["test_*.py"],
    dependencies=[
        "src/ai/backend/manager/data:src",
        "src/ai/backend/manager/errors:src",
        "src/ai/backend/manager/models:src",
        "src/ai/backend/manager/repositories/auth:src",
    ],
)