python_tests(
    name="tests",
    dependencies=[
        ":conftest",
        ":fixtures",
    ],
)

python_test_utils(
    name="conftest",
    sources=["conftest.py"],
    dependencies=[
        ":fixtures",
    ],
)

python_test_utils(
    name="fixtures",
    sources=["fixtures.py"],
)