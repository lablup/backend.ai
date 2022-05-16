python_test_utils(
    name="test_utils",
)

python_tests(
    name="tests",
    dependencies=[
        "src/ai/backend/agent:service",
        "tests/agent:config",
    ],
)

file(name="config", source="agent.toml")
