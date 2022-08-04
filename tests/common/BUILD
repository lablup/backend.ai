python_test_utils()

python_tests(
    name="tests",
    dependencies=[
        "src/ai/backend/common:lib",
        "src/ai/backend/testutils:lib",
    ],
    overrides={
        "test_distributed.py": {"timeout": 30},
    },
)
