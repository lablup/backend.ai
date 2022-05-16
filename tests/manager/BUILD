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
        "tests/manager:config",
    ],
)

file(name="config", source="manager.toml")
