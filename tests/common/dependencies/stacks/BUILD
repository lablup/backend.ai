python_test_utils(
    name="test_utils",
    sources=["conftest.py"],
    dependencies=[
        "src/ai/backend/common:src",
    ],
)

python_tests(
    name="tests",
    sources=["test_*.py"],
    dependencies=[
        ":test_utils",
        "src/ai/backend/common:src",
    ],
)
