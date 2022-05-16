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
        "tests/manager:config",
        "//:reqs#aiosqlite",
    ],
)

file(name="config", source="manager.toml")
