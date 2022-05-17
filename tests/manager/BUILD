python_test_utils(
    name="test_utils",
    sources=[
        "conftest.py",
        "model_factory.py",
    ],
)

python_tests(
    name="tests",
    dependencies=[
        "src/ai/backend/manager:service",
        "src/ai/backend/testutils:lib",
        "//:reqs#aiosqlite",
    ],
)
