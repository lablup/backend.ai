python_test_utils(
    sources=[
        "*.py",
        "!test_*.py",
    ],
    dependencies=[
        "//:reqs#aiosqlite",  # not auto-inferred
    ],
)

python_tests(
    name="tests",
    dependencies=[
        "src/ai/backend/manager:src",
    ],
)
